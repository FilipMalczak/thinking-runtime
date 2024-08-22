from dataclasses import dataclass
from typing import Callable

from thinking_runtime.model import BootstrapAction, ConfigurationRequirement

ActionName = str
ActionType = type[BootstrapAction]

@dataclass
class ActionDefinition:
    name: ActionName
    clazz: ActionType
    enabled: bool = True


ACTIONS: list[ActionDefinition] = []

BOOTSTRAP_CONFIG = ConfigurationRequirement(["__bootstrap__", "__setup__", "__project__", "__structure__"])


def register_action(action: ActionType, *, name: ActionName=None, enabled: bool=True):
    assert issubclass(action, BootstrapAction)
    assert not any(isinstance(a, action) for a in ACTIONS) #todo msg only one instance of action allowed
    name = name or action.__name__
    ACTIONS.append(ActionDefinition(name, action))
    set_enabled(action, enabled) #use set_enabled to make sure that its allowed to disable if requested

ActionPointer = ActionName | ActionType

def resolve_action(pointer: ActionPointer) -> ActionDefinition:
    assert isinstance(pointer, str) or (isinstance(pointer, type) and issubclass(pointer, BootstrapAction)) #todo msg
    for a in ACTIONS:
        if isinstance(pointer, ActionName) and a.name == pointer:
            return a
        elif a.clazz == pointer:
            return a
    assert False #todo msg

def set_enabled(pointer: ActionPointer, enabled: bool):
    action = resolve_action(pointer)
    if not enabled:
        assert action.clazz.can_be_disabled() #todo msg
    action.enabled = enabled

def disable(pointer: ActionPointer):
    set_enabled(pointer, False)

class SetupBootstrapping(BootstrapAction):
    def __init__(self, action_runner: Callable[[BootstrapAction], None]):
        self.runner = action_runner

    def requirements(self) -> list[ConfigurationRequirement]:
        return [ BOOTSTRAP_CONFIG ]

    def perform(self) -> None:
        for a in ACTIONS:
            if a.enabled:
                self.runner(a.clazz())