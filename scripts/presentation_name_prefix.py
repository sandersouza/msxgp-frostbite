"""Source-valid warm AL temperature prefix; PGT/keys and dirty union stay complete."""
def start(rows,lower):
    if type(rows)is not int or not 0<=rows<1<<24 or type(lower)is not int or not 0<=lower<65536:raise ValueError('bounded24-bit dirty mask and16-bit lower mask required')
    return 3 if lower==14 and rows&7==7 and rows&255!=255 else 0
