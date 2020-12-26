import typer


app = typer.Typer()


@app.command()
def create(name: str):
    typer.echo(f"Hello {name}")


@app.command()
def show(name: str, formal: bool = False):
    if formal:
        typer.echo(f"Goodbye Ms. {name}. Have a good day.")
    else:
        typer.echo(f"Bye {name}!")
