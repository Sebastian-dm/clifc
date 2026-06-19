import click
from clifc.commands.crop import crop

@click.group()
def cli():
    pass

cli.add_command(crop)

if __name__ == "__main__":
    cli()