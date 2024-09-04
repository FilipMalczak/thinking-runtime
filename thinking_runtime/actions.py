from dataclasses import dataclass, field
from typing import Protocol

from thinking_runtime.defaults.configure_logging import ConfigureLogging
from thinking_runtime.defaults.recognise_runtime import RecogniseRuntime
from thinking_runtime.model import BootstrapAction

ActionName = str
ActionType = type[BootstrapAction]


ActionPointer = ActionName | ActionType

#todo only enabled should be modifiable
class ActionDefinition(Protocol):
    name: ActionName
    clazz: ActionType
    enabled: bool

@dataclass
class SimpleActionDefinition(ActionDefinition):
    name: ActionName
    clazz: ActionType
    enabled: bool = True

@dataclass
class NonDisablableActionDefinition(ActionDefinition):
    name: ActionName
    clazz: ActionType

    @property
    def enabled(self) -> bool:
        return True

    @enabled.setter
    def enabled(self, val: bool):
        if not val:
            raise NotImplemented(f"Cannot disable action {self.name}")

#fixme this whole thing stinks to high heaven; disabling must be guarded and removing should be impossible (at least via API); rewrite
class BootstrapActions:
    _actions: list[SimpleActionDefinition] = []

    @classmethod
    @property
    def defaults(cls) -> tuple[ActionDefinition, ...]:
        return tuple([
            NonDisablableActionDefinition(x.__name__, x)
            for x in [
                RecogniseRuntime,
                ConfigureLogging
                # todo add ConfigureResources action/module
            ]
        ])

    @classmethod
    @property
    def all(cls) -> tuple[ActionDefinition, ...]:
        return tuple(cls.defaults + tuple(cls._actions))

    @classmethod
    def register(cls, action: ActionType, *, name: ActionName = None, enabled: bool = True):
        assert issubclass(action, BootstrapAction)
        assert not any(issubclass(action, a.clazz) for a in cls.all)  # todo msg only one instance of action allowed
        name = name or action.__name__
        cls._actions.append(SimpleActionDefinition(name, action))
        cls.set_enabled(action, enabled)  # use set_enabled to make sure that its allowed to disable if requested

    @classmethod
    def resolve(cls, pointer: ActionPointer) -> ActionDefinition:
        assert isinstance(pointer, str) or (
                    isinstance(pointer, type) and issubclass(pointer, BootstrapAction))  # todo msg
        for a in cls.all:
            if isinstance(pointer, ActionName) and a.name == pointer:
                return a
            elif a.clazz == pointer:
                return a
        assert False  # todo msg

    @classmethod
    def set_enabled(cls, pointer: ActionPointer, enabled: bool):
        action = cls.resolve(pointer)
        if not enabled:
            assert action.clazz.can_be_disabled()  # todo msg
        action.enabled = enabled

    @classmethod
    def disable(cls, pointer: ActionPointer):
        cls.set_enabled(pointer, False)
