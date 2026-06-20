import ifcopenshell
import ifcopenshell.util.element
import uuid
from ifcopenshell.file import file as IfcFile


InjectProperties = {
    "Verkupplýsingar.Vegnafn": "Laugavegur / Suðurlandsbraut",
    "Verkupplýsingar.Heiti hæðarlegu": "B2441300_BORG_TOPO_3D_001_P12",
    "Verkupplýsingar.Heiti planlegu": "BL130-STR-IDA-CC-NAL",
    "Verkupplýsingar.Svædi": "130",
    "Verkupplýsingar.Veglikan": "BL130-STR-IDA-DM-21000",
    "Verkupplýsingar.SVF": "Reykjavik",
    "Verkupplýsingar.Veghaldari": "Reykjavik",
    "Verkupplýsingar.Hlid": "N/A",
    "Verkupplýsingar.Nafn byggingarhluta": "",
    "Verkupplýsingar.Verkþáttur": "",
    "Verkupplýsingar.Verkþáttarheiti": "",
    "Verkupplýsingar.Ástand": "Nýtt"
    }


class InjectService:

    def __init__(self, input_file):
        self.ifc = ifcopenshell.open(input_file)
        self.ifcFileName = input_file.split("/")[-1]
        if not isinstance(self.ifc, IfcFile):
            raise TypeError("Expected an IFC file model")
    

    def GetObjectLayerInformation(self):
        objectLayerInformation = {}
        for presentationLayer in self.ifc.by_type('IFCPRESENTATIONLAYERASSIGNMENT'):
            layerData = {}
            layerData.update({"Number": presentationLayer.Name.split("_")[0]})
            layerData.update({"Name": "_".join(presentationLayer.Name.split("_")[1:])})
            if presentationLayer.Description:
                layerData.update({"LOD": presentationLayer.Description.split("_")[0]})

            layerObjects = list(ifcopenshell.util.element.get_elements_by_layer(self.ifc, presentationLayer))
            for layerObject in layerObjects:
                id = layerObject.id()
                objectLayerInformation.update({id:layerData})
        return objectLayerInformation


    def AddIfcPropertySet(self, ifcObjects, propertySetName, propertyDictionary):

        # TODO: Group properties by property set and add them together instead of one by one
        
        # Create a new property set
        propertySet = self.ifc.createIfcPropertySet()
        propertySet.Name = propertySetName

        # Add string properties to the property set
        ifcProperties = []
        for pName, pValue in propertyDictionary.items():
            prop_single_value = self.ifc.createIfcPropertySingleValue(pName, pName, self.ifc.create_entity('IfcText'))
            prop_single_value.NominalValue = self.ifc.create_entity('IfcText', pValue)
            ifcProperties.append(prop_single_value)
        propertySet.HasProperties = ifcProperties

        # Add property set to ifc file
        self.ifc.createIfcRelDefinesByProperties(
            ifcopenshell.guid.compress(uuid.uuid1().hex),
            self.ifc.by_type("IfcOwnerHistory")[0], None, None, ifcObjects, propertySet)


    def find3DObjects(self):
        ifc3DObjects = []
        for entity in self.ifc.by_type('IfcObject'):
            if hasattr(entity, 'Representation') and entity.Representation is not None:
                ifc3DObjects.append(entity)
        return ifc3DObjects


    def deletePropertySets(self, propertySetNames):
        for ifcPropertySet in self.ifc.by_type('IFCPROPERTYSET'):
            if ifcPropertySet.Name in propertySetNames:
                self.deletePropertySet(ifcPropertySet)

    def deletePropertySet(self, ifcPropertySet):
        # Delete properties in the set
        for ifcProperty in ifcPropertySet.HasProperties:
            if len(ifcProperty.PartOfPset) <= 1:
                self.ifc.remove(ifcProperty)
            else:
                ifcProperty.PartOfPset = ifcProperty.PartOfPset.remove(ifcPropertySet)
        # Delete the set
        self.ifc.remove(ifcPropertySet)



    def inject_properties(self):
        # Go through all objects adding properties
        ifcObjects = self.find3DObjects()
        print("Adding properties to "+self.ifcFileName+" with "+str(len(ifcObjects))+" objects")
        for ifcObject in ifcObjects:
            self.AddIfcPropertySet(self.ifc, [ifcObject], InjectProperties)
    
        
        self.ifc.write("output/"+self.ifcFileName)

    