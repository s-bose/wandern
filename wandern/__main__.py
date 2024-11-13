from typing import Optional

import typer
from typer import Typer
from wandern.__version__ import __version__

app = Typer(
    name="wandern",
)


@app.command()
def version():
    print("wandern version: ", __version__)


@app.command()
def reset():
    pass


@app.command()
def generate(name: Optional[str] = typer.Option(None, "-n", "--name")):
    """Generates two empty migration scripts UP and DOWN"""
    print(f"{name=}")


if __name__ == "__main__":
    app()
