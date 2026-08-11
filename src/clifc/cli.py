import click
from clifc.commands.crop import crop
from clifc.commands.merge import merge
from clifc.commands.propcheck import propcheck
from clifc.commands.valueextract import valueextract

@click.group()
def cli():
    pass

cli.add_command(crop)
cli.add_command(merge)
cli.add_command(propcheck)
cli.add_command(valueextract)

if __name__ == "__main__":
    cli(prog_name="clifc")