from unittest import mock

import typer

from yaaccu import __main__


def test_cli_simple():
    assert __main__
    assert isinstance(__main__.app, typer.Typer)
    __main__.init()
    with mock.patch.object(__main__, "app"):
        with mock.patch.object(__main__, "__name__", "__main__"):
            __main__.init()
