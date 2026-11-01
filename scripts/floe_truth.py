"""Strict packed protocol for literal-view collision observation sidecars.

Each row holds228 P0-contact bits and228 M1/P1-shadow bits. They are distinct
source latch channels; dropping bit6 would invalidate complete RAM comparison.
"""
VIEWS=228
BYTES_PER_CHANNEL=29
ROW_BYTES=58
FULL_BYTES=384
ROI_BYTES=78


def view_index(pose,shift,reflection):
    if (type(pose) is not int or type(shift) is not int or not 0<=pose<6 or not 0<=shift<19
            or type(reflection) not in (int,bool) or reflection not in (0,1)):
        raise ValueError('literal view requires pose0..5,shift0..18,reflection0/1')
    return pose*38+shift*2+int(reflection)


def validate_row(data):
    if len(data)!=ROW_BYTES or data[28]&240 or data[57]&240:raise ValueError('complete228-bit row channels with zero padding required')


def sample(data,view):
    validate_row(data)
    if type(view) is not int or not 0<=view<VIEWS:raise ValueError('literal view outside0..227')
    byte,bit=divmod(view,8);mask=1<<bit
    return 7|(128 if data[byte]&mask else 0)|(64 if data[29+byte]&mask else 0)


def full_record(data):
    if len(data)!=FULL_BYTES:raise ValueError('complete384-byte source record required')
    rows=[bytes(data[i*ROW_BYTES:(i+1)*ROW_BYTES]) for i in range(4)]
    for row in rows:validate_row(row)
    return {'truth':rows,'ram':bytes(data[232:360]),
        'registers':dict(zip(('a','x','y','p','sp'),data[360:365])),'glyph':bytes(data[365:384])}


def roi_record(data):
    if len(data)!=ROI_BYTES or data[58]&63!=7:raise ValueError('complete78-byte original-window record with electrical low bits required')
    validate_row(data[:ROW_BYTES])
    return {'truth':bytes(data[:ROW_BYTES]),'actual':data[58],'glyph':bytes(data[59:78])}
