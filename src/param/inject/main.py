import ifcopenshell
import uuid
import os
import json


streetPropertySetBanlist = [
    '[Generic].[Graphic3d]',
    'Feature',
    'QTO_DimensionsAspect',
    'QTO_MaterialAspect',
    'QTO_SideAreasAspect',
    'QTO_SurfaceAreaAspect',
    'QTO_VolumeAspect',
    'QTO_DimensionsAspect',
]


def GetObjectLayerInformation(ifcFile):
    objectLayerInformation = {}
    for presentationLayer in ifcFile.by_type('IFCPRESENTATIONLAYERASSIGNMENT'):
        layerData = {}
        layerData.update({"Number": presentationLayer.Name.split("_")[0]})
        layerData.update({"Name": "_".join(presentationLayer.Name.split("_")[1:])})
        if presentationLayer.Description:
            layerData.update({"LOD": presentationLayer.Description.split("_")[0]})

        layerObjects = list(ifcopenshell.util.element.get_elements_by_layer(ifcFile, presentationLayer))
        for layerObject in layerObjects:
            id = layerObject.id()
            objectLayerInformation.update({id:layerData})
    return objectLayerInformation


def AssembleProjectProperties(ifcFile, ifcFileName, ifcObject, projectAttributesJson, objectLayerInformation):
    Discipline = ifcFileName[6:9]

    # Load default attributes from json file
    projectAttributes = projectAttributesJson[Discipline]

    # Set file dependent properties
    projectAttributes["Dags"] = ifcFile.wrapped_data.header.file_name.time_stamp[:10]
    projectAttributes["Verksvaedi"] = ifcFileName[2:5]
    
    # Set layer dependent properties
    if Discipline == "ULA":
        info = objectLayerInformation[ifcObject.id()]
        projectAttributes["LOD"] = info["LOD"]
    
    return projectAttributes


def AssembleDisciplineProperties(ifcFile, ifcFileName, ifcObject, disciplineAttributesJson, objectLayerInformation):
    Discipline = ifcFileName[6:9]
    Section = ifcFileName[2:5]

    # Load default attributes from json file
    if Discipline == "STR":
        disciplineAttributes = disciplineAttributesJson[Discipline][Section]
    elif Discipline == "ULA":
        disciplineAttributes = disciplineAttributesJson[Discipline]
    
    # Set layer dependent properties
    disciplineAttributes["Verkþáttur"] = objectLayerInformation[ifcObject.id()]["Number"]
    disciplineAttributes["Verkþáttarheiti"] = objectLayerInformation[ifcObject.id()]["Name"]
    if Discipline == "STR":
        disciplineAttributes["Nafn byggingarhluta"] = objectLayerInformation[ifcObject.id()]["Name"]
    
    return disciplineAttributes


def AddIfcPropertySet(ifcFile, ifcObjects, propertySetName, propertyDictionary):
    
    # Create a new property set
    propertySet = ifcFile.createIfcPropertySet()
    propertySet.Name = propertySetName

    # Add string properties to the property set
    ifcProperties = []
    for pName, pValue in propertyDictionary.items():
        prop_single_value = ifcFile.createIfcPropertySingleValue(pName, pName, ifcFile.create_entity('IfcText'))
        prop_single_value.NominalValue = ifcFile.create_entity('IfcText', pValue)
        ifcProperties.append(prop_single_value)
    propertySet.HasProperties = ifcProperties

    # Add property set to ifc file
    ifcFile.createIfcRelDefinesByProperties(
        ifcopenshell.guid.compress(uuid.uuid1().hex),
        ifcFile.by_type("IfcOwnerHistory")[0], None, None, ifcObjects, propertySet)


def find3DObjects(ifcFile):
    ifc3DObjects = []
    for entity in ifcFile.by_type('IfcObject'):
        if hasattr(entity, 'Representation') and entity.Representation is not None:
            ifc3DObjects.append(entity)
    return ifc3DObjects


