"""Exact byte allocator for declared, independently justified native RAM holes."""
import hashlib


class Layout:
    def __init__(self,free):
        self.free=sorted(tuple(row) for row in free)
        for i,(a,b) in enumerate(self.free):
            if type(a) is not int or type(b) is not int or not 0<=a<b<=65536:
                raise ValueError('bounded nonempty native allocation domain required')
            if i and self.free[i-1][1]>a:raise ValueError('overlapping native allocation domains')
        self.image=bytearray(65536)
        self.objects={}

    def add(self,name,data,alignment=1):
        if not isinstance(name,str) or not name or name in self.objects:raise ValueError('unique named native object required')
        if not data or type(alignment) is not int or alignment<1 or alignment&(alignment-1):
            raise ValueError('nonempty object and power-of-two alignment required')
        choices=[]
        for i,(a,b) in enumerate(self.free):
            start=(a+alignment-1)&-alignment
            if start+len(data)<=b:choices.append((b-a,i,start))
        if not choices:raise ValueError(f'native object {name} ({len(data)} bytes) cannot fit certified free extents')
        _,i,start=min(choices)
        a,b=self.free.pop(i);end=start+len(data)
        if a<start:self.free.append((a,start))
        if end<b:self.free.append((end,b))
        self.free.sort()
        self.image[start:end]=data
        self.objects[name]=dict(address=start,size=len(data),alignment=alignment,sha256=hashlib.sha256(data).hexdigest())
        return start

    def records(self,name,data,stride):
        if type(stride) is not int or stride<1 or not data or len(data)%stride:
            raise ValueError('whole fixed-stride native record stream required')
        return b''.join(self.add(f'{name}/{i//stride}',data[i:i+stride]).to_bytes(2,'little')
                        for i in range(0,len(data),stride))
