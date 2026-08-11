# Troubleshooting

## Command not found: `clifc`

Install in editable mode from the repository root:

```bash
pip install -e .
```

## Merge fails with unit mismatch

All merge inputs must use the same IFC length units. Re-export models with matching units and retry.

## Merge fails with distance error (> 500 m)

Merge checks sampled object placements across files. Ensure the models are in the same coordinate context and physically near each other.

## No IFC files found

Provide at least one valid `.ifc` file path or a directory containing `.ifc` files.

## propcheck schema/template issues

If using custom schema/template paths, verify that the files exist and are readable.
