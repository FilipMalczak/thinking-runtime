from typing import Iterable

from fluent_container.append import UniqueAppendMixin
from fluent_container.traits import Identifiable


class ElementMatchingClosure[E](UniqueAppendMixin):
    _data: Iterable[E]

    def _bind(self, data: list[E]):
        self._data = data

    def _matches(self, x: E) -> bool:
        return True

    def __iter__(self) -> Iterable[E]:
        yield from self.all

    @property
    def all[T](self) -> Iterable[T]:
        for x in self._data:
            if self._matches(x):
                yield x

class SubtypeMatchingClosure[E, T](ElementMatchingClosure):
    _type: type[T]

    def _bind(self, data: Iterable[E], _type: type[T]):
        ElementMatchingClosure._bind(self, data)
        self._type = _type

    def _matches(self, x: E) -> bool:
        return isinstance(x, self._type)

    def _make(self, *args, **kwargs) -> E:
        return self._type(*args, **kwargs)



class SearchClosure[E: Identifiable, T: Identifiable, ID](ElementMatchingClosure):

    def __getitem__(self, id: ID) -> T:
        for x in self._data:
            if self._matches(x) and x.identifier == id:
                return x
        raise KeyError(id)

    def get(self, id: ID, _default: T | None = None) -> T | None:
        try:
            return self[id]
        except KeyError:
            return _default

    def find(self, *ids: ID, skip_missing: bool=True) -> Iterable[T]:
        for id in ids:
            try:
                yield self[id]
            except KeyError:
                if not skip_missing:
                    raise

    def __contains__(self, id: ID) -> bool:
        return self.get(id) is not None
