import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import NamedTuple, Callable

from lazy import lazy
from thinking_modules.immutable import Immutable
from thinking_modules.main_module import main_module, main_name
from thinking_modules.model import ModuleName, ModuleNamePointer

from fluent_container.closure import SearchClosure
from fluent_container.container import Container
from fluent_container.traits import name_as_id
from thinking_runtime.model import BootstrapAction, ConfigurationRequirement
from thinking_runtime.init_config import BOOTSTRAP_CONFIG


class PackagesClosure(Immutable):
    target: list[str]

    def add(self, other: ModuleNamePointer):
        self.target.append(ModuleName.of(other).module_descriptor.root_package.qualified)
        return self

    def __contains__(self, item: ModuleNamePointer) -> bool:
        return ModuleName.of(item).qualified in self.target

    __iadd__= add
    __lshift__ = add

@dataclass
class PackagesStructure:
    project_packages: list[str] = None
    test_packages: list[str] = field(default_factory=lambda: ["test", "tests"])

    @lazy
    def project(self) -> PackagesClosure:
        return PackagesClosure(self.project_packages)

    @lazy
    def test(self) -> PackagesClosure:
        return PackagesClosure(self.test_packages)


STRUCTURE = PackagesStructure()

def project_structure() -> PackagesStructure:
    return STRUCTURE

class RuntimeMode(Enum):
    APP = auto()
    TEST = auto()

#todo add description, make it a protocol, maybe add __or__ and __and__
Condition = Callable[[], bool]


class Missing(Enum):
    MISSING = auto()


class SplitEnvvarClosure:
    def __init__(self, ev: 'envvar', sep: str=","):
        self.ev = ev
        self.sep = sep

    def contains(self, value) -> Condition:
        return lambda: value in self.ev._value().split(self.sep)

class envvar:
    def __init__(self, name: str):
        self.varname = name

    def _value(self):
        return os.environ.get(self.varname, Missing.MISSING)

    @property
    def is_present(self) -> Condition:
        return lambda: self._value() is not Missing.MISSING

    def equals(self, value) -> Condition:
        return lambda: self._value() == str(value)

    def split(self, sep=",") -> SplitEnvvarClosure:
        return SplitEnvvarClosure(self, sep)

@name_as_id
class RuntimeFacetDefinition(NamedTuple):
    name: str
    triggers: list[Condition]


_FACETS: list[RuntimeFacetDefinition] = []

RUNTIME_DETAILS = "RUNTIME_DETAILS"

def facet(name: str, *triggers: Condition, ignore_details: bool=False):
    t = [*triggers]
    if not ignore_details:
        t.append(envvar(RUNTIME_DETAILS).split(",").contains(name))
    return RuntimeFacetDefinition(name, [*triggers])


def register_facet(facet: RuntimeFacetDefinition):
    _FACETS.append(facet)


@name_as_id
class RuntimeFacet(NamedTuple):
    name: str
    trigger: Condition


class FacetsByName(SearchClosure):
    def __init__(self, facets: 'ActiveFacets'):
        SearchClosure._bind(self, facets)


class ActiveFacets(Container):
    def __init__(self):
        Container.__init__(self, RuntimeFacet, [])

    @property
    def by_name(self) -> FacetsByName:
        return FacetsByName(self)


class Runtime(NamedTuple):
    mode: RuntimeMode
    facets: ActiveFacets
    started_on: datetime

    def name(self, prefix: str = "session"):
        return f"{prefix}_{self.started_on}"


RUNTIME: Runtime = None

def current_runtime() -> Runtime:
    return RUNTIME

DEBUG = "DEBUG"
DEBUG_FACET = facet(
    DEBUG,
    envvar("DEBUG").is_present,
    envvar("DEBUGGING").is_present
)
PROFILING = "PROFILING"
PROFILING_FACET = facet(
    PROFILING,
    envvar("PROFILING").is_present
)
register_facet(DEBUG_FACET)
register_facet(PROFILING_FACET)

def _figure_out_mode(main_name: ModuleName) -> RuntimeMode:
    root_name = main_name.module_descriptor.root_package_name
    if root_name is not None and root_name in STRUCTURE.test:
        return RuntimeMode.TEST
    return RuntimeMode.APP


class RecogniseRuntime(BootstrapAction):
    def requirements(self) -> list[ConfigurationRequirement]:
        return [ BOOTSTRAP_CONFIG or "__runtime__" ]

    def perform(self) -> None:
        global RUNTIME
        assert RUNTIME is None
        root = main_module.root_package_name
        if root is not None:
            if STRUCTURE.project_packages is None:
                STRUCTURE.project_packages = [ root.qualified ] if root not in STRUCTURE.test else []
            elif root not in STRUCTURE.project:
                if root not in STRUCTURE.test:
                    STRUCTURE.project.add(root)
        mode = _figure_out_mode(main_name)
        active_facets = ActiveFacets()
        for definition in _FACETS:
            for trigger in definition.triggers:
                if trigger():
                    active_facets.append(RuntimeFacet(definition.name, trigger))
                    continue
        RUNTIME = Runtime(mode, active_facets, datetime.now())

