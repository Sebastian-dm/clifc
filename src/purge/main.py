import ifcopenshell
from ifcopenshell.file import file as IfcFile
from ifcopenshell.ifcopenshell_wrapper import item
import ifcopenshell.util.element
import ifcopenshell.api.root


def collect_by_EntityName(item, purgeList=None):
    removeList = []

    cls = item.is_a()
    short = cls[3:] if cls.startswith("Ifc") else cls
    if short in purgeList or cls in purgeList:
        removeList.append(item)
    
    return removeList


def collect_byLayer_(model, purgeList):
    removeList = []

    for layer in model.by_type("IfcPresentationLayerAssignment"):
        if layer.Name in purgeList:
            for item in layer.AssignedItems or []:
                removeList.append(item)
    
    return removeList


def purge(modelPath, savePath, purgeLayers=[], purgeEntityNames=[]):
    model = ifcopenshell.open(modelPath)
    if not isinstance(model, IfcFile):
        raise TypeError("Expected an IFC file model")

    removeList = []
    for item in model.by_type("IfcProduct"):
        removeList.extend(collect_by_EntityName(item, purgeEntityNames))
        removeList.extend(collect_byLayer_(model, purgeLayers))

    for item in set(removeList):
        if len(model.get_inverse(item)) == 0:
            ifcopenshell.api.root.remove_product(model, product=item)
    
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