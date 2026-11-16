#!/usr/bin/env python3
"""Prepare pinned macOS source tools without replacing supplied caches/venvs."""
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




def validate_binary_architecture(description, machine):
    aliases = {'x86_64': ('x86_64', 'x86-64'), 'arm64': ('arm64',), 'aarch64': ('aarch64',)}
    if not any(name in description for name in aliases.get(machine, (machine,))):
        raise ValueError(f'unexpected executable architecture: {description}')


def validate_checkout(path, commit, generated_files=()):
    actual = output(['git', '-C', path, 'rev-parse', 'HEAD'])
    if actual != commit:
        raise ValueError(f'{path}: unexpected revision; preserve/inspect it, no reset performed')
    result = subprocess.run(['git', '-C', str(path), 'diff', '--quiet', 'HEAD', '--'],
                            capture_output=True, timeout=30)
    if result.returncode:
        raise ValueError(f'{path}: modified tracked source; preserved, not rebuilt/reset')
    untracked = run(['git', '-C', path, 'ls-files', '--others', '--exclude-standard', '-z'],
                    stdout=subprocess.PIPE).stdout.decode().split('\0')
    allowed = {'.frostbite-build.log', '.frostbite-receipt.json', *generated_files}
    unexpected = [name for name in untracked if name and name not in allowed]
    if unexpected:
        raise ValueError(f'{path}: unexpected untracked files {unexpected}; preserved, not rebuilt/reset')


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
    validate_checkout(directory, spec['commit'], spec.get('generated_files', ()))
    binary = directory / spec['binary']
    receipt = validate_receipt(binary, directory / '.frostbite-receipt.json', spec['commit'])
    if receipt.get('architecture') != platform.machine() or not os.access(binary, os.X_OK):
        raise ValueError(f'{binary}: executable/architecture mismatch; preserved')
    return binary




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
    validate_checkout(directory, spec['commit'], spec.get('generated_files', ()))
    binary = directory / spec['binary']
    receipt_path = directory / '.frostbite-receipt.json'
    if receipt_path.exists() or binary.exists():
        validate_receipt(binary, receipt_path, spec['commit'])
        return verified_tool(name, root)
    print(f'Building {name}; log {directory / ".frostbite-build.log"}', flush=True)
    with (directory / '.frostbite-build.log').open('w') as log:
        run(spec['build'], cwd=directory, stdout=log, stderr=subprocess.STDOUT)
    validate_checkout(directory, spec['commit'], spec.get('generated_files', ()))
    banner = version_output(binary,spec['version_args'])
    if spec['version_contains'] not in banner:
        raise ValueError(f'{name}: expected pinned version banner not found')
    architecture = output(['file', '-b', binary])
    validate_binary_architecture(architecture, platform.machine())
    receipt_path.write_text(json.dumps({'commit': spec['commit'], 'repository': spec['repository'],
        'binary_sha256': digest(binary), 'architecture': platform.machine(), 'file': architecture,
        'version_banner': banner.strip(), 'build': spec['build']}, indent=2) + '\n')
    return verified_tool(name, root)
