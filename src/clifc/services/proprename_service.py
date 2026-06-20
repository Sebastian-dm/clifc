import ifcopenshell
import ifcopenshell.util.element
import uuid
from ifcopenshell.file import file as IfcFile

mappingDict = {
  "UTI": {
    "PropertySets" : {
      "FAGLIKAN_ALMENNT" : "Verkupplýsingar"
    },
    "Properties" :  {
      "VERKHEITI": "Verkheiti",
      "VERKNR": "Verknumer",
      "DAGSINNSETNINGAR": "Dags",
      "FM_INN": "Hönnudur",
      "LOD": "LOD",
      "VERKSVAEDI": "Verksvaedi",
      "VERKFASI": "Verkfasi"
    },
    "Values" : {
      "Forhönnun" : "PD"
    }
  },
  "PWR": {
    "PropertySets" : {
      "FAGLIKAN_ALMENNT" : "Verkupplýsingar"
    },
    "Properties" :  {
      "VERKHEITI": "Verkheiti",
      "VERKNR": "Verknumer",
      "DAGSINNSETNINGAR": "Dags",
      "FM_INN": "Hönnudur",
      "LOD": "LOD",
      "VERKSVAEDI": "Verksvaedi",
      "VERKFASI": "Verkfasi"
    },
    "Values" : {
      "Forhönnun" : "PD"
    }
  }
}


class RenameService:

    def __init__(self, input_file):
        self.ifc = ifcopenshell.open(input_file)
        if not isinstance(self.ifc, IfcFile):
            raise TypeError("Expected an IFC file model")
    

    def RenamePropertySet(self, mappingDict, copy = True):
        for ifcPropertySet in self.ifc.by_type('IFCPROPERTYSET'):
            for propertySet in mappingDict.keys():
                if ifcPropertySet.Name == propertySet:
                    ifcPropertySet.Name = mappingDict[propertySet]


    def renameProperties(self, mappingDict, copy = True):
        mappingPropertySets = mappingDict["PropertySets"].keys()
        mappingProperties = mappingDict["Properties"].keys()
        mappingValues = mappingDict["Values"].keys()

        for propertySet in mappingPropertySets:
            for ifcPropertySet in self.ifc.by_type('IFCPROPERTYSET'):
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
                    self.AddIfcPropertySet(ifcObjects, mappingDict["PropertySets"][propertySet], propertyDictionary)
                    if not copy:
                        self.deletePropertySet(ifcPropertySet)

    def AddIfcPropertySet(self, ifcObjects, propertySetName, propertyDictionary):
        
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