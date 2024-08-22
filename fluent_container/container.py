from fluent_container.append import UniqueAppendMixin
from fluent_container.traits import Identifiable


class Container[E: Identifiable](list, UniqueAppendMixin):
    def __init__(self, t: type[E], data: list[E]):
        self._type = t
        self._data = self
        list.__init__(self)
        for e in data:
            self.append(e)
