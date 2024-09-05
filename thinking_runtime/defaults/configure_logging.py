import logging.config

from thinking_runtime.defaults.logging_config import logging_config, resolve_level
from thinking_runtime.defaults.recognise_runtime import current_runtime, PROFILING, DEBUG
from thinking_runtime.model import BootstrapAction, ConfigurationRequirement


class ConfigureLogging(BootstrapAction):
    def prepare(self) -> None:
        if current_runtime().facets.by_name.any_present(DEBUG, PROFILING):
            logging_config.level = logging.DEBUG
        else:
            logging_config.level = logging.INFO
            logging_config.handlers.files.append(current_runtime().name()+".log")

    def requirements(self) -> list[ConfigurationRequirement]:
        return [ ConfigurationRequirement(["__log__", "__logs__", "__logging__" ]) ]

    def perform(self) -> None:
        root_logger = logging.getLogger()
        root_logger.setLevel(resolve_level(logging_config.level))
        root_logger.handlers = [
            h.to_native_handler(
                logging_config.format_style.value,
                logging_config.format,
                logging_config.level
            )
            for h in logging_config.handlers
            if h.enabled
        ]
