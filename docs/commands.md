# CLI Reference

## Overview

CLIFC provides these commands:

- `crop`
- `propcheck`
- `valueextract`
- `merge`

Use:

```bash
clifc --help
```

## crop

Crop an IFC file using two corner points (XY) defining a rectangle.

```bash
clifc crop INPUT_FILE "X1 Y1" "X2 Y2" [-o OUTPUT_FILE] [-v]
```

Options:

- `-o, --output_file`: Output IFC file path.
- `-v, --verbose`: Print additional diagnostics.

## propcheck

Validate IFC properties against YAML rules and generate reports.

```bash
clifc propcheck [PATHS]... -r RULES_FILE [options]
```

Options:

- `-r, --rulespath`: Path to YAML rules file (required).
- `-o, --outputfolder`: Output folder for reports.
- `-s, --schemapath`: Override JSON schema path.
- `-t, --templatepath`: Override HTML template path.
- `-c, --csv_out`: Generate CSV output.
- `-a, --all`: Include passing rows in CSV.
- `-v, --verbose`: Verbose output.

Outputs:

- `propcheck_report.html`
- `propcheck_report.csv` (when `--csv_out` is used)

## valueextract

Extract values for a property path in `PsetName.PropertyName` format.

```bash
clifc valueextract [PATHS]... -p PSET.PROPERTY [options]
```

Options:

- `-p, --property-name`: Property path (required).
- `-o, --out`: Output text file path.
- `--dedupe`: Remove duplicate values.
- `--skip-empty`: Skip empty values.
- `--ccs-xlsx`: Optional lookup file with `CCS` and `Hovedbegreb` columns.
- `--concat-separator`: Separator used for concatenated lookup output.
- `--default-hovedbegreb`: Fallback text when lookup misses.
- `--no-normalize-wrapped`: Disable wrapped-value normalization.

## merge

Combine IFC objects from multiple input IFC files into one output IFC file.

```bash
clifc merge [PATHS]... [-o OUTPUT_FILE] [-v]
```

Options:

- `-o, --output-file`: Output merged IFC path (default: `merged.ifc`).
- `-v, --verbose`: Print additional validation details.

## Notes

- Paths may include IFC files and/or directories.
- Directory inputs are scanned recursively for `.ifc` files.
- The first file is used as the base model.
