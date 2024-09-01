from importlib import import_module

from thinking_runtime.defaults.configure_logging import ConfigureLogging
from thinking_runtime.defaults.recognise_runtime import RecogniseRuntime
from thinking_runtime.model import BootstrapAction, ConfigurationItem
from thinking_runtime.setup import SetupBootstrapping, register_action

BOOTSTRAPPED = False

def run(action: BootstrapAction):
    action.prepare()
    configurators: list[ConfigurationItem] = []
    for r in action.requirements():
        name = None
        mod = None
        for n in r.module_names:
            try:
                mod = import_module(n)
                name = n
            except ModuleNotFoundError:
                pass
        assert mod is not None or not r.required #todo msg
        configurators.append(ConfigurationItem(name, mod))
    action.perform()

def bootstrap():
    global BOOTSTRAPPED
    if not BOOTSTRAPPED:
        register_action(RecogniseRuntime)
        register_action(ConfigureLogging)
        #todo add ConfigureResources action/module
        setup_action = SetupBootstrapping(run)
        run(setup_action)
        BOOTSTRAPPED = True