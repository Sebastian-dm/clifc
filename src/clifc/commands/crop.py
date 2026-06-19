import click
from clifc.services.crop_service import CropService

@click.command()
@click.argument("input_file")
@click.argument("p1")
@click.argument("p2")
@click.option("-o", "--output_file", default=None, help="Output IFC file")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output")
def crop(input_file, p1, p2, output_file, verbose):
    """
    Crop an IFC file using two rectangle corners.

    P1 and P2 should be given as quoted coordinate pairs:

        clifc crop model.ifc "627579.000 1147842.900" "627608.000 1147868.100"
    """
    CropService().crop_file(input_file, p1, p2, output_file, verbose=verbose)