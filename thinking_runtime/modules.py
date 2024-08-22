import sys
from importlib import import_module
from types import ModuleType
from typing import NamedTuple


class ModuleName(NamedTuple):
    parts: list[str]
    is_package: bool

    @property
    def quailified(self) -> str:
        return ".".join(self.parts)

    @property
    def simple(self) -> str:
        return self.parts[-1]

    @property
    def root_package(self) -> str:
        if len(self.parts) > 1 or (len(self.parts) > 0 and self.is_package):
            return self.parts[0]
        return None

    @property
    def parent(self) -> 'ModuleName':
        if len(self.parts) == 1:
            return None
        return ModuleName(self.parts[:-1], True)

    @property
    def has_been_evaluated(self) -> bool:
        return self.quailified in sys.modules


ModulePointer = str | ModuleName | ModuleType

ModuleNamePointer = ModulePointer | list[str] | object


def resolve_module_name(something: ModuleNamePointer) -> ModuleName:
    if isinstance(something, str):
        return ModuleName(something.split("."))
    elif isinstance(something, ModuleName):
        return something
    elif isinstance(something, ModuleType):
        return resolve_module_name(something.__name__)
    elif isinstance(something, list):
        assert all(isinstance(x, str) for x in something) #todo msg
        return ModuleName(something)
    else:
        return resolve_module_name(something.__module__.__name__)


def resolve_module(pointer: ModulePointer, *, evaluate_if_missing: bool=True) -> ModuleType:
    name = resolve_module_name(pointer).quailified
    if evaluate_if_missing:
        return import_module(name)
    return sys.modules[name]
