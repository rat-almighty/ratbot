import logging
from datetime import UTC
from datetime import datetime as DateTime
from functools import partial
from types import TracebackType
from typing import final

from discord.ext.commands import is_owner

import ratcore as rc
from ratcore import Bot
from ratcore import CheckFailure
from ratcore import Cog
from ratcore import CommandInvokeError
from ratcore import Context

log = logging.getLogger(__name__)
now = partial(DateTime.now, tz=UTC)


IGNORED_ERRORS = (CheckFailure, NotImplementedError)


def to_exc_info[Exc: Exception](e: Exc) -> tuple[type[Exc], Exc, TracebackType | None]:
    return (type(e), e, e.__traceback__)


@final
class Admin(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @rc.text_command()
    async def ping(self, ctx: Context):
        """pong"""
        _ = await ctx.reply("pong")

    @rc.text_command()
    @is_owner()
    async def sync(self, _ctx: Context) -> None:
        """Synchronizes the command list."""
        raise NotImplementedError()

    @Cog.listener()
    async def on_command_error(self, ctx: Context, err: Exception):
        if isinstance(err, CommandInvokeError):
            err = err.original

        async def show_error():
            nonlocal ctx
            nonlocal err

            name = type(err).__name__
            note = str(err)
            if not note:
                note = "(no explanation provided)"
            _ = await ctx.reply(f"`{name}`: {note}")

        if isinstance(err, IGNORED_ERRORS):
            await show_error()
            return

        if await self.bot.is_owner(ctx.author):
            await show_error()

        command = ctx.command
        assert command is not None
        log.exception(
            f"An {type(err).__name__} exception occurred while handling the '{command.name}' command:",
            exc_info=to_exc_info(err),
        )


async def setup(bot: Bot):
    cog = Admin(bot)
    await bot.add_cog(cog)
