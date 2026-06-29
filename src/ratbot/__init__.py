__all__ = ["app", "start"]
__author__ = "Ernie Serrano"
__license__ = "MIT"
__version__ = "0.1.0"

from cyclopts import App

app = App()


@app.command
@app.default
def start() -> None:
    print("Hello, world")
