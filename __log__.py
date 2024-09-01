from thinking_runtime.defaults.logging_config import logging_config, L

logging_config.format = "[{levelname:^"+L+"}] NO_TIME_FOR_REPRODUCIBILITY | {name:^5} @{lineno} :: {msg}"
for h in logging_config.handlers.files:
    h.enabled = False

logging_config.handlers.streams["STDOUT"].enabled = True
logging_config.handlers.streams["STDERR"].enabled = False