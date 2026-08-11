from __future__ import annotations

import math
from pathlib import Path
from typing import List, Optional, Tuple

import ifcopenshell
from ifcopenshell.file import file as IfcFile

try:
    from ifcopenshell.util import placement as ifc_placement
except Exception:
    ifc_placement = None


class MergeService:
    def __init__(self, ifc_file_paths: List[str], output_file: str, verbose: bool = False):
        self.ifc_file_paths = ifc_file_paths
        self.output_file = output_file
        self.verbose = verbose

    def _open_model(self, path: str) -> IfcFile:
        model = ifcopenshell.open(path)
        if not isinstance(model, IfcFile):
            raise TypeError(f"Expected an IFC file model for '{path}'.")
        return model

    def _length_unit_signature(self, model: IfcFile) -> str:
        projects = model.by_type("IfcProject")
        if not projects:
            raise ValueError("IfcProject not found while reading units.")

        unit_assignment = getattr(projects[0], "UnitsInContext", None)
        units = getattr(unit_assignment, "Units", None) or []

        length_signatures: List[str] = []
        for unit in units:
            unit_type = getattr(unit, "UnitType", None)
            if str(unit_type) != "LENGTHUNIT":
                continue

            if unit.is_a("IfcSIUnit"):
                length_signatures.append(
                    f"IfcSIUnit:{getattr(unit, 'Name', None)}:{getattr(unit, 'Prefix', None)}"
                )
            elif unit.is_a("IfcConversionBasedUnit"):
                conv = getattr(unit, "ConversionFactor", None)
                value_component = getattr(conv, "ValueComponent", None)
                wrapped = getattr(value_component, "wrappedValue", None)
                unit_component = getattr(conv, "UnitComponent", None)
                length_signatures.append(
                    "IfcConversionBasedUnit:"
                    f"{getattr(unit, 'Name', None)}:"
                    f"{wrapped}:"
                    f"{getattr(unit_component, 'Name', None)}:"
                    f"{getattr(unit_component, 'Prefix', None)}"
                )
            else:
                length_signatures.append(f"{unit.is_a()}:{str(unit)}")

        if not length_signatures:
            raise ValueError("No LENGTHUNIT found in IfcProject.UnitsInContext.")

        return "|".join(sorted(length_signatures))

    def _length_scale_to_meters(self, model: IfcFile) -> float:
        projects = model.by_type("IfcProject")
        unit_assignment = getattr(projects[0], "UnitsInContext", None)
        units = getattr(unit_assignment, "Units", None) or []

        si_prefix_to_scale = {
            None: 1.0,
            "KILO": 1e3,
            "HECTO": 1e2,
            "DECA": 1e1,
            "DECI": 1e-1,
            "CENTI": 1e-2,
            "MILLI": 1e-3,
        }

        for unit in units:
            if str(getattr(unit, "UnitType", None)) != "LENGTHUNIT":
                continue

            if unit.is_a("IfcSIUnit") and str(getattr(unit, "Name", "")) == "METRE":
                prefix = getattr(unit, "Prefix", None)
                return float(si_prefix_to_scale.get(str(prefix) if prefix is not None else None, 1.0))

            if unit.is_a("IfcConversionBasedUnit"):
                conv = getattr(unit, "ConversionFactor", None)
                value_component = getattr(conv, "ValueComponent", None)
                wrapped = getattr(value_component, "wrappedValue", None)
                unit_component = getattr(conv, "UnitComponent", None)
                comp_name = str(getattr(unit_component, "Name", ""))
                comp_prefix = getattr(unit_component, "Prefix", None)
                if comp_name == "METRE" and wrapped is not None:
                    base_scale = float(si_prefix_to_scale.get(str(comp_prefix) if comp_prefix is not None else None, 1.0))
                    return float(wrapped) * base_scale

        raise ValueError("Could not resolve LENGTHUNIT scale to meters.")

    def _placement_world_xy(self, obj) -> Optional[Tuple[float, float]]:
        try:
            placement = getattr(obj, "ObjectPlacement", None)
            if placement is None:
                return None

            if ifc_placement is not None:
                matrix = ifc_placement.get_local_placement(placement)
                return float(matrix[0][3]), float(matrix[1][3])

            rel = placement.RelativePlacement
            loc = rel.Location
            coords = loc.Coordinates
            if len(coords) < 2:
                return None
            return float(coords[0]), float(coords[1])
        except Exception:
            return None

    def _sample_points(self, model: IfcFile, sample_size: int = 25) -> List[Tuple[float, float]]:
        points: List[Tuple[float, float]] = []
        for product in model.by_type("IfcProduct"):
            pt = self._placement_world_xy(product)
            if pt is None:
                continue
            points.append(pt)
            if len(points) >= sample_size:
                break
        return points

    def _min_distance(self, points_a: List[Tuple[float, float]], points_b: List[Tuple[float, float]]) -> Optional[float]:
        if not points_a or not points_b:
            return None

        min_dist = None
        for ax, ay in points_a:
            for bx, by in points_b:
                d = math.hypot(ax - bx, ay - by)
                if min_dist is None or d < min_dist:
                    min_dist = d
        return min_dist

    def _validate_units(self, models: List[IfcFile], labels: List[str]) -> None:
        reference_signature = self._length_unit_signature(models[0])
        for idx in range(1, len(models)):
            signature = self._length_unit_signature(models[idx])
            if signature != reference_signature:
                raise ValueError(
                    "Cannot merge IFC files with different length units. "
                    f"Reference ({labels[0]}): {reference_signature}; "
                    f"Found ({labels[idx]}): {signature}"
                )

    def _validate_proximity(self, models: List[IfcFile], labels: List[str], threshold_meters: float = 500.0) -> None:
        reference_model = models[0]
        reference_points = self._sample_points(reference_model)
        if not reference_points:
            raise ValueError(f"Could not find test objects with placement in '{labels[0]}'.")

        scale_to_meters = self._length_scale_to_meters(reference_model)
        threshold_in_model_units = threshold_meters / scale_to_meters

        for idx in range(1, len(models)):
            current_points = self._sample_points(models[idx])
            if not current_points:
                raise ValueError(f"Could not find test objects with placement in '{labels[idx]}'.")

            min_dist = self._min_distance(reference_points, current_points)
            if min_dist is None:
                raise ValueError(
                    f"Could not compute test-object distance between '{labels[0]}' and '{labels[idx]}'."
                )

            if self.verbose:
                distance_m = min_dist * scale_to_meters
                print(
                    f"[INFO] Minimum sampled distance {labels[0]} <-> {labels[idx]}: "
                    f"{distance_m:.3f} m"
                )

            if min_dist > threshold_in_model_units:
                distance_m = min_dist * scale_to_meters
                raise ValueError(
                    "Cannot merge IFC files because sampled objects are too far apart. "
                    f"Distance between '{labels[0]}' and '{labels[idx]}' is {distance_m:.3f} m "
                    f"(limit: {threshold_meters:.3f} m)."
                )

    def merge(self) -> int:
        if len(self.ifc_file_paths) < 2:
            raise ValueError("At least two IFC files are required for merge.")

        labels = [Path(p).name for p in self.ifc_file_paths]
        models = [self._open_model(p) for p in self.ifc_file_paths]

        self._validate_units(models, labels)
        self._validate_proximity(models, labels)

        target = models[0]

        # Keep the first file as base model and copy object definitions from additional files.
        for src in models[1:]:
            for obj in src.by_type("IfcObject"):
                target.add(obj)

        output_path = Path(self.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        target.write(str(output_path))

        if self.verbose:
            print(f"[INFO] Merged {len(self.ifc_file_paths)} IFC file(s) into {output_path}")

        return 0
