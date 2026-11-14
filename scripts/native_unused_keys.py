"""Explicit all-state native roles that no longer publish six-byte tile keys.

Ice/fusion use separate tuples/tags/colors; invalid physical slots never had a
producer. Active bear, actor, igloo and header keys are deliberately excluded.
These are allocation candidates, not permission to bypass owner validation.
"""

def extents():
    return tuple((0xD000+(page*3+bank)*384+first*6,0xD000+(page*3+bank+1)*384)
                 for page in range(2) for bank,first in ((0,56),(1,19),(2,9)))


def audit_and_shadow(memory,objects):
    """Verify explicit immutable linked owners before adapting historical readers."""
    import hashlib
    if len(memory)!=65536:raise ValueError('complete native memory required')
    permitted={a for start,end in extents() for a in range(start,end)}
    shadow=bytearray(memory);seen=set()
    for row in objects:
        a,n=row['address'],row['size'];domain=set(range(a,a+n))
        if not n or not domain<=permitted or domain&seen:raise ValueError('unique whole unused-key allocation required')
        if hashlib.sha256(memory[a:a+n]).hexdigest()!=row['sha256']:raise ValueError('native unused-key immutable owner changed')
        seen|=domain;shadow[a:a+n]=bytes([255])*n
    if any(memory[a]!=255 for a in permitted-seen):raise ValueError('unregistered unused-key bytes changed')
    return bytes(shadow)
