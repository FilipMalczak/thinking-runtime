from thinking_runtime.model import ConfigurationRequirement
#fixme poor hack to avoid circular import

BOOTSTRAP_CONFIG = ConfigurationRequirement(["__bootstrap__", "__setup__", "__project__", "__structure__"])