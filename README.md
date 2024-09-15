# thinking-runtime

[![CI](https://github.com/FilipMalczak/thinking-runtime/actions/workflows/ci.yml/badge.svg)](https://github.com/FilipMalczak/thinking-runtime/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/thinking-runtime.svg)](https://badge.fury.io/py/thinking-runtime)

> Part of [thinking](https://github.com/FilipMalczak/thinking-rationale) family.

This will configure the very basics of the runtime before you run more code.

The point is to run some configurations before you proceed with anything else - logging anything, running any meaningul
code, etc. It is based on dunder config files like `__project__` or `__log__`, where you can configure meta-aspects
of your app. This lib will load them and configure the runtime for you.

Those dunder files should not be packaged and should reside in the root of your repo. If you're writing an app, you 
can provide custom config files in your working directory. In case of libraries, you can have defaults for CI and local
development, without impacting consumers configs.

> Requires python 3.12. Is properly typed.

## Usage

> Admittedly, docs need enhancements.

Base abstraction is the `BootstrapAction`. It represents an action that needs to run when bootstrapping the runtime.
It must provide `perform(self) -> None` method that encapsulates the action itself. It can also have 
`prepare(self) -> None` method and expose requirements for dunder config files by implementing 
`requirements(self) -> list[ConfigurationRequirement]`. Each requirement is constructed from list of dunder name and
`required` flag (`False` by default, actions should usually provide default configs and dunder config files should
be used for customization).

> todo describe disabling actions

> todo talk about how you can do anything from any config, but there is only guarantee that config will be loaded before
> an action that requires it

Entrypoint to the framework is [`bootstrap()`](./thinking_runtime/bootstrap.py) method. It will register initial actions
and execute them. It should be called before anything else - notably before any call to `logging.getLogger` (so that
the framework can configure logging first).

> This is a subject to change in the future. It's pretty early in the lifecycle of this project. We will retrieve
> all existing loggers and reconfigure them, at some point, but not at MVP.

For each action the framework will retrieve requirements and iterate over them. 
For each requirement it will iterate over dunder names and try to import them until import succeeds or it runs out of
names. If no import succeeded and `required` is `True`, there will be a failure.

First action that runs is [`SetupBootstrapping`](./thinking_runtime/setup.py). It will try to read any of `__bootstrap__`, 
`__setup__`, `__project__`, `__structure__`. That file should use 
[`register_action(action: ActionType, *, name: ActionName=None, enabled: bool=True)`](./thinking_runtime/setup.py)
to register any custom actions. Before the setup action is executed, following actions are already registered.

>...but can be disabled; document it.

First non-setup action is [`RecogniseRuntime`](./thinking_runtime/defaults/recognise_runtime.py). It will
analyse what is going on in the runtime to figure out if you're running the app or tests and if there are
any facets (think "Spring profiles") enabled. You can configure custom facets with `register_facet(facet: RuntimeFacetDefinition)`
or customize what is the package structure of your code and its tests with `project_structure() -> PackagesStructure`.
Config files used by that actions are the same as for `SetupBootstrapping` or `__runtime__`.

Another default step is [`ConfigureLogging`](./thinking_runtime/defaults/configure_logging.py). Use `__log__`, `__logs__`, `__logging__`
to make calls to [`thinking_runtime.default.logging_config.logging_config: LoggingConfig`](./thinking_runtime/defaults/logging_config.py)
and configure logging aspects like log format, handlers, etc. There is already a default config that will log to stderr
with a sane format, and in case of non-test environment, will als dump logs to a file (with name based on session timestamp).

Sweet part of this setup is that when `ConfigureLogging` is running (so, loading the dunder configs), there is a guarantee
that `RecogniseRuntime` has already executed, so you can safely make statements like

```python
if current_runtime().mode == RuntimeMode.APP:
    logging_config.handlers.streams["STDOUT"].enabled = False

#or
if current_runtime().mode == RuntimeMode.TEST:
    logging_config.format = "..."
```

### [`fluent_container`](./fluent_container) and logging configuration

This package allows for creation of `list`s on steroids, meant to simplify creation of configuration DSLs. 

It exposes [`Container`](./fluent_container/container.py) base class that can hold 
['Identifiable's](./fluent_container/traits.py) (anything that exposes `identifier` property).
It won't allow duplicates (considering only the `identifier`s) and will only accept the type that you specify (raising, 
when you try to append something that doesn't match). Besides that it is ordered like a `list`.

It can also expose views (["closures"](./fluent_container/closure.py)) that filter out anything that doesn't match
view criteria (these usually being "of given type").

Both `Container` and `...Closure`s overload `append(...)` so that you can either pass a concrete instance of 
`Identifiable` or simply constructor arguments.

See [`Handlers`](./thinking_runtime/defaults/logging_config.py) for example usage. Its a container of logging handler
definition. As the framework supports 3 main types of handlers: `StreamHandler` (routing logs to any stream, usually
stdout or stderr), `FileHandler` (dumping logs to file or rotating file) or `RawHandler` (wrapper over a raw `logging.Handler`
and its `identifier`), `Handlers` expose 3 properties: `streams`, `files` and `raw`, being `closures` that match
those specific types. Thanks to that you can use:

```python
handlers.streams.append(NamedTextIO("name", some_stream), "DEBUG")
handlers.files.all #or simply handlers.files, since it supports __iter__ 
handlers.raw["specific_id"]
```

instead of

```python
handlers.append(StreamHandler(NamedTextIO("name", some_stream), "DEBUG"))
[ x for x in handlers if isinstance(FileHandler) ]
{ x.identifier: x for x in handlers if isinstance(RawHandler) }["specific_id"]
```