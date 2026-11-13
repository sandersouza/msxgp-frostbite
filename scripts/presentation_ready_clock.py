"""First-safe-VBlank presentation contract; the original source clock is unchanged.

The legacy fixed-clock diagnostic retains its two-field contract. This distinct
contract admits a fully prepared coherent picture at the next actual field and
retains every source/IRQ/order check. No timestamps or field indices are scaled.
"""
from presentation_fixed_clock_probe import active


def admit_ready(ready, tick, last):
    if type(ready) is not bool or any(type(x) is not int or not 0 <= x < 65536
                                    for x in (tick, last)):
        raise ValueError('ready flag and uint16 VBlank counters required')
    return ready and ((tick-last) & 65535) >= 1


def clocks(irq, timings, points):
    """Use real IRQ entry timestamps and strictly increasing hardware fields."""
    if not irq or any(len(r) != 7 or int(r[0]) != i+1 or
                      int(r[4]) not in (1, 2) or int(r[6])
                      for i, r in enumerate(irq)):
        raise ValueError('missed/partial VBlank records')
    if any(int(b[1])-int(a[1]) != 1 for a, b in zip(irq, irq[1:])):
        raise ValueError('missed hardware VBlank')
    if not timings or any(int(b[4])-int(a[4]) < 1
                          for a, b in zip(timings, timings[1:])):
        raise ValueError('picture cap differs')
    elapsed = float(irq[-1][2])-float(irq[0][2])
    if elapsed <= 0:
        raise ValueError('positive measured source interval required')
    active_intervals = []
    for a, b in zip(timings, timings[1:]):
        first, last = int(a[1]), int(b[1])
        if not first < last < len(points):
            raise ValueError('unordered picture source indices')
        if all(active(p['ram']) for p in points[first:last+1]):
            active_intervals.append(float(b[3])-float(a[3]))
    pictures_elapsed = float(timings[-1][3])-float(timings[0][3]) if len(timings) > 1 else 0
    return dict(source_steps_per_second=sum(int(r[4]) for r in irq[1:])/elapsed,
        committed_pictures_per_second=(len(timings)-1)/pictures_elapsed if pictures_elapsed else None,
        active_picture_intervals=len(active_intervals),
        active_pictures_per_second=len(active_intervals)/sum(active_intervals) if active_intervals else None)
