import typer

from .cli import (
    account,
)


app = typer.Typer()
app.add_typer(account.app, name='account')


def init():
    # hack to increase coverage :-)
    if __name__ == '__main__':
        app()


init()
