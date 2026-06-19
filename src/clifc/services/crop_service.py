#!/usr/bin/env python3
import argparse
import ifcopenshell
from ifcopenshell.file import file as IfcFile
import ifcopenshell.geom
from shapely.geometry import box, Point
from tqdm import tqdm
import click

try:
    from ifcopenshell.util import placement as ifc_placement
except Exception:
    ifc_placement = None


class CropService():

    def parse_args(self):
        parser = argparse.ArgumentParser(
            description="Filter IFC by deleting elements outside a rectangular XY boundary"
        )
        parser.add_argument("input_ifc", help="Path to input IFC file")
        parser.add_argument("output_ifc", help="Path to output IFC file")
        parser.add_argument(
            "--p1",
            nargs=2,
            type=float,
            required=True,
            help="First corner (X Y) of rectangle (world coordinates)",
        )
        parser.add_argument(
            "--p2",
            nargs=2,
            type=float,
            required=True,
            help="Opposite corner (X Y) of rectangle (world coordinates)",
        )
        return parser.parse_args()

    def get_project_offset(self, ifc):
        ctxs = ifc.by_type("IfcGeometricRepresentationContext")
        for ctx in ctxs:
            hasop = getattr(ctx, "HasCoordinateOperation", None)
            if hasop:
                conv = hasop[0]
                if conv.is_a("IfcMapConversion"):
                    try:
                        return float(conv.Eastings or 0.0), float(conv.Northings or 0.0)
                    except Exception:
                        pass
        return 0.0, 0.0

    def rect_from_world_points(self, p1, p2, offset):
        xmin = min(p1[0], p2[0]) - offset[0]
        xmax = max(p1[0], p2[0]) - offset[0]
        ymin = min(p1[1], p2[1]) - offset[1]
        ymax = max(p1[1], p2[1]) - offset[1]
        return box(xmin, ymin, xmax, ymax), (xmin, ymin, xmax, ymax)

    def product_bbox_xy(self, shape):
        verts = shape.geometry.verts
        if not verts:
            return None
        xs = verts[0::3]
        ys = verts[1::3]
        return min(xs), min(ys), max(xs), max(ys)

    def placement_world_xy(self, obj):
        try:
            if obj.ObjectPlacement is None:
                return None
            if ifc_placement is None:
                loc = obj.ObjectPlacement.RelativePlacement.Location
                return float(loc.Coordinates[0]), float(loc.Coordinates[1])
            m = ifc_placement.get_local_placement(obj.ObjectPlacement)
            return float(m[0][3]), float(m[1][3])
        except Exception:
            return None

    def object_outside_boundary(self, product, boundary_poly, settings, debug_list):
        try:
            shape = ifcopenshell.geom.create_shape(settings, product)
            bbox = self.product_bbox_xy(shape)
            if bbox is not None:
                pb = box(*bbox)
                if len(debug_list) < 10:
                    debug_list.append({
                        "guid": getattr(product, "GlobalId", None),
                        "prod": product.is_a(),
                        "bbox": bbox,
                        "boundary": boundary_poly.bounds,
                        "method": "geometry"
                    })
                return not pb.intersects(boundary_poly)
        except Exception:
            pass

        pt_xy = self.placement_world_xy(product)
        if pt_xy is not None:
            pt = Point(pt_xy[0], pt_xy[1])
            if len(debug_list) < 10:
                debug_list.append({
                    "guid": getattr(product, "GlobalId", None),
                    "prod": product.is_a(),
                    "point": pt_xy,
                    "boundary": boundary_poly.bounds,
                    "method": "placement"
                })
            return not boundary_poly.contains(pt)

        if len(debug_list) < 10:
            debug_list.append({
                "guid": getattr(product, "GlobalId", None),
                "prod": product.is_a(),
                "info": "no-geom-no-placement",
                "boundary": boundary_poly.bounds,
                "method": "none"
            })
        return True  # If we cannot determine, remove by default

    def crop_file(self, input_file, p1, p2, output_file=None):
        if output_file is None:
            output_file = input_file.replace(".ifc", "_cropped.ifc")

        ifc = ifcopenshell.open(input_file)
        if not isinstance(ifc, IfcFile):
            raise TypeError("Expected an IFC file model")

        offset = self.get_project_offset(ifc)
        boundary_poly, boundary_bounds = self.rect_from_world_points(
            [float(coord) for coord in p1.split(" ")],
            [float(coord) for coord in p2.split(" ")],
            offset
        )

        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_WORLD_COORDS, True)

        products = [e for e in ifc.by_type("IfcProduct") if getattr(e, "Representation", None)]

        inside_count = 0
        outside_count = 0
        debug_list = []

        for prod in tqdm(products, desc="Filtering products"):
            if self.object_outside_boundary(prod, boundary_poly, settings, debug_list):
                ifc.remove(prod)
                outside_count += 1
            else:
                inside_count += 1

        ifc.write(output_file)

        print("Boundary (local IFC coords):", boundary_bounds)
        print("\nFirst up to 10 debug entries (element vs boundary):")
        for d in debug_list:
            print(d)

        print("\nConcluding Report:")
        print(f"Products scanned: {len(products)}")
        print(f"Elements kept inside boundary: {inside_count}")
        print(f"Elements deleted outside boundary: {outside_count}")

if __name__ == "__main__":
    CropService().crop_file(None, None, None)
