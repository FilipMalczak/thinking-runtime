from abc import ABC, abstractmethod
from dataclasses import field
from types import ModuleType
from typing import NamedTuple, Self


class ConfigurationRequirement(NamedTuple):
    module_names: list[str] = field(default_factory=list)
    required: bool = False

    def __or__(self, other: str) -> Self:
        return ConfigurationRequirement(self.module_names + [other], self.required)

class BootstrapAction(ABC):
    def prepare(self) -> None: pass

    def requirements(self) -> list[ConfigurationRequirement]: return []

    @abstractmethod
    def perform(self) -> None: pass

    #todo rethink and reenable
    # @abstractmethod
    # def report(self) -> Iterable[str]: pass

    @classmethod
    def can_be_disabled(cls) -> bool: return True

    #todo allow for customizing str and repr with custom fields

    def __str__(self):
        return f"BootstrapAction<{type(self).__name__}>"

    def __repr__(self):
        return f"{type(self).__name__}(requires={self.requirements()}, can_be_disabled={self.can_be_disabled()})"