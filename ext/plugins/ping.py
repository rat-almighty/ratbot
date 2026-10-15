import logging
from datetime import UTC
from datetime import datetime as DateTime
from functools import partial

from discord.ext.commands import is_owner

import ratcore as rc
from ratcore import Interaction

log = logging.getLogger(__name__)
now = partial(DateTime.now, tz=UTC)


async def ping(itc: Interaction):
    t1 = now()
    m = await itc.response.send_message()
    log.info(itc.message)
    t2 = now()


@rc.text_command()
@is_owner()
async def sync(ctx: rc.Context) -> None:
    async with ctx.channel.typing():
        try:
            n = await ctx.bot.tree.sync()
        except Exception:
            _ = await ctx.send("Sync failed")
            raise
        else:
            _ = await ctx.send(
                f"Successfully synchronized {n} command" + "s" if n else "" + "."
            )


async def setup(bot: rc.Bot):
    _ = bot.tree.command()(ping)
    bot.add_command(sync)
