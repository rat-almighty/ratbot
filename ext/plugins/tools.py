import asyncio
import asyncio.subprocess as process
import logging
import re
from asyncio import Semaphore
from collections.abc import Awaitable
from collections.abc import Callable
from datetime import UTC
from datetime import datetime as DateTime
from functools import partial
from functools import wraps
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import LiteralString
from typing import final

from discord.file import File
from frozenlist import FrozenList as flist

import ratcore as rc
from ratcore import Bot
from ratcore import Cog
from ratcore import Context
from ratcore import Message

log = logging.getLogger(__name__)
now = partial(DateTime.now, tz=UTC)


MAX_CONCURRENT_LATEX_THREADS = Semaphore(4)
MAX_CONCURRENT_TYPST_THREADS = Semaphore(4)

BASE_COMMAND: flist[LiteralString] = flist(
    (
        "bwrap",
        "--die-with-parent",
        "--clear-env",
        "--setenv",
        "PATH",
        "/usr/bin",
        "--dev",
        "/dev",
        "--proc",
        "/proc",
        "--tmpfs",
        "/tmp",
    )
)

for path in ("/usr", "/lib", "/lib64", "/var/lib/texmf"):
    if Path(path).exists():
        BASE_COMMAND.extend(["--ro-bind", path, path])
    else:
        log.warning(f"path does not exist: {path}")

BASE_COMMAND.freeze()


async def _compile_latex(tmp_dir: Path, _expr: str) -> bytes:
    _command = (
        *BASE_COMMAND,
        "--bind",
        tmp_dir.as_posix(),
        "--chdir",
        tmp_dir.as_posix(),
        "--",
    )
    raise NotImplementedError("_compile_latex function")


async def compile_latex(expr: str):
    async with MAX_CONCURRENT_LATEX_THREADS:
        with TemporaryDirectory() as dir:
            retval = await _compile_latex(Path(dir), expr)
    return retval


def concurrency_limit(n: int):
    """Limit a function to `n` concurrent invocations."""

    def limiter[**P, RT](fn: Callable[P, Awaitable[RT]]) -> Callable[P, Awaitable[RT]]:
        LIMIT = Semaphore(n)

        @wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> RT:
            async with LIMIT:
                rv = await fn(*args, **kwargs)
            return rv

        return wrapper

    return limiter


@final
class CompileError(RuntimeError):
    def __init__(self, code: int, stderr: str, kind: LiteralString = "Process"):
        super().__init__(
            f"{kind} failed with error code {code}:\n" + "```\n" + stderr + "```"
        )
        self.code = code
        self.stderr = stderr


@concurrency_limit(4)
async def compile_typst(
    body: str, /, jobs: int = 2, ppi: int = 300, timeout: int = 15
) -> bytes:
    with TemporaryDirectory() as root:
        Path(root).mkdir(exist_ok=True)
        assert Path(root).is_dir()
        proc = await process.create_subprocess_exec(
            "typst",
            "compile",
            "--format=png",
            f"--{root=!s}",
            f"--{jobs=}",
            f"--{ppi=}",
            "-",
            "-",
            stdin=process.PIPE,
            stdout=process.PIPE,
            stderr=process.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(body.encode()), timeout)
        code = proc.returncode
        assert Path(root).is_dir()
    if code:
        raise CompileError(code, stderr.decode(), kind="Typst compilation")
    return stdout


TYPST_PRELUDE = Path(__file__).with_name("typst_prelude.typ").read_text() + "\n"


@final
class Tools(Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @rc.hybrid_command(aliases=("ltx",))
    async def latex(self, _ctx: Context, latex: str) -> None:
        """Renders LaTeX output"""
        image = BytesIO(await compile_latex(latex))
        _ = await _ctx.reply(file=File(image, "latex-output.png"))

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or getattr(message.channel, "name", None) == "rat":
            return

        code_blocks: list[str] = re.findall(
            r"```typ(?:st)?\s*\n((?:[^`]|`[^`]|``[^`])+)\s*```",
            message.content,
            re.DOTALL | re.IGNORECASE,
        )
        if not code_blocks:
            return
        try:
            images: list[File] = []
            for i, block in enumerate(code_blocks):
                if block and block[-1] == "\n":
                    block = block[: len(block) - 1]
                image = BytesIO(await compile_typst(TYPST_PRELUDE + block))
                images.append(File(image, f"typst-output-{i}.png"))
            if images:
                _ = await message.reply(files=images)
        except Exception as err:
            _ = await message.reply(f"{type(err).__name__}: {err}")
            raise


async def setup(bot: Bot):
    cog = Tools(bot)
    await bot.add_cog(cog)
