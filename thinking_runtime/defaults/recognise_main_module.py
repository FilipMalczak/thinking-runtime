import sys
from os.path import basename, dirname, exists, join
from types import ModuleType
from typing import NamedTuple, Optional

from thinking_runtime.model import BootstrapAction
from thinking_runtime.modules import ModuleName


class Module(NamedTuple):
    module_: ModuleType
    file_path: Optional[str]
    name: Optional[ModuleName]
    is_shell: bool = False


MAIN: Module = None

_INIT = "__init__.py"

def main_module() -> Module:
    return MAIN

class RecogniseMainModule(BootstrapAction):
    def perform(self) -> None:
        global MAIN
        assert MAIN is None #todo msg
        main = sys.modules["__main__"]
        try:
            main_file = main.__file__
        except AttributeError:
            MAIN = Module(main, None, None, True)
            return
        assert main_file.endswith(".py")  # todo msg
        name_parts = [basename(main_file)[:-len(".py")]]
        parent_dir = dirname(main_file)
        while exists(join(parent_dir, _INIT)):
            name_parts = [basename(parent_dir)] + name_parts
            parent_dir = dirname(parent_dir)
        if len(name_parts) > 1 and name_parts[-1] == "__main__":
            name_parts = name_parts[:-1]
            is_package = True
        else:
            is_package = False
        main_name = ".".join(name_parts)
        sys.modules[main_name] = main
        MAIN = Module(main, main_file, ModuleName(name_parts, is_package))

    # def report(self, emitter: Callable[[str], None]): #todo
    #     emitter(f"Main module recognized as {MAIN}")