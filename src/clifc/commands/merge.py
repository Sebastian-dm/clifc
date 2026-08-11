import sys

import click

from clifc.helpers.directory import DirectoryHelper
from clifc.services.merge_service import MergeService


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("-o", "--output-file", default="merged.ifc", help="Output merged IFC file")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose output")
def merge(paths, output_file, verbose):
    """Merge IFC objects from multiple IFC files into one IFC model."""
    if paths is None or len(paths) == 0:
        print("[red]Error: No paths provided for .ifc files or directories.[/red]")
        sys.exit(1)

    ifc_file_paths = DirectoryHelper().collect_ifc_file_paths(paths)
    if len(ifc_file_paths) < 2:
        print("[red]Error: At least two .ifc files are required for merge.[/red]")
        sys.exit(1)

    try:
        service = MergeService(ifc_file_paths=ifc_file_paths, output_file=output_file, verbose=verbose)
        exit_code = service.merge()
    except ValueError as e:
        print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        print(f"[red]Error: merge failed: {e}[/red]")
        sys.exit(3)

    print(f"Merged {len(ifc_file_paths)} file(s) into: {output_file}")
    sys.exit(exit_code)
