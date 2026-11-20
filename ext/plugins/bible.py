import json
import random
from pathlib import Path
from typing import Literal
from typing import final

import aiohttp
from aiofiles import open

from ratbot.model import Model
from ratcore import Bot
from ratcore import Cog
from ratcore import Context
from ratcore import text_command


class Root(Model):
    Translation: Literal["RST"]
    Books: list[Book]


class Book(Model):
    BookId: int
    Chapters: list[Chapter]


class Chapter(Model):
    ChapterId: int
    Verses: list[Verse]


class Verse(Model):
    VerseId: int
    Text: str


SOURCE = "https://gist.githubusercontent.com/a1ip/0a5ec1b89e79b4490ef5992a80e72eeb/raw/643fb1089165676903b05852cb7d72cb2f51b2f8/rst.json"
STORE = Path(__file__).with_name("rst.json")


async def fetch_synodal_bible():
    async with aiohttp.ClientSession() as client:
        resp = await client.get(SOURCE)
        root = Root.model_validate_json(await resp.read())

    chunks: list[str] = []
    for book in root.Books:
        for chapter in book.Chapters:
            chunk: list[str] = []
            for verse in chapter.Verses:
                text = verse.Text
                chunk.append(text)
                last_char = text[-1:]
                match last_char:
                    case "." | "!" | "?" | '"' | ")":
                        chunks.append(" ".join(chunk))
                        chunk.clear()
                    case c if c in ",;:–-" or c.islower():
                        pass
                    case c:
                        raise RuntimeError(f"unexpected sentence ending: {text!r}")
    async with open(STORE, "w") as file:
        _ = await file.write(json.dumps(chunks, ensure_ascii=False))
    return chunks


@final
class SynodalBible(Cog, name="THE HOLY BIBLE"):
    __name__ = "THE HOLY BIBLE"
    __cog_name__ = "THE HOLY BIBLE"
    __cog_group_name__ = "THE HOLY BIBLE"

    def __init__(self, bot: Bot) -> None:
        self.bot = bot
        self.__chunks: list[str] | None = None

    async def get_chunks(self) -> list[str]:
        if self.__chunks is None:
            try:
                async with open(STORE) as file:
                    text = await file.read()
                self.__chunks = json.loads(text)
            except FileNotFoundError:
                self.__chunks = await fetch_synodal_bible()
            assert self.__chunks is not None
        return self.__chunks

    @text_command(aliases=("bible_chunk",))
    async def synode(self, ctx: Context):
        """Gets a random chunk from the synodal bible.

        Has the potential to be larger than a single verse, though oft is not."""
        return await ctx.reply(random.choice(await self.get_chunks()))


async def setup(bot: Bot):
    cog = SynodalBible(bot)
    await bot.add_cog(cog)
