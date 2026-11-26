__all__ = ["app", "start"]

__author__ = "Ernie Serrano"
__license__ = "MIT"
__version__ = "0.1.0"


import logging
from contextlib import suppress
from pathlib import Path
from typing import ClassVar
from typing import NewType

from cyclopts import App
from discord import Forbidden
from discord import NotFound
from discord.utils import setup_logging

import ratcore as rc
from ratcore import Message
from ratcore import get_plugins

from .model import YamlModel
from .paths import CONFIG_DIRECTORY

Token = NewType("Token", str)

app = App()
log = logging.getLogger(__name__)


class Tokens(YamlModel):
    __model_path__: ClassVar[Path] = CONFIG_DIRECTORY / "tokens.yaml"

    main: Token
    devel: Token | None = None


@app.command
def init(main: Token, devel: Token | None = None, /) -> None:
    """Create ratbot's configuration."""

    Tokens(main=main, devel=devel).dump()


@app.command
@app.default
def start() -> None:
    """Start the application."""
    setup_logging()

    try:
        token = Tokens.load().main
    except FileNotFoundError:
        import sys

        log.critical(
            f"The `{Tokens.__model_path__.name}` file was not found.\n"
            f"Please run `{sys.argv[0]} init` to perform configuration."
        )
        sys.exit(1)

    intents = rc.Intents.default()
    intents.expressions = True
    intents.messages = True
    intents.message_content = True

    client = rc.Bot(("r.", "rat "), intents=intents)

    plugins_loaded = False

    @client.event
    async def on_ready():
        nonlocal plugins_loaded
        log.info(f"Logged in as user: {client.user}")

        if plugins_loaded:
            return
        n = 0
        for n, plugin in enumerate(get_plugins(), start=1):
            await client.load_extension(plugin)
            log.info(f"Loaded plugin: {plugin}")
        plugins_loaded = True
        log.info(f"Loaded {n} plugin" + ("s" if n != 1 else "") + "!")

    @client.event
    async def on_message(message: Message):
        if message.author.bot:
            return

        ctx = await client.get_context(message)

        if ctx.chname == "rat":
            if message.content == "rat" and not message.attachments:
                _ = await message.channel.send("rat")
            else:
                with suppress(Forbidden, NotFound):
                    await message.delete()
        else:
            if message.content.startswith("rat"):
                _ = await message.channel.send("rat")
            await client.invoke(ctx)

    @client.event
    async def on_message_edit(_before: Message, message: Message):
        if message.author.bot:
            return
        if getattr(message.channel, "name", None) == "rat":
            await message.delete()

    client.run(token, log_handler=None)
