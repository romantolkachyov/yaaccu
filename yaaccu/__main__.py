import typer

from .cli import (
    account,
)


app = typer.Typer()
app.add_typer(account.app, name='account')


if __name__ == '__main__':
    app()
