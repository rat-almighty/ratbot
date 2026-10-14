__all__ = ["Context"]

from functools import cached_property

from discord import Message
from discord.ext import commands


def get_origin(message: Message):
    if message.thread:
        return message.thread
    return message.channel


class Context[T: commands.Bot | commands.AutoShardedBot](commands.Context[T]):
    @cached_property
    def chname(self) -> str | None:
        """Channel name, if any."""
        return getattr(self.channel, "name", None)
