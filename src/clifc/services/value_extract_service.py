from __future__ import annotations

import sys
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import ifcopenshell
import openpyxl


def _iter_ifc_files(root: Path) -> Iterable[Path]:
    # Recursively find .ifc files (case-insensitive)
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() == ".ifc":
            yield p


def _property_string_treatment(value: str) -> str:
    value = value.replace("[L]%", "")
    if len(value) > 2:
        value = value[:-2]
    value = value.replace(".", "")
    value = re.sub(r"\d", "", value)
    return value


def _stringify_ifc_value(nominal_value: Any, normalize_wrapped_values: bool = True) -> str:
    """
    Convert IFC nominal value objects / python primitives to a stable string.
    ifcopenshell often returns:
      - python primitives (str/int/float/bool)
      - IFC wrapper objects with .wrappedValue
    """
    if nominal_value is None:
        return ""
    if hasattr(nominal_value, "wrappedValue"):
        v = getattr(nominal_value, "wrappedValue")
        if v is None:
            return ""
        out = str(v)
        return _property_string_treatment(out) if normalize_wrapped_values else out
    return str(nominal_value)


def _extract_property_values_from_object(
    obj,
    pset_name: str,
    prop_name: str,
    normalize_wrapped_values: bool = True,
) -> List[str]:
    values = []

    rels = getattr(obj, "IsDefinedBy", None)
    if not rels:
        return values

    for rel in rels:
        if not rel.is_a("IfcRelDefinesByProperties"):
            continue

        pdef = rel.RelatingPropertyDefinition
        if not pdef or not pdef.is_a("IfcPropertySet"):
            continue

        if str(pdef.Name) != pset_name:
            continue

        for prop in pdef.HasProperties or []:
            if str(prop.Name) != prop_name:
                continue

            if prop.is_a("IfcPropertySingleValue"):
                values.append(_stringify_ifc_value(prop.NominalValue, normalize_wrapped_values))

            elif prop.is_a("IfcPropertyEnumeratedValue"):
                values.append(
                    ";".join(
                        _stringify_ifc_value(v, normalize_wrapped_values)
                        for v in prop.EnumerationValues or []
                    )
                )

            elif prop.is_a("IfcPropertyListValue"):
                values.append(
                    ";".join(_stringify_ifc_value(v, normalize_wrapped_values) for v in prop.ListValues or [])
                )

    return values


def _parse_property_name(property_name: str) -> Tuple[str, str]:
    if not property_name or "." not in property_name:
        raise ValueError("propertyName must be in format 'PsetName.PropertyName'.")
    pset_name, prop_name = property_name.split(".", 1)
    pset_name = pset_name.strip()
    prop_name = prop_name.strip()
    if not pset_name or not prop_name:
        raise ValueError("propertyName must be in format 'PsetName.PropertyName'.")
    return pset_name, prop_name


def load_css_hovedbegreb_lookup(
    xlsx_path: str | Path,
    css_col: str = "CCS",
    hovedbegreb_col: str = "Hovedbegreb",
    normalize: bool = True,
) -> Dict[str, str]:
    """
    Reads an .xlsx containing two sheets, each with columns:
      - CCS
      - Hovedbegreb

    Returns a dict: {ccs_value -> hovedbegreb_value}
    If a CCS value appears multiple times across sheets, the first non-empty Hovedbegreb wins.
    """
    xlsx_path = Path(xlsx_path)
    wb = openpyxl.load_workbook(xlsx_path, data_only=True, read_only=True)
    lookup: Dict[str, str] = {}

    def norm(s: object) -> str:
        if s is None:
            return ""
        t = str(s)
        return t.strip() if normalize else t

    for ws in wb.worksheets:
        # Map header -> column index
        header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
        if not header_row:
            continue

        headers = {norm(v): idx for idx, v in enumerate(header_row) if norm(v)}
        if css_col not in headers or hovedbegreb_col not in headers:
            continue

        css_idx = headers[css_col]
        hov_idx = headers[hovedbegreb_col]

        for row in ws.iter_rows(min_row=2, values_only=True):
            css_val = norm(row[css_idx] if css_idx < len(row) else None)
            hov_val = norm(row[hov_idx] if hov_idx < len(row) else None)
            if not css_val:
                continue

            # Keep first non-empty mapping
            if css_val not in lookup and hov_val:
                lookup[css_val] = hov_val
            elif css_val not in lookup and not hov_val:
                # store empty only if nothing else exists (optional behavior)
                lookup[css_val] = ""

    wb.close()
    return lookup


