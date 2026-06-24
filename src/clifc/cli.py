import click
from clifc.commands.crop import crop
from clifc.commands.propcheck import propcheck

@click.group()
def cli():
    pass

cli.add_command(crop)
cli.add_command(propcheck)

if __name__ == "__main__":
    cli()