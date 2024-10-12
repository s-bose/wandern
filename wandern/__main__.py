from typing import Optional

from typer import Typer
from wandern.__version__ import version

app = Typer(name="Wandern")


@app.command()
def version():
    print("wandern version: ", version)


@app.command()
def reset():
    pass


@app.command()
def generate(name: Optional[str] = None):
    """Generates two empty migration scripts UP and DOWN"""


if __name__ == "__main__":
    app()
