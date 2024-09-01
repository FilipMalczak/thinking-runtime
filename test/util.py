from datetime import datetime
from logging import getLogger

from thinking_modules.main_module import main_module

from thinking_runtime.bootstrap import bootstrap
from thinking_runtime.defaults.recognise_runtime import current_runtime

def fixture(name):
    bootstrap()

    logger = getLogger(name)

    logger.info(main_module)
    logger.info(current_runtime().mode)
    logger.info(current_runtime().facets)
    assert current_runtime().started_on < datetime.now()

