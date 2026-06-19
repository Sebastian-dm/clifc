import click
from clifc.services.crop_service import CropService

@click.command()
@click.argument("input_file")
@click.argument("p1")
@click.argument("p2")
@click.option("--output_file", default=None, help="Output IFC file")
def crop(input_file, p1, p2, output_file):
    """
    Crop an IFC file using two rectangle corners.

    P1 and P2 should be given as quoted coordinate pairs:

        clifc crop model.ifc "627579000 1147842900" "627608000 1147868100"
    """
    CropService().crop_file(input_file, p1, p2, output_file)