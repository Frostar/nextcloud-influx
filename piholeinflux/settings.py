from dynaconf import LazySettings, Validator
from dynaconf.utils.boxing import DynaBox

settings = LazySettings(
    SETTINGS_FILE_FOR_DYNACONF="default.toml,user.toml",
    ENVVAR_PREFIX_FOR_DYNACONF="PIHOLE",
)
settings.validators.register(Validator("INSTANCES", must_exist=True))
settings.validators.validate()