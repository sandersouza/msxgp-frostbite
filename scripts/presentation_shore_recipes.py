"""Exact source-derived standing left-shore recipes; no captured state input."""
def pack_record(cut,entries):
    if len(entries)>4 or any(not(-128<=dy<=127 and 0<=color<16 and 0<=pid<256)for dy,color,pid in entries):
        raise ValueError('shore descriptor bounds exceeded')
    data=bytes((len(entries),cut&255))+b''.join(bytes((dy&255,color,pid))for dy,color,pid in entries)
    return data+bytes(16-len(data))

def compile_standing(rom,palette):
    import itertools
    from presentation_model import player
    from presentation_sprites import expand_pair
    if len(rom)!=4096 or len(palette)!=256:raise ValueError('complete source ROM and actual P0 palette required')
    pool=[];poolids={};records=[];recordids={};directory=[];maxcolor=0;maxentries=0;empty=0;checks=0
    for y,x,pose,reflect,coarse in itertools.product((27,),range(24),range(6),range(2),range(2)):
     ram=bytearray(128);ram[0x64]=y;ram[0x66]=x;ram[0x6e]=pose;ram[0x6c]=reflect*8
     d=player(rom,list(ram));planes={};colors=[];pixels={}
     def point(ty,dx,color):
      if color not in planes:planes[color]={};colors.append(color)
      planes[color][ty]=planes[color].get(ty,0)|(128>>dx);pixels[ty,dx]=color
     for row in d['rows']:
      for dx in range(8):
       pos=x+dx;bit=dx if reflect else 7-dx;mask=row['prefix_pattern']if pos<row['update_x']else row['pattern'];color=row['prefix_color']if pos<row['color_update_x']else row['color'];color=row['suffix_color']if pos>=row['suffix_x']else color
       if pos>=8 and mask&(1<<bit):point(row['y']-7+int(coarse and row['y']>=57),dx,palette[color])
       if coarse and row['y']==56 and row['pattern']&(1<<bit):point(50,dx,palette[row['color']])
     maxcolor=max(maxcolor,len(colors));entries=[];cut=0
     if pixels:
      top=min(t for t,dx in pixels);bottom=max(t for t,dx in pixels)
      for cut in range(bottom-15,top+17):
       if all(sum(any(mask for ty,mask in planes[c].items()if bt<=ty<bt+16)for c in colors)<=3 for bt in(cut-16,cut)):break
      else:raise ValueError('No legal cut')
      for bt in(cut-16,cut):
       for color in colors:
        pat=bytearray(32)
        for i in range(16):pat[i],pat[i+16]=expand_pair(planes[color].get(bt+i,0),x&1)
        if any(pat):
         pat=bytes(pat)
         if pat not in poolids:poolids[pat]=len(pool);pool.append(pat)
         entries.append((bt-y-coarse,color,poolids[pat]))
      if len(entries)>6:raise ValueError('Too many entries')
      # Decode every 16x16 pattern independently back to local source-scaled pixels.
      actual={}
      for dy,color,pid in entries:
       pat=pool[pid]
       for ty in range(16):
        for tx in range(16):
         if pat[(tx//8)*16+ty]&(128>>(tx%8)):actual[y+coarse+dy+ty,tx]=color
      want={}
      for(ty,dx),color in pixels.items():
       for tx in range((x+dx)*3//2-x*3//2,(x+dx+1)*3//2-x*3//2):want[ty,tx]=color
      if actual!=want:raise ValueError((y,x,pose,reflect,coarse,'decoded pixels differ'))
     else:empty+=1
     maxentries=max(maxentries,len(entries));rec=pack_record(cut-y-coarse,entries)
     if rec not in recordids:recordids[rec]=len(records);records.append(rec)
     directory.append(recordids[rec]);checks+=1
    if checks!=576 or len(pool)>256 or maxentries>4:raise ValueError('finite standing domain exceeds allocation')
    return b''.join(n.to_bytes(2,'little')for n in directory),b''.join(records),b''.join(pool),dict(finite_cases=checks,unique_records=len(records),patterns=len(pool),max_colors=maxcolor,max_entries=maxentries,empty_cases=empty,scope='Finite sourceY27/X0..23/6poses/reflection/coarse. Exact source prefix/color races, clip and unblank; no captured route data.')

def recipe_x(x):
    if 0<=x<24:return x
    if 84<=x<153:return 22+(x&1)
    raise ValueError('standing X outside specialized domain')


def verify_right_alias(rom,palette,directory,records,patterns):
    """Decode the prepared alias against independent source commands at right X."""
    import itertools
    from presentation_model import player
    checks=0
    for x,pose,reflect,coarse in itertools.product(range(84,153),range(6),range(2),range(2)):
        ram=bytearray(128);ram[0x64]=27;ram[0x66]=x;ram[0x6e]=pose;ram[0x6c]=reflect*8
        want={}
        for row in player(rom,list(ram))['rows']:
            for dx in range(8):
                pos=x+dx;bit=dx if reflect else 7-dx
                mask=row['prefix_pattern']if pos<row['update_x']else row['pattern']
                color=row['prefix_color']if pos<row['color_update_x']else row['color']
                if pos>=row['suffix_x']:color=row['suffix_color']
                targets=[]
                if pos>=8 and mask&(1<<bit):targets.append((row['y']-7+int(coarse and row['y']>=57),color))
                if coarse and row['y']==56 and row['pattern']&(1<<bit):targets.append((50,row['color']))
                for ty,c in targets:
                    for tx in range((x+dx)*3//2-x*3//2,(x+dx+1)*3//2-x*3//2):want[ty,tx]=palette[c]
        offset=((recipe_x(x)*6+pose)*4+2*reflect+coarse)*2
        rid=int.from_bytes(directory[offset:offset+2],'little');rec=records[rid*16:rid*16+16];actual={}
        for i in range(rec[0]):
            dy,color,pid=rec[2+i*3:5+i*3];dy=dy if dy<128 else dy-256;pat=patterns[pid*32:pid*32+32]
            for ty in range(16):
                for tx in range(16):
                    if pat[(tx//8)*16+ty]&(128>>(tx%8)):actual[27+coarse+dy+ty,tx]=color
        if actual!=want:raise ValueError(('right alias pixels differ',x,pose,reflect,coarse))
        checks+=1
    return checks
