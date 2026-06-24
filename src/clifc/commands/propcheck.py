import os, sys
import click

from importlib.resources import files

from clifc.services.propcheck_service import PropCheckService
from clifc.helpers.directory import DirectoryHelper

@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("-r", "--rulespath", required=True, type=click.Path(exists=True), help="YAML rules file")
@click.option("-o", "--outputfolder", default=None, help="Folder to output reports to (default: current folder)")
@click.option("-s", "--schemapath", default=None, help="Path to override the default JSON schema file for rules validation")
@click.option("-t", "--templatepath", default=None, help="Path to override the default HTML template for report generation")
@click.option("-c", "--csv_out", is_flag=True, default=False, help="Export results to CSV file")
@click.option("-a", "--all", is_flag=True, default=False, help="Include all (also passing) rows in CSV")
@click.option("-v", "--verbose", is_flag=True, default=False, help="Enable verbose output")
def propcheck(paths, rulespath, outputfolder, schemapath, templatepath, csv_out, all, verbose):
    """Check IFC files against property rules defined in a YAML file.
    """
    if paths is None or len(paths) == 0:
        print("[red]Error: No paths provided for .ifc files or directories.[/red]")
        sys.exit(1)
    ifcFilePaths = DirectoryHelper().collect_ifc_file_paths(paths)
    if not ifcFilePaths:
        print("[red]Error: No .ifc files found in the specified paths.[/red]")
        sys.exit(1)
    if rulespath and not os.path.isfile(rulespath):
        print(f"[red]Error: Rules file '{rulespath}' not found.[/red]")
        sys.exit(2)
    if outputfolder and not os.path.isdir(outputfolder):
        print(f"[red]Error: Output folder '{outputfolder}' does not exist.[/red]")
        sys.exit(3)
    if schemapath is None:
        schemapath = files("clifc.schemas").joinpath("propcheck.schema.json")
    if templatepath is None:
        templatepath = files("clifc.templates").joinpath("propcheck.html.j2")

    propcheck_service = PropCheckService(ifcFilePaths,
                                         rulesPath=rulespath,
                                         outputPath=outputfolder,
                                         schemaPath=schemapath,
                                         templatePath=templatepath,
                                         outputCsv=csv_out,
                                         includePassingRows=all,
                                         verbose=verbose)
    exit_code = propcheck_service.propcheck()
    sys.exit(exit_code)