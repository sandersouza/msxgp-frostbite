#!/usr/bin/env python3
"""Prepare pinned macOS source tools without replacing supplied caches/venvs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
LOCK_PATH = ROOT / 'references/tools-lock.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command, cwd=ROOT, **kwargs):
    return subprocess.run([str(x) for x in command], cwd=cwd, check=True,
        env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1', 'GIT_OPTIONAL_LOCKS': '0'},
        timeout=300, **kwargs)


def output(command, cwd=ROOT):
    return run(command, cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout.strip()


def validate_host(system, machine):
    if system != 'Darwin' or machine not in ('arm64', 'x86_64'):
        raise ValueError('supported setup hosts: macOS arm64/x86_64; Intel is prepared but untested')
    if sys.version_info < (3, 11):
        raise ValueError('Python >=3.11 required; install Homebrew python and rerun')


def validate_checkout(path, commit):
    actual = output(['git', '-C', path, 'rev-parse', 'HEAD'])
    if actual != commit:
        raise ValueError(f'{path}: unexpected revision; preserve/inspect it, no reset performed')
    result = subprocess.run(['git', '-C', str(path), 'diff', '--quiet', 'HEAD', '--'],
                            capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError(f'{path}: modified tracked source; preserved, not rebuilt/reset')


def validate_receipt(binary, receipt_path, commit):
    receipt = json.loads(receipt_path.read_text())
    if receipt.get('commit') != commit or receipt.get('binary_sha256') != digest(binary):
        raise ValueError(f'{binary}: unverified or changed binary; preserved, inspect its managed directory')
    return receipt


def tool_directory(root, name, spec):
    return root / '.tools/frostbite' / f"{name}-{spec['commit']}"


def verified_tool(name, root=ROOT):
    lock = json.loads((root / 'references/tools-lock.json').read_text())
    spec = lock['tools'][name]
    directory = tool_directory(root, name, spec)
    validate_checkout(directory, spec['commit'])
    binary = directory / spec['binary']
    receipt = validate_receipt(binary, directory / '.frostbite-receipt.json', spec['commit'])
    if receipt.get('architecture') != platform.machine() or not os.access(binary, os.X_OK):
        raise ValueError(f'{binary}: executable/architecture mismatch; preserved')
    return binary


def describe_plan(root=ROOT):
    return (f'Would verify macOS/CLT/Homebrew/Python prerequisites; install missing openMSX/Stella; '
            f'preserve or create {root / ".venv"}; add only missing pinned Python dependencies; '
            f'build pinned sjasmplus/DiStella/DASM under {root / ".tools/frostbite"}; '
            'preserve existing .tools and fail on dirty/mismatched managed inputs. No changes applied.')


def version_output(binary,args):
    # DiStella's legacy argv buffer includes argv[0], even for its version banner.
    result=subprocess.run([f'./{binary.name}',*args],cwd=binary.parent,
                          capture_output=True,text=True,timeout=30)
    if result.returncode not in (0,1):
        raise ValueError(f'{binary.name}: version command failed')
    return result.stdout+result.stderr


def prepare_tool(root, name, spec):
    directory = tool_directory(root, name, spec)
    if not directory.exists():
        directory.parent.mkdir(parents=True, exist_ok=True)
        print(f'Preparing pinned {name} source...', flush=True)
        run(['git', 'clone', '--quiet', '--filter=blob:none', '--no-checkout', spec['repository'], directory])
        run(['git', '-C', directory, 'checkout', '--quiet', '--detach', spec['commit']])
    validate_checkout(directory, spec['commit'])
    binary = directory / spec['binary']
    receipt_path = directory / '.frostbite-receipt.json'
    if receipt_path.exists() or binary.exists():
        validate_receipt(binary, receipt_path, spec['commit'])
        return verified_tool(name, root)
    print(f'Building {name}; log {directory / ".frostbite-build.log"}', flush=True)
    with (directory / '.frostbite-build.log').open('w') as log:
        run(spec['build'], cwd=directory, stdout=log, stderr=subprocess.STDOUT)
    validate_checkout(directory, spec['commit'])
    banner = version_output(binary,spec['version_args'])
    if spec['version_contains'] not in banner:
        raise ValueError(f'{name}: expected pinned version banner not found')
    architecture = output(['file', '-b', binary])
    if platform.machine() not in architecture:
        raise ValueError(f'{name}: unexpected executable architecture: {architecture}')
    receipt_path.write_text(json.dumps({'commit': spec['commit'], 'repository': spec['repository'],
        'binary_sha256': digest(binary), 'architecture': platform.machine(), 'file': architecture,
        'version_banner': banner.strip(), 'build': spec['build']}, indent=2) + '\n')
    return verified_tool(name, root)


def python_dependencies(root, install=False):
    python = root / '.venv/bin/python'
    if not python.exists():
        if not install:
            raise ValueError('missing .venv; run bash scripts/setup.sh')
        if (root / '.venv').exists():
            raise ValueError('existing .venv has no usable Python; preserved, repair explicitly')
        run([sys.executable, '-m', 'venv', root / '.venv'])
    output([python, '-c', 'import sys; assert sys.version_info >= (3,11), "Python>=3.11 required"'])
    query = 'import importlib.metadata as m; print(m.version("py65") if list(m.distributions(name="py65")) else "missing")'
    observed = output([python, '-c', query])
    if observed == 'missing' and install:
        run([python, '-m', 'pip', 'install', '--disable-pip-version-check', '-r', root / 'requirements-reference.txt'])
        observed = output([python, '-c', query])
    if observed != '1.2.0':
        raise ValueError(f'existing .venv py65={observed}; requires1.2.0, preserved without upgrade/downgrade')
    output([python, '-m', 'pip', 'check'])
    return python


def check(root=ROOT):
    problems = []
    for executable in ('git', 'cc', 'make', 'brew', 'file', 'openmsx', 'stella'):
        if not shutil.which(executable):
            problems.append(f'missing {executable}; install Xcode command-line tools/Homebrew or run setup for emulators')
    try:
        python_dependencies(root)
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        problems.append(str(error))
    for name in json.loads((root / 'references/tools-lock.json').read_text())['tools']:
        try:
            verified_tool(name, root)
        except (OSError, ValueError, subprocess.SubprocessError) as error:
            problems.append(f'{name}: {error}; run setup or inspect preserved managed directory')
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--check', action='store_true')
    group.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    try:
        validate_host(platform.system(), platform.machine())
        if args.dry_run:
            print(describe_plan())
            return 0
        if not args.check:
            for executable in ('git', 'cc', 'make', 'brew', 'file'):
                if not shutil.which(executable):
                    raise ValueError(f'missing {executable}; install Xcode CLT/Homebrew first')
            for name in ('openmsx', 'stella'):
                if not shutil.which(name):
                    run(['brew', 'install', name])
            python_dependencies(ROOT, install=True)
            for name, spec in json.loads(LOCK_PATH.read_text())['tools'].items():
                prepare_tool(ROOT, name, spec)
        problems = check()
        if problems:
            raise ValueError('\n'.join(problems))
        print('Verified pinned Frostbite assemblers, preserved Python environment and host emulator availability.')
        print('Intel x86_64 and physical MSX remain untested; run build/smoke separately.')
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError) as error:
        print(f'Environment preparation failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