def deletePropertySets(ifcFile, propertySetNames):
    for ifcPropertySet in ifcFile.by_type('IFCPROPERTYSET'):
        if ifcPropertySet.Name in propertySetNames:
            deletePropertySet(ifcFile, ifcPropertySet)

def deletePropertySet(ifcFile, ifcPropertySet):
    # Delete properties in the set
    for ifcProperty in ifcPropertySet.HasProperties:
        if len(ifcProperty.PartOfPset) <= 1:
            ifcFile.remove(ifcProperty)
        else:
            ifcProperty.PartOfPset = ifcProperty.PartOfPset.remove(ifcPropertySet)
    # Delete the set
    ifcFile.remove(ifcPropertySet)

def RenamePropertySet(ifcFile, mappingDict, copy = True):
    mappingPropertySets = mappingDict["PropertySets"].keys()
    mappingProperties = mappingDict["Properties"].keys()
    mappingValues = mappingDict["Values"].keys()

    for propertySet in mappingPropertySets:
        for ifcPropertySet in ifcFile.by_type('IFCPROPERTYSET'):
            if ifcPropertySet.Name == propertySet:
                
                # Assemble the properties dictionary with translated names and model values
                propertyDictionary = {}
                for ifcProperty in ifcPropertySet.HasProperties:
                    if ifcProperty.Name in mappingProperties:
                        name = mappingDict["Properties"][ifcProperty.Name]
                        value = ifcProperty.NominalValue.wrappedValue
                        if value in mappingValues:
                            value = mappingDict["Values"][value]
                        propertyDictionary[name] = value

                # Find the related objects
                ifcObjects = list(ifcPropertySet.PropertyDefinitionOf[0].RelatedObjects)

                # Add now property set
                AddIfcPropertySet(ifcFile, ifcObjects, mappingDict["PropertySets"][propertySet], propertyDictionary)
                if not copy:
                    deletePropertySet(ifcFile, ifcPropertySet)



def PostProcess(ifcFileName):
    ifcFile = ifcopenshell.open("input/"+ifcFileName)
    Discipline = ifcFileName[6:9]
        
    # Load all properties data
    objectLayerInformation = GetObjectLayerInformation(ifcFile)
    
    f = open('ProjectAttributes.json', encoding='utf-8')
    projectAttributesJson = json.load(f)
    f.close()

    # Load attribute mapping
    f = open('PropertySetRenameMapping.json', encoding='utf-8')
    pSetMapping = json.load(f)
    f.close()
    
    #f = open('DisciplineAttributes.json', encoding='utf-8')
    #disciplineAttributesJson = json.load(f)
    #f.close()

    # Go through all objects adding properties
    ifcObjects = find3DObjects(ifcFile)
    print("Adding properties to "+ifcFileName)
    for ifcObject in ifcObjects:
        
        if Discipline in ["ULA", "STR", "CON"]:
            projectProperties = AssembleProjectProperties(ifcFile, ifcFileName, ifcObject, projectAttributesJson, objectLayerInformation)
            AddIfcPropertySet(ifcFile, [ifcObject], "Verkupplýsingar", projectProperties)
        elif Discipline in ["UTI", "PWR"]:
            RenamePropertySet(ifcFile, pSetMapping[Discipline])
        
        #disciplineProperties = getDisciplineProperties(ifcFile, ifcFileName, ifcObject, disciplineAttributesJson, objectLayerInformation)
        #AddIfcPropertySet(ifcFile, [ifcObject], "Fagupplýsingar", disciplineProperties)
    
    if Discipline == "STR":
        print("Cleaning up property sets in "+ifcFileName)
        deletePropertySets(ifcFile, streetPropertySetBanlist)
    
    ifcFile.write("output/"+ifcFileName)



if __name__ == "__main__":
    inputFiles = os.listdir("input/")
    for ifcFileName in inputFiles:
        PostProcess(ifcFileName)
    print("Done")
    