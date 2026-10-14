__all__ = ["Bot"]

from typing import Self
from typing import override

from discord import Interaction
from discord import Message
from discord.ext import commands

from .context import Context


class Bot(commands.Bot):
    @override
    async def get_context(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, origin: Message | Interaction, /, *, cls: type[Context[Self]] = Context
    ) -> Context[Self]:
        return await super().get_context(origin, cls=cls)
