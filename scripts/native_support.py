"""Shared helpers for frozen native build and loading checks."""

import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET
from environment import ROOT

CONTROL_SHA = 'e75535923a5751e3f4924dc7a3a2f762041b825efb7a5336650d35890cd3ff1d'
COUNTS = (56,60,50)

def symbols(path):
    result={}
    for line in path.read_text().splitlines():
        match=re.fullmatch(r'([^:]+): EQU 0x([0-9A-Fa-f]+)',line.strip())
        if match:result[match[1]]=int(match[2],16)
    return result

def private_output(path):
    path = Path(path).resolve()
    if path == (ROOT / 'outputs').resolve() or not path.is_relative_to((ROOT / 'outputs').resolve()):
        raise ValueError('raw source captures must stay in a fresh ignored outputs subtree')
    return path

def validate_machine_profile(data):
    root=ET.fromstring(data)
    ram=sum(int(node.attrib['size'],0) for node in root.findall('.//RAM/mem'))
    if ram!=65536 or root.findall('.//MemoryMapper'):
        raise ValueError('diagnostic requires unexpanded 64 KiB RAM')
    vdp=root.find('.//VDP')
    if vdp is None or not vdp.findtext('version','').startswith(('TMS9918','TMS9928','TMS9929')):
        raise ValueError('diagnostic requires TMS9918-family VDP')
    if vdp.findtext('vram')!='16':
        raise ValueError('diagnostic requires configured 16 KiB VRAM')

def find_machine_profile(executable):
    prefix=Path(executable).resolve().parent.parent
    candidates=[prefix/'openMSX.app/Contents/Resources/share/machines/C-BIOS_MSX1.xml',
                prefix/'share/openmsx/machines/C-BIOS_MSX1.xml',
                Path('/usr/share/openmsx/machines/C-BIOS_MSX1.xml')]
    for path in candidates:
        if path.is_file():
            return path
    raise ValueError('C-BIOS_MSX1 profile not found; install full openMSX data or pass --machine-profile')

def isolated_profile(path):
    root=ET.fromstring(path.read_bytes())
    for descriptor in root.findall('.//ROM/rom'):
        filename=descriptor.find('filename')
        if filename is None or not filename.text:
            raise ValueError('C-BIOS profile has no firmware filename')
        firmware=(path.parent/filename.text.strip()).resolve()
        data=firmware.read_bytes()
        expected=descriptor.findtext('sha1')
        if expected and hashlib.sha1(data).hexdigest()!=expected.strip():
            raise ValueError(f'bundled C-BIOS firmware identity mismatch: {firmware}')
        filename.text=str(firmware)
    return (b'<?xml version="1.0"?>\n<!DOCTYPE msxconfig SYSTEM "msxconfig2.dtd">\n'
            + ET.tostring(root,encoding='utf-8'))

def hardware(controls,player):
    if player not in (0,1):raise ValueError('original C7 requires0/1')
    r6,r8,j1,j2=controls
    keys=15^(((r8>>5)&3)|((r8>>2)&4)|((r8>>4)&8))
    ports=((15^(j1&15))<<4)|(15^(j2&15))
    ports&=(keys|240) if player else ((keys<<4)|15)
    fire=[0 if j&16 else 128 for j in (j1,j2)]
    if r8&1:fire[player]=0
    return ports,63^((r6>>5)&3),*fire

def native_code_size(metadata):
    rows=[r for r in metadata.get('compact_enemy_ram',{}).get('initializers',[]) if r['ram_address']==0xE300]
    feature=metadata.get('native_enemy_irq_fix')
    expected=116 if feature else 112
    if (len(rows)!=1 or rows[0]['size']!=expected or feature and
            (feature.get('code_bytes')!=116 or not feature.get('protected_address_latch'))):
        raise ValueError('explicit exact native enemy code allocation required')
    return expected

def mask_tiles(bitmap, width, height, phase_x, phase_y):
    """Expand a source mask into reusable eight-row SCREEN2 pattern fragments."""
    if (type(width) is not int or type(height) is not int or not 1 <= width <= 32 or not 1 <= height <= 32
            or type(phase_x) is not int or not 0 <= phase_x < 16 or type(phase_y) is not int or not 0 <= phase_y < 8
            or len(bitmap) != width * height or any(value not in (0, 1) for value in bitmap)):
        raise ValueError('bounded binary source mask and explicit horizontal/vertical phase required')
    start = 8 + phase_x * 3 // 2; origin = start & ~7
    columns = (8 + (phase_x + width) * 3 // 2 - origin + 7) // 8
    rows = (phase_y + height + 7) // 8; patterns = [bytearray(8) for _ in range(columns * rows)]
    for y in range(height):
        target_y = phase_y + y
        for x in range(width):
            if bitmap[y * width + x]:
                for target_x in range(8 + (phase_x + x) * 3 // 2 - origin, 8 + (phase_x + x + 1) * 3 // 2 - origin):
                    patterns[(target_y // 8) * columns + target_x // 8][target_y % 8] |= 128 >> (target_x % 8)
    return {'columns': columns, 'rows': rows, 'patterns': [bytes(pattern) for pattern in patterns]}

def expand_pair(mask,parity):
    if type(mask)is not int or not 0<=mask<=255 or parity not in (0,1):raise ValueError('byte mask and pixel-scale parity required')
    result=bytearray(2)
    for x in range(8):
        if mask&(128>>x):
            for tx in range((parity+x)*3//2-parity*3//2,(parity+x+1)*3//2-parity*3//2):result[tx//8]|=128>>(tx%8)
    return bytes(result)

def view(rom, address, height, reflect=False, scale=1):
    if (len(rom)!=4096 or type(address) is not int or type(height) is not int
            or height<1 or address<0xF000 or address+height>0x10000 or scale not in (1,2)):
        raise ValueError('invalid table range or pixel scale')
    rows=rom[address-0xF000:address-0xF000+height][::-1]
    pixels=[]
    for row in rows:
        bits=[int(bool(row&(128>>x))) for x in range(8)]
        if reflect:bits.reverse()
        pixels.extend(value for value in bits for _ in range(scale))
    return {'range':[address,address+height-1],'width':8*scale,'height':height,
            'reflected':reflect,'pixels':pixels}
