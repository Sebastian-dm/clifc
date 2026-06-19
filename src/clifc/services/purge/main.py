import ifcopenshell
from ifcopenshell.file import file as IfcFile
from ifcopenshell.ifcopenshell_wrapper import item

import ifcopenshell.api.root
import ifcopenshell.api.layer


def entityName_in_purgelist(item, purgeList=None):
    cls = item.is_a()
    short = cls[3:] if cls.startswith("Ifc") else cls
    if short in purgeList or cls in purgeList:
        return True
    
    return False


def collect_products_in_layers(model, layers):
    products = set()
    for layer in model.by_type("IfcPresentationLayerAssignment"):
        if layer.Name in layers:
            for item in layer.AssignedItems:
                for shape_rep in (
                    inv for inv in model.get_inverse(item)
                    if inv.is_a("IfcShapeRepresentation")
                ):
                    for prod_rep in (
                        inv for inv in model.get_inverse(shape_rep)
                        if inv.is_a("IfcProductRepresentation")
                    ):
                        for product in (
                            inv for inv in model.get_inverse(prod_rep)
                            if inv.is_a("IfcProduct")
                        ):
                            products.add(product)
    return list(products)




def purge(modelPath, savePath, purgeLayers=[], purgeEntityNames=[]):
    purgeLayers = purgeLayers or set()
    purgeEntityNames = purgeEntityNames or set()
    
    model = ifcopenshell.open(modelPath)
    if not isinstance(model, IfcFile):
        raise TypeError("Expected an IFC file model")
    
    

    removeList = []
    products = model.by_type("IfcProduct")
    for p in products:
        if entityName_in_purgelist(p, purgeEntityNames):
            removeList.append(p)

    for p in removeList:
        if p.is_a("IfcProduct"):
            ifcopenshell.api.root.remove_product(model, product=p)

    productsToRemove = collect_products_in_layers(model, purgeLayers)
    for product in productsToRemove:
        ifcopenshell.api.root.remove_product(model, product=product)

    model.write(savePath)
    return


def main():
    modelPath = "models/KKU_K19_S1_N20.ifc"
    savePath = modelPath.split(".ifc")[0] + "_purged.ifc"
    ENTITY_NAMES = {
        "Shape",
        "Line String"
    }
    TARGET_LAYERS = {
        "3D TA_G_RGN_Pkt--_P",
        "3D TA_G_RGN_Pkt--_P_--U",
        "TA_G_RGN_BronT_P",
        "TA_G_RGN_BronT_P_RST",
        "TA_G_RGN_Pkt-T_P_TLS::TA_G_RGN_Pkt-T_P_TLS-alt"
    }
    purge(modelPath,
          savePath,
          purgeLayers = TARGET_LAYERS,
          purgeEntityNames = ENTITY_NAMES)
    print("finished purge")

if __name__ == "__main__":
    main()