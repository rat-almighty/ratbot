__all__ = [
    "Bot",
    "CheckFailure",
    "Cog",
    "CommandInvokeError",
    "Context",
    "ContextABC",
    "Intents",
    "Interaction",
    "Message",
    "command",
    "get_ext_path",
    "is_owner",
    "text_command",
]

import sys
from collections import deque
from collections.abc import Iterator
from functools import cache
from pathlib import Path

from discord import Intents
from discord import Interaction
from discord import Message
from discord.app_commands import command
from discord.ext.commands import CheckFailure
from discord.ext.commands import Cog
from discord.ext.commands import CommandInvokeError
from discord.ext.commands import command as text_command
from discord.ext.commands import is_owner

from .bot import Bot
from .context import Context as ContextABC

type Context = ContextABC[Bot]


@cache
def get_ext_path():
    this_dir = Path(__file__).parent
    repo_root = this_dir.parent.parent
    extdir = (repo_root / "ext").resolve()
    assert extdir.is_dir()

    e = extdir.as_posix()
    if e not in sys.path:
        sys.path.append(e)

    return extdir


def get_plugins() -> Iterator[str]:
    dirs: deque[tuple[Path, str]] = deque([(get_ext_path() / "plugins", "plugins")])
    while dirs:
        dir, prefix = dirs.popleft()
        for path in dir.iterdir():
            if path.name.startswith((".", "_")):
                continue
            p_prefix = prefix + "." + path.name.rstrip(".py")
            if path.is_dir():
                dirs.append((path, p_prefix))
            elif path.is_file() and path.suffix.endswith(".py"):
                yield p_prefix
