"""Host feasibility model, NOT a Z80 renderer or frame-time prediction.

Keep published tiles resident across generations; never evict the current
display or the complete next frame's requested set. Tile keys include color.
"""


class Residency:
    def __init__(self, capacity):
        if type(capacity) is not int or not 1 <= capacity <= 256:
            raise ValueError('capacity must be 1..256 physical tile slots')
        self.capacity = capacity
        self.slots = {}
        self.age = {}
        self.tick = 0

    def prepare(self, requested, active):
        requested = list(dict.fromkeys(requested))
        active = set(active)
        if not active <= self.slots.keys():
            raise ValueError('active tile is not resident')
        pinned = active | set(requested)
        if len(pinned) > self.capacity:
            raise ValueError('current and next frame exceed physical capacity')
        misses = 0
        self.tick += 1
        for key in requested:
            if key not in self.slots:
                misses += 1
                if len(self.slots) == self.capacity:
                    victim = min((k for k in self.slots if k not in pinned),
                                 key=lambda k: self.age[k])
                    slot = self.slots.pop(victim)
                    del self.age[victim]
                else:
                    occupied = set(self.slots.values())
                    slot = next(i for i in range(self.capacity) if i not in occupied)
                self.slots[key] = slot
            self.age[key] = self.tick
        return {key: self.slots[key] for key in requested}, misses
