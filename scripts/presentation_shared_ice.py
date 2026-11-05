"""Reference lifecycle for the physical shared ice pool; no original assets."""


class SharedIce:
    def __init__(self):
        self.keys = {b: [None] * 64 for b in (1, 2)}
        self.refs = {b: [0] * 64 for b in (1, 2)}
        self.cursor = {b: 0 for b in (1, 2)}
        self.rows = {(p, r): [] for p in (0, 1) for r in range(4)}

    def replace(self, page, row, keys):
        keys = list(keys)
        if (page not in (0, 1) or row not in range(4) or not 1 <= len(keys) <= 14
                or len(set(keys)) != len(keys)
                or any(type(k) is not int or not 0 <= k <= 2048
                       or type(c) is not int or not 1 <= c <= 15 for k, c in keys)):
            raise ValueError('bounded unique exact keys and a page/row owner required')
        bank = 2 if row < 2 else 1
        for slot in self.rows[page, row]:
            self.refs[bank][slot] -= 1
        result = []
        for key in keys:
            if key in self.keys[bank]:
                slot = self.keys[bank].index(key)
            else:
                slot = self.cursor[bank]
                for _ in range(64):
                    if not self.refs[bank][slot]:
                        break
                    slot = (slot + 1) % 64
                else:
                    raise ValueError('all physical slots pinned')
                self.keys[bank][slot] = key
                self.cursor[bank] = (slot + 1) % 64
            self.refs[bank][slot] += 1
            result.append(slot)
        self.rows[page, row] = result
        return result

    def audit(self):
        expected = {b: [0] * 64 for b in (1, 2)}
        for (_, row), slots in self.rows.items():
            bank = 2 if row < 2 else 1
            for slot in slots:
                if self.keys[bank][slot] is None:
                    raise ValueError('unpublished referenced slot')
                expected[bank][slot] += 1
        if expected != self.refs:
            raise ValueError('reference counts disagree with row owners')
