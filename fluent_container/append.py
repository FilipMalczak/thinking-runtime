from typing import Protocol, overload

from fluent_container.traits import Identifiable


class HasAppend[E](Protocol):
    def append(self, item: E): pass

class TypedAppendMixin[E, **D](HasAppend):
    _type: type[E]
    _data: list[E]

    def _make(self, *args: D.args, **kwargs: D.kwargs) -> E:
        assert False, f"Cannot produce {self._type} from {args} {kwargs}"

    @overload
    def append(self, x: E): pass

    @overload
    def append(self, *args: D.args, **kwargs: D.kwargs): pass

    def append(self, *args, **kwargs):
        if len(args) == 1 and isinstance(args[0], self._type) and len(kwargs) == 0:
            x = args[0]
        else:
            x = self._make(*args, **kwargs)
        self._raw_append(x)

    def _raw_append(self, element: E):
        list.append(self._data, element)

class UniqueAppendMixin[E: Identifiable](TypedAppendMixin):
    def _raw_append(self, element: E):
        for x in self._data:
            assert x.identifier != element.identifier #todo msg, maybe with idx
        TypedAppendMixin._raw_append(self, element)
