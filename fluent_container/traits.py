from typing import Protocol, Iterable


class Identifiable[ID](Protocol):
    identifier: ID


class Named(Identifiable, Protocol):
    name: str


class NameAsId:
    name: str

    @property
    def identifier(self) -> str:
        return self.name

def name_as_id(cls: type):
    """
    NamedTuples can be tricky to extend with mixins - handle named/identifiable traits with this decorator instead.
    """
    def identifier(self) -> str: return self.name
    cls.identifier = property(identifier)
    return cls


class Enablable(Protocol):
    enabled: bool

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

