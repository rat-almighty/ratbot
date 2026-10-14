"""Slight improvements to the `pyyaml` API."""
# pyright: reportAny = false

__all__ = ["Document", "dump", "full_load"]

import os
from pathlib import Path

import yaml

type StrPath = str | os.PathLike[str]

type Document = (
    str | int | float | bool | None | list[Document] | dict[Document, Document]
)


def full_load(path: Path, /) -> Document:
    return yaml.full_load(path.read_text())


def dump(document: Document, path: StrPath) -> None:
    data = yaml.dump(document)
    with open(path, "w+") as file:
        _ = file.write(data)
