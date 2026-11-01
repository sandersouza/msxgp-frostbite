"""Distinct native presentation cartridge profile; runtime delivery is pending."""
from original_graphics import SOURCE_SHA256
from presentation_assets import memory_layout

VERSION = '0.0.7-presentation'
ROM_BYTES = 4194304


def bank_layout(contact_banks):
    if type(contact_banks) is not int or not 1 <= contact_banks <= 242:
        raise ValueError('contact banks must fit the fixed256-bank cartridge')
    contacts = list(range(14, 14 + contact_banks))
    return {'resident': 0, 'fragments': 1, 'native': 2, 'contacts': contacts,
            'available_assets': list(range(3, 14)) + list(range(14 + contact_banks, 256))}


def profile():
    ram = memory_layout()
    # Existing native acquisition scratch is retained separately from bus IO.
    ram['regions'].append({'name': 'native_contacts', 'start': 0xC780, 'end': 0xC7A0})
    return {'version': VERSION, 'signature': 'FBP0', 'source_sha256': SOURCE_SHA256,
            'clock_hz': 3579545, 'ram_bytes': 65536, 'vram_bytes': 16384, 'mapper': 'ASCII16',
            'rom_bytes': ROM_BYTES, 'ram': ram, 'runtime_qualified': False,
            'scope': 'New build profile; source/live target equivalence and timing gates remain pending'}


def validate_rom(data):
    errors = []
    if len(data) != ROM_BYTES: errors.append('4MiB ASCII16 cartridge required')
    if data[:2] != b'AB' or data[16:20] != b'FBP0': errors.append('distinct presentation cartridge signature required')
    if len(data) < 20 or not 0x4014 <= int.from_bytes(data[2:4], 'little') < 0x8000 or any(data[4:16]):
        errors.append('resident cartridge entry and zero vectors required')
    return errors
