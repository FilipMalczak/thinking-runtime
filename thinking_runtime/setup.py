from typing import Callable

from thinking_runtime.actions import BootstrapActions
from thinking_runtime.init_config import BOOTSTRAP_CONFIG
from thinking_runtime.model import BootstrapAction, ConfigurationRequirement


class SetupBootstrapping(BootstrapAction):
    def __init__(self, action_runner: Callable[[BootstrapAction], None]):
        self.runner = action_runner

    def requirements(self) -> list[ConfigurationRequirement]:
        return [ BOOTSTRAP_CONFIG ]

    def perform(self) -> None:
        for a in BootstrapActions.all:
            if a.enabled:
                self.runner(a.clazz())