from pathlib import Path
from typing import ClassVar, Self, cast

from pydantic import BaseModel

import ratbot.yaml as yaml  # noqa: PLR0402, this causes an import cycle


class Model(BaseModel):
    pass


class YamlModel(Model):
    __model_path__: ClassVar[Path]

    @classmethod
    def load(cls) -> Self:
        data = yaml.full_load(cls.__model_path__)
        return cls.model_validate(data)

    def dump(self) -> None:
        data = cast(
            dict[yaml.Document, yaml.Document], self.model_dump(exclude_defaults=True)
        )
        yaml.dump(data, self.__model_path__)
