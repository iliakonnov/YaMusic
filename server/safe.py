print("Loaded safe")
class SafeDict:
    def __init__(self, inner=None, fake=None):
        self._inner = {}
        self._fake = fake
        if inner is not None:
            for k, v in inner.items():
                self[k] = v

    def __contains__(self, key):
        return key in self._inner

    def __getitem__(self, key):
        if key in self._inner:
            return self._inner[key]
        else:
            return SafeDict(fake=(key, self))

    def __setitem__(self, key, value):
        self.de_fake()
        if isinstance(value, dict):
            self._inner[key] = SafeDict(value)
        else:
            self._inner[key] = value

    def __len__(self):
        return len(self._inner)

    def items(self):
        return self._inner.items()

    @staticmethod
    def is_fake(obj):
        if isinstance(obj, SafeDict):
            return obj._fake is not None
        return False

    def de_fake(self):
        if self._fake is not None:
            me, parent = self._fake
            parent[me] = self
            self._fake = None

    def clone(self):
        res = {}
        for k, v in self.items():
            if isinstance(v, SafeDict):
                res[k] = v.clone()
            else:
                res[k] = v
        return res

