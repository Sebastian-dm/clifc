import sys

import click

from clifc.helpers.directory import DirectoryHelper
from clifc.services.value_extract_service import ValueExtractService


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("-p", "--property-name", "property_name", required=True, help="Property path in format PsetName.PropertyName")
@click.option("-o", "--out", default="property_values.txt", help="Output txt file path")
@click.option("--dedupe", is_flag=True, default=True, help="Remove duplicate values (keeps first-seen order before sorting)")
@click.option("--skip-empty", is_flag=True, default=True, help="Skip empty-string values")
@click.option("--ccs-xlsx", default=None, type=click.Path(exists=True, dir_okay=False), help="Optional XLSX lookup file with CCS and Hovedbegreb columns")
@click.option("--concat-separator", default=" ", show_default=True, help="Separator used when concatenating matched Hovedbegreb")
@click.option("--default-hovedbegreb", default="", help="Fallback Hovedbegreb when lookup entry is missing")
@click.option("--no-normalize-wrapped", is_flag=True, default=False, help="Keep IFC wrapped values as-is without CCS-style normalization")
def valueextract(
    paths,
    property_name,
    out,
    dedupe,
    skip_empty,
    ccs_xlsx,
    concat_separator,
    default_hovedbegreb,
    no_normalize_wrapped,
):
    """Extract IFC property values from one or more IFC files or directories."""
    if paths is None or len(paths) == 0:
        print("[red]Error: No paths provided for .ifc files or directories.[/red]")
        sys.exit(1)

    ifc_file_paths = DirectoryHelper().collect_ifc_file_paths(paths)
    if not ifc_file_paths:
        print("[red]Error: No .ifc files found in the specified paths.[/red]")
        sys.exit(1)

    try:
        service = ValueExtractService(
            property_name=property_name,
            dedupe=dedupe,
            skip_empty=skip_empty,
            ccs_lookup_path=ccs_xlsx,
            concat_separator=concat_separator,
            default_hovedbegreb=default_hovedbegreb,
            normalize_wrapped_values=not no_normalize_wrapped,
        )
        result = service.run(ifc_file_paths, out)
    except ValueError as e:
        print(f"[red]Error: {e}[/red]")
        sys.exit(2)
    except Exception as e:
        print(f"[red]Error: value extraction failed: {e}[/red]")
        sys.exit(3)

    print(f"Wrote {result['count']} value(s) to: {result['output_path']}")
