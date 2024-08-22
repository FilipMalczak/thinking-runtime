import logging
import os.path
import sys
from abc import abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from logging.handlers import RotatingFileHandler
from typing import TextIO, NamedTuple, Self, Protocol

from fluent_container.closure import SubtypeMatchingClosure, SearchClosure
from fluent_container.container import Container
from fluent_container.traits import Identifiable, Enablable, name_as_id, NameAsId

LogLevel = int | str
#todo enumeration?

STANDARD_LEVELS = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
MAX_STANDARD_LEVEL_LENGTH = max(len(l) for l in STANDARD_LEVELS)
L = str(MAX_STANDARD_LEVEL_LENGTH) # shortcut for easier embedding

def resolve_level(level: LogLevel) -> int:
    assert isinstance(level, LogLevel) #todo msg
    if isinstance(level, int):
        return level
    return getattr(logging, level)


FormatDefinition = str | logging.Formatter

def resolve_formatter(fmt: FormatDefinition, style: str):
    if not isinstance(fmt, logging.Formatter):
        fmt = logging.Formatter(fmt, style = style)
    return fmt



_I = 0


@name_as_id
class NamedTextIO(NamedTuple):
    name: str
    io: TextIO

    @classmethod
    def of(cls, stream: TextIO) -> Self:
        global _I
        name = f"NamedStream{_I}"
        _I += 1
        return NamedTextIO(name, stream)


@name_as_id
class Stream(Enum):
    STDOUT = NamedTextIO("STDOUT", sys.stdout)
    STDERR = NamedTextIO("STDERR", sys.stderr)


class HandlerDefinition(Identifiable, Enablable, Protocol):
    level: LogLevel = logging.DEBUG
    format: FormatDefinition = None

    def to_native_handler(self, format_style: str, default_format: FormatDefinition, default_level: LogLevel) -> logging.Handler | None:
        if not self.enabled:
            return None
        out = self._construct_native_handler()
        out.setLevel(resolve_level(self.level or default_level))
        out.setFormatter(resolve_formatter(self.format or default_format, format_style))
        return out

    @abstractmethod
    def _construct_native_handler(self) -> logging.Handler: pass



@dataclass
class LogStream(HandlerDefinition, NameAsId):
    stream: NamedTextIO
    level: LogLevel = logging.DEBUG
    format: FormatDefinition = None
    enabled: bool = True

    @property
    def name(self) -> str:
        return self.stream.name

    def _construct_native_handler(self) -> logging.Handler:
        return logging.StreamHandler(self.stream.io)



@dataclass
class RotationDefinition:
    max_bytes: int
    backup_count: int = 0


class FilesystemCoordinates(NamedTuple):
    filename: str
    base_dir: str = None

    @property
    def path(self) -> str:
        base_dir = self.base_dir or "."
        return os.path.join(base_dir, self.filename)


@dataclass
class LogFile(HandlerDefinition, Identifiable):
    filename: str
    base_dir: str = None
    rotation: RotationDefinition = None
    level: LogLevel = logging.DEBUG
    format: FormatDefinition = None
    enabled: bool = True

    @property
    def filesystem_coordinates(self) -> FilesystemCoordinates:
        return FilesystemCoordinates(self.filename, self.base_dir)

    @property
    def identifier(self) -> FilesystemCoordinates:
        return self.filesystem_coordinates

    def _construct_native_handler(self) -> logging.Handler:
        if self.rotation is None:
            return logging.FileHandler(self.filesystem_coordinates.path)
        return RotatingFileHandler(self.filesystem_coordinates.path, maxBytes=self.rotation.max_bytes, backupCount=self.rotation.backup_count)


class RawHandler(HandlerDefinition, NameAsId):
    name: str
    backend: logging.Handler
    enabled: bool = True

    def _construct_native_handler(self) -> logging.Handler:
        return self.backend

class StreamHandlersClosure(SubtypeMatchingClosure, SearchClosure):
    def __init__(self, handlers: list[HandlerDefinition]):
        self._bind(handlers, LogStream)


class FileHandlersClosure(SubtypeMatchingClosure, SearchClosure):
    def __init__(self, handlers: list[HandlerDefinition]):
        self._bind(handlers, LogFile)


class RawHandlersClosure(SubtypeMatchingClosure, SearchClosure):
    def __init__(self, handlers: list[HandlerDefinition]):
        self._bind(handlers, RawHandler)


class Handlers(Container):
    def __init__(self, handlers: list[HandlerDefinition] = None):
        Container.__init__(self, HandlerDefinition, handlers or [])

    @property
    def streams(self) -> StreamHandlersClosure:
        return StreamHandlersClosure(self)

    @property
    def files(self) -> FileHandlersClosure:
        return FileHandlersClosure(self)

    @property
    def raw(self) -> RawHandlersClosure:
        return RawHandlersClosure(self)

    @staticmethod
    def defaults():
        out = Handlers()
        out.streams.append(Stream.STDOUT.value, enabled=False)
        out.streams.append(Stream.STDERR.value)
        #log file appended in actions prepare(), as it requires runtime to be known
        return out

#todo add collapsed module name; https://docs.python.org/3/library/logging.html#logging.setLogRecordFactory
# by collapsed I mean "foo.bar.baz" -> "f.b.baz" and stuff like that

class FormatStyle(Enum):
    LEGACY = "%"
    FORMAT = "{"
    TEMPLATE = "$"

@dataclass
class LoggingConfig:
    format: FormatDefinition = "[{levelname:^"+L+"}] {asctime} | {name:^5} @{lineno} :: {msg}" #todo
    format_style: FormatStyle = FormatStyle.FORMAT
    level: LogLevel = None #default set in prepare() of configure_logging action (as it requires runtime to be known already)
    log_dir: str = "./logs"
    handlers: Handlers = field(default_factory=Handlers.defaults)

logging_config = LoggingConfig()
