#!/usr/bin/env python3

#
# (c) 2022 Robert Bosch GmbH
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#
#
# Convert vspec files to DDS-IDL
#

from email.policy import default
import sys
import vspec
import argparse

from vspec.model.vsstree import VSSNode, VSSType

def add_arguments(parser: argparse.ArgumentParser):
   parser.description="The DDS-IDL exporter"
   parser.add_argument('--all-idl-features', action='store_true',
                        help='Generate all features based on DDS IDL 4.2 specification')


idlFileBuffer = []

dataTypesMap_covesa_dds={"uint8": "octet",
              "int8": "octet",
              "uint16": "unsigned short",
              "int16": "short",
              "uint32": "unsigned long",
              "int32": "long",
              "uint64": "unsigned long long",
              "int64": "long long",
              "boolean": "boolean",
              "float": "float",
              "double": "double",
              "string": "string"
              }

def export_node( node, generate_uuid,generate_all_idl_features):
    """
    This method is used to traverse VSS node and to create corresponding DDS IDL buffer string
    """
    global idlFileBuffer
    datatype = None
    unit=None
    min=None
    max=None
    defaultValue=None
    allowedValues=None
    arraysize=None

    if node.type == VSSType.BRANCH:
        idlFileBuffer.append("module "+node.name)
        idlFileBuffer.append("{")
        for child in node.children:
            export_node( child, generate_uuid,generate_all_idl_features)
        idlFileBuffer.append("};")
        idlFileBuffer.append("");
    else:
        isEnumCreated=False
        #check if there is a need to create enum (based on the usage of allowed values)
        if node.allowed!="":
            idlFileBuffer.append("enum "+node.name+"Values{"+str(",".join(node.allowed))+"};")
            isEnumCreated=True
            idlFileBuffer.append("")
            allowedValues=str(node.allowed)

        idlFileBuffer.append("struct "+node.name)
        idlFileBuffer.append("{")
        if generate_uuid:
            idlFileBuffer.append("string uuid;")
        #fetching value of datatype and obtaining the equivalent DDS type
        try:
            if str(node.data_type.value) in dataTypesMap_covesa_dds:
                datatype= str(dataTypesMap_covesa_dds[str(node.data_type.value)])
            elif '[' in str(node.data_type.value):
                nodevalueArray=str(node.data_type.value).split("[",1)
                if str(nodevalueArray[0]) in dataTypesMap_covesa_dds :
                    datatype= str(dataTypesMap_covesa_dds[str(nodevalueArray[0])])
                    arraysize='['+str(arraysize)+nodevalueArray[1]

        except AttributeError:
            pass
        #fetching value of unit
        try:
            unit =str(node.unit.value)
        except AttributeError:
            pass

        if node.min!="":
            min=str(node.min)
        if node.max!="":
            max=str(node.max)
        if node.default != "":
            defaultValue=node.default
            if isinstance(defaultValue,str) and isEnumCreated==False:
                defaultValue="\""+defaultValue+"\""


        if datatype !=None:
            #adding range if min and max are specified in vspec file
            if min!=None and max!=None and generate_all_idl_features:
                idlFileBuffer.append("@range(min="+str(min)+" ,max="+str(max)+")")

            if allowedValues == None:
                if defaultValue==None:
                    idlFileBuffer.append(("sequence<"+datatype+"> value" if arraysize!=None else datatype+" value")+";" )
                else:
                    #default values in IDL file are not accepted by CycloneDDS/FastDDS : these values can be generated if --all-idl-features is set as True
                    idlFileBuffer.append(("sequence<"+datatype+"> value" if arraysize!=None else datatype+" value")+
                                        ("  default "+str(defaultValue) if generate_all_idl_features else "") +";")
            else:
                #this is the case where allowed values are provided, accordingly contents are converted to enum
                if defaultValue==None:
                    idlFileBuffer.append(node.name+"Values value;")
                else:
                    #default values in IDL file are not accepted by CycloneDDS/FastDDS : these values can be generated if --all-idl-features is set as True
                    idlFileBuffer.append(node.name+"Values value"+ (" "+str(defaultValue) if generate_all_idl_features else "")+";")


        if unit!=None:
            idlFileBuffer.append(("" if generate_all_idl_features else "//")+"const string unit=\""+unit +"\";")



        idlFileBuffer.append(("" if generate_all_idl_features else "//")+"const string type =\""+  str(node.type.value)+"\";")

        idlFileBuffer.append(("" if generate_all_idl_features else "//")+"const string description=\""+  node.description+"\";")
        idlFileBuffer.append("};")


def export_idl(file, root, generate_uuids=True, generate_all_idl_features=False):
    """This method is used to traverse through the root VSS node to build
       -> DDS IDL equivalent string buffer and to serialize it acccordingly into a file
    """
    export_node( root, generate_uuids,generate_all_idl_features)
    file.write('\n'.join(idlFileBuffer))
    print("IDL file generated at location : "+file.name)



def export(config: argparse.Namespace, root: VSSNode):
    print("Generating DDS-IDL output...")
    idl_out=open(config.output_file,'w')
    export_idl(idl_out, root, not config.no_uuid, config.all_idl_features)