"""Check all five native delivery files against the reviewed release baseline."""
import argparse
import json
from pathlib import Path
from artifact_hash import digest

ROOT = Path(__file__).resolve().parents[1]
PAYLOADS = ('cartridge/FROSTBIT.ROM', 'disk/FROSTBIT.COM', 'disk/FROSTBIT.BIN',
            'disk/FBGFX.BIN', 'disk/FROSTBIT.BAS')


def check_artifact(data, version, baseline):
    if version != baseline['version']:
        raise ValueError('new version requires a reviewed baseline and release')
    if len(data) != baseline['rom']['size'] or digest(data) != baseline['rom']['sha256']:
        raise ValueError('changed bytes require a new version and release')


def verify_delivery(directory, baseline):
    directory = Path(directory)
    expected = baseline['files']
    metadata = json.loads((directory / 'native-delivery-build.json').read_text())
    if set(expected) != set(PAYLOADS) or set(metadata['files']) != set(PAYLOADS):
        raise ValueError('all five native files are required')
    if metadata.get('native_formats_built') is not True:
        raise ValueError('completed native build required')
    for name in PAYLOADS:
        data = (directory / name).read_bytes()
        actual = dict(size=len(data), sha256=digest(data))
        if actual != expected[name] or metadata['files'][name] != expected[name]:
            raise ValueError('release bytes or build receipt differ: ' + name)
    return expected


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--delivery', type=Path, required=True)
    parser.add_argument('--baseline', type=Path,
                        default=ROOT/'references/compact-delivery/issue-14-selective-gain.json')
    args = parser.parse_args()
    files = verify_delivery(args.delivery, json.loads(args.baseline.read_text()))
    print(json.dumps(dict(matches_release_baseline=True, files=files), indent=2))
