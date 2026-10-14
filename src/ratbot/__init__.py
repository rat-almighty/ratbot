__all__ = ["app", "start"]

__author__ = "Ernie Serrano"
__license__ = "MIT"
__version__ = "0.1.0"


from pathlib import Path
from typing import ClassVar, NewType

import discord
from cyclopts import App

from .model import YamlModel
from .paths import CONFIG_DIRECTORY

app = App()

Token = NewType("Token", str)


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
    try:
        token = Tokens.load().main
    except FileNotFoundError:
        import sys

        print(
            f"The `{Tokens.__model_path__.name}` file was not found.",
            f"Please run `{sys.argv[0]} init` to perform configuration.",
            sep="\n",
        )
        sys.exit(1)

    intents = discord.Intents.default()
    intents.message_content = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as user: {client.user}")

    @client.event
    async def on_message(message: discord.Message):
        if message.author.bot:
            return

        if message.content.startswith("rat"):
            _ = await message.channel.send("rat")

    client.run(token)