def match_and_concat(
    property_value: str,
    lookup: Dict[str, str],
    sep: str = " ",
    default_hovedbegreb: str = "",
) -> Tuple[str, Optional[str]]:
    """
    Returns:
      (concatenated_output, matched_hovedbegreb_or_None)

    Output is: "<property_value><sep><hovedbegreb>" if matched, otherwise "<property_value>".
    """
    key = property_value.strip()
    hovedbegreb = lookup.get(key)

    if hovedbegreb is None or hovedbegreb == "":
        if default_hovedbegreb:
            return f"{property_value}{sep}{default_hovedbegreb}", default_hovedbegreb
        return property_value, None

    return f"{property_value}{sep}{hovedbegreb}", hovedbegreb


class ValueExtractService:
    def __init__(
        self,
        property_name: str,
        dedupe: bool = False,
        skip_empty: bool = False,
        ccs_lookup_path: Optional[str] = None,
        concat_separator: str = " ",
        default_hovedbegreb: str = "",
        normalize_wrapped_values: bool = True,
    ):
        self.pset_name, self.prop_name = _parse_property_name(property_name)
        self.dedupe = dedupe
        self.skip_empty = skip_empty
        self.concat_separator = concat_separator
        self.default_hovedbegreb = default_hovedbegreb
        self.normalize_wrapped_values = normalize_wrapped_values
        self.lookup = (
            load_css_hovedbegreb_lookup(ccs_lookup_path)
            if ccs_lookup_path
            else None
        )

    def extract_values_from_ifc_file(self, ifc_path: Path) -> List[str]:
        try:
            model = ifcopenshell.open(str(ifc_path))
        except Exception as e:
            print(f"[WARN] Failed to open: {ifc_path} ({e})", file=sys.stderr)
            return []

        found: List[str] = []
        # By spec, most element-like objects are IfcObjectDefinition; this covers elements, types, spatial, etc.
        for obj in model.by_type("IfcObjectDefinition"):
            try:
                found.extend(
                    _extract_property_values_from_object(
                        obj,
                        self.pset_name,
                        self.prop_name,
                        self.normalize_wrapped_values,
                    )
                )
            except Exception as e:
                # Keep going; IFCs can contain oddities.
                oid = getattr(obj, "GlobalId", None)
                print(f"[WARN] Error on object {oid} in {ifc_path.name}: {e}", file=sys.stderr)

        return found

    def extract_values(self, ifc_paths: List[str]) -> List[str]:
        all_values: List[str] = []
        for raw_path in ifc_paths:
            ifc_path = Path(raw_path)
            all_values.extend(self.extract_values_from_ifc_file(ifc_path))

        if self.skip_empty:
            all_values = [v for v in all_values if v != ""]

        if self.dedupe:
            seen = set()
            deduped: List[str] = []
            for value in all_values:
                if value in seen:
                    continue
                seen.add(value)
                deduped.append(value)
            all_values = deduped

        return sorted(all_values)

    def format_output_values(self, values: List[str]) -> List[str]:
        if not self.lookup:
            return values

        out_values: List[str] = []
        for value in values:
            value_out, _ = match_and_concat(
                value,
                self.lookup,
                sep=self.concat_separator,
                default_hovedbegreb=self.default_hovedbegreb,
            )
            out_values.append(value_out)
        return out_values

    def write_output(self, output_path: str, values: List[str]) -> Path:
        out_path = Path(output_path).expanduser()
        if not out_path.is_absolute():
            out_path = (Path.cwd() / out_path).resolve()

        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8", newline="\n") as f:
            for value in values:
                f.write(f"{value}\n")
        return out_path

    def run(self, ifc_paths: List[str], output_path: str) -> Dict[str, Any]:
        values = self.extract_values(ifc_paths)
        output_values = self.format_output_values(values)
        written_path = self.write_output(output_path, output_values)
        return {
            "values": output_values,
            "count": len(output_values),
            "output_path": str(written_path),
        }
