"""Standard openMSX device replay, audited from local GPLv3 Seaquest tooling.

No source-game addresses/fixtures or old evidence are reused. OMR snapshots
contain local cartridge data and remain ignored under outputs/.
"""
import gzip
import xml.etree.ElementTree as ET

MASTER_HZ=3436363200


def device_events(time,controls):
    row6,row8,joy1,joy2=controls
    return ([(time,'KeyMatrixState',{'row':r,'press':v,'release':255^v}) for r,v in ((6,row6),(8,row8))]
            +[(time,'MSXJoyState',{'id':p,'press':v,'release':63^v}) for p,v in ((1,joy1),(2,joy2))])


def replay(seed,events,end,path):
    root=ET.fromstring(gzip.decompress(seed.read_bytes()));record=root.find('replay')
    snapshots=record.find('snapshots')
    for child in list(snapshots)[1:]:snapshots.remove(child)
    log=record.find('events');log.clear()
    next_id=max(int(e.attrib['id']) for e in root.iter() if e.attrib.get('id','').isdigit())+1
    for time,kind,values in events+[(end,'EndLog',{})]:
        item=ET.SubElement(log,'item',id=str(next_id),type=kind);next_id+=1
        ET.SubElement(ET.SubElement(ET.SubElement(item,'StateChange'),'time'),'time').text=str(round(time*MASTER_HZ))
        for key,value in values.items():
            field=ET.SubElement(item,key)
            if isinstance(value,list):
                for token in value:ET.SubElement(field,'item').text=token.decode('latin1') if isinstance(token,(bytes,bytearray)) else str(token)
            else:field.text=str(value)
    record.find('currentTime/time').text='0'
    xml=ET.tostring(root,encoding='utf-8').replace(b'\0',b'\xc0\x80')
    for byte in range(1,32):
        if byte not in (9,10,13):xml=xml.replace(bytes([byte]),f'&#x{byte:02X};'.encode())
    path.write_bytes(gzip.compress(b'<?xml version="1.0"?>\n<!DOCTYPE serial SYSTEM "openmsx-serialize.dtd">\n'+xml))
