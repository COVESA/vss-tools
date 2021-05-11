#!/usr/bin/env python3

# (C) 2021 BMW Group - All rights reserved.
# AUTHOR: Daniel Wilms BMW Group;

#
#
#
# All files and artifacts in this repository are licensed under the
# provisions of the license provided by the LICENSE file in this repository.
#

#
# Convert vspec file to TTL
#
import os
import sys
#Add path to main py vspec  parser
myDir= os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.join(myDir, "../.."))

from anytree import RenderTree, PreOrderIter

import vspec
import getopt

from model.vsstree import VSSNode, VSSType

from rdflib import Graph, Literal, RDF, URIRef, Namespace
from rdflib.namespace import RDFS, XSD, OWL, XMLNS, RDF, FOAF, SKOS, SDO, NamespaceManager
from enum import Enum

from vssotypes import VssoConcepts, DataTypes, DataUnits, Namespaces





def usage():
    print(f"""
Usage: {sys.argv[0]} [options] vspec_file ttl_file

  where [options] are:

  -I include_dir       Add include directory to search for included vspec
                       files. Can be used multiple timees.

  -i prefix:uuid_file  "prefix" is an optional string that will be
                       prepended to each signal name defined in the
                       vspec file.

                       "uuid_file" is the name of the file containing the
                       static UUID values for the signals.  This file is
                       read/write and will be updated if necessary.

                       This option can be specified several times in
                       to store the UUIDs of different parts of the
                       signal tree in different files.

  vspec_file           The vehicle specification file to parse.

  ttl_file             The file to output the ttl data to.
""")
    sys.exit(255)


def setup_graph():
    # create a Graph
    g = Graph()
    
    belongsTo = VssoConcepts.BELONGS_TO.uri
    g.add((belongsTo, RDF.type, OWL.AnnotationProperty))
    g.add((belongsTo,RDFS.label, Literal(VssoConcepts.BELONGS_TO.value,lang="en")))

    holdsValue = VssoConcepts.HOLDS_VALUE.uri
    g.add((holdsValue, RDF.type, OWL.DatatypeProperty))
    g.add((holdsValue,RDFS.subPropertyOf, OWL.topDatatypeProperty))
    g.add((holdsValue,RDFS.domain, VssoConcepts.VEHICLE_PROP.uri))
    g.add((holdsValue,RDFS.label, Literal(VssoConcepts.HOLDS_VALUE.value,lang="en")))

    partOf = VssoConcepts.PART_OF.uri
    g.add((partOf, RDF.type, OWL.ObjectProperty))
    g.add((partOf,RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((partOf,RDFS.domain, VssoConcepts.VEHICLE_COMP.uri))
    g.add((partOf,RDFS.label, Literal("partOf",lang="en")))

    hasComponentInstance = VssoConcepts.HAS_COMP_INST.uri
    g.add((hasComponentInstance, RDF.type, OWL.DatatypeProperty))
    g.add((hasComponentInstance,RDFS.subPropertyOf, OWL.topDatatypeProperty))
    g.add((hasComponentInstance,RDFS.label, Literal(VssoConcepts.HAS_COMP_INST.value,lang="en")))


    hasAttribute = VssoConcepts.HAS_ATTRIBUTE.uri
    g.add((hasAttribute, RDF.type, OWL.ObjectProperty))
    g.add((hasAttribute,RDFS.subPropertyOf, OWL.topObjectProperty))
    g.add((hasAttribute, RDFS.domain, VssoConcepts.VEHICLE.uri))
    g.add((hasAttribute, RDFS.range, VssoConcepts.VEHICLE_STAT.uri))
    g.add((hasAttribute, RDFS.label, Literal(VssoConcepts.HAS_ATTRIBUTE.value,lang="en")))


    ##
    # Classes
    ##
    vehicle = VssoConcepts.VEHICLE.uri
    g.add((vehicle, RDF.type, OWL.Class))
    g.add((vehicle, RDF.type, RDFS.Class))
    g.add((vehicle,RDFS.label, Literal(VssoConcepts.VEHICLE.value,lang="en")))


    staticVehicleProperty = VssoConcepts.VEHICLE_STAT.uri
    g.add((staticVehicleProperty, RDF.type, OWL.Class))
    g.add((staticVehicleProperty, RDF.type, RDFS.Class))
    g.add((staticVehicleProperty, RDFS.label, Literal(VssoConcepts.VEHICLE_STAT.value,lang="en")))
    
    vehicleComp = VssoConcepts.VEHICLE_COMP.uri
    g.add((vehicleComp, RDF.type, OWL.Class))
    g.add((vehicleComp, RDF.type, RDFS.Class))
    g.add((vehicleComp,RDFS.label, Literal(VssoConcepts.VEHICLE_COMP.value,lang="en")))


    vehicleProp = VssoConcepts.VEHICLE_PROP.uri
    g.add((vehicleProp, RDF.type, OWL.Class))
    g.add((vehicleProp, RDF.type, RDFS.Class))
    g.add((vehicleProp,RDFS.label, Literal(VssoConcepts.VEHICLE_PROP.value,lang="en")))


    vehicleSignal = VssoConcepts.VEHICLE_SIGNAL.uri
    g.add((vehicleSignal, RDF.type, OWL.Class))
    g.add((vehicleSignal, RDF.type, RDFS.Class))
    g.add((vehicleSignal, RDFS.subClassOf, VssoConcepts.VEHICLE_PROP.uri))
    g.add((vehicleSignal,RDFS.label, Literal(VssoConcepts.VEHICLE_SIGNAL.value,lang="en")))


    vehicleAct = VssoConcepts.VEHICLE_ACT.uri
    g.add((vehicleAct, RDF.type, OWL.Class))
    g.add((vehicleAct, RDF.type, RDFS.Class))
    g.add((vehicleAct, RDFS.subClassOf, VssoConcepts.VEHICLE_PROP.uri))
    g.add((vehicleAct,RDFS.label, Literal(VssoConcepts.VEHICLE_ACT.value,lang="en")))



    # Bind the FOAF namespace to a prefix for more readable output
    g.bind("vsso", VssoConcepts.EMPTY.uri)
    g.bind("rdfs",RDFS)
    g.bind("rdf", RDF)
    g.bind("owl", OWL)
    g.bind("skos", SKOS)
    g.bind("schema", SDO)
    g.bind("xsd", XSD)
    g.bind("qudt", URIRef(Namespaces["qudt"]))
    g.bind("cdt", URIRef(Namespaces["cdt"]))
    

    # print all the data in the Notation3 format
    print("--- printing mboxes ---")
    print(g.serialize(format='ttl').decode("utf-8"))

    return g

def setUniqueNodeName (name):
    if 'Vehicle' != name:
        return name.replace('Vehicle','').replace('.','')
    else:
        return name.replace('.','')

def setTTLName (node):
    if node.ttl_name:
        return node.ttl_name
    if node.parent and node.parent.name != "Vehicle":
        ttl_name = node.parent.name + node.name
    else:    
        ttl_name = node.name
    node.ttl_name  = ttl_name
    return ttl_name 

def print_ttl_content(file, tree):
    tree_node: VSSNode
    name_list = []
    vsso_name_list = []
    duplication = {}
    duplication_vsso = {}
    datatypes = {}
    enums = 0

    graph = setup_graph()

    for tree_node in PreOrderIter(tree):
        data_type_str = tree_node.data_type.value if tree_node.has_data_type() else ""
        unit_str = tree_node.unit.value if tree_node.has_unit() else ""
        type_str = tree_node.type.value 
        
        name = setTTLName(tree_node)
        if tree_node.name in name_list:
            print (f"** warning: {tree_node.name}" )
            print (f"** VSSO warning Replaced by: {name}" )
            if tree_node.name in duplication.keys():
                duplication [tree_node.name] += 1
            else:
                duplication [tree_node.name] = 2
        else:
            name_list.append (tree_node.name)

        extension = ''
        
        
        if name in vsso_name_list:
            print (f"** VSSO warning: {name}" )
            name = setTTLName(tree_node.parent) + tree_node.name
            print (f"** VSSO warning Replaced by: {name}" )
            
            if name in duplication_vsso.keys():
                duplication_vsso [name] += 1
            else:
                duplication_vsso [name] = 2
        else:
            vsso_name_list.append (name)

        name_space = VssoConcepts.EMPTY.uri_string
        
        
        
        node = URIRef(name_space + name)

        # not needed, in case we use classes
        # if VSSType.ATTRIBUTE == tree_node.type:
        #     node = URIRef(f"{VssoConcepts.EMPTY.uri_string}has{name}")
        
        graph.add((node, RDFS.label, Literal(name,"en")))
        graph.add((node, SKOS.altLabel, Literal(tree_node.qualified_name('.'),"en")))
        graph.add((node, RDFS.comment, Literal(tree_node.description,"en")))
        
        parent_name_space = VssoConcepts.EMPTY.uri_string
        


        # branch nodes (incl. instance handling)
        if VSSType.BRANCH == tree_node.type:
            if tree_node.parent:
                graph.add((node, RDF.type, VssoConcepts.VEHICLE_COMP.uri))
                graph.add((node, VssoConcepts.PART_OF.uri, URIRef(parent_name_space + setTTLName(tree_node.parent))))
            # if tree_node.instances:
            #     print (instances)
        # leafs (incl. restrictions)
        else: 
            graph.add((node, VssoConcepts.BELONGS_TO.uri, URIRef(parent_name_space + setTTLName(tree_node.parent))))

            if tree_node.has_data_type() and tree_node.data_type.value in DataTypes.keys():
                graph.add((node, SDO.rangeIncludes, DataTypes[tree_node.data_type.value]))

            if tree_node.has_unit() and tree_node.unit.value in DataUnits.keys():
                graph.add((node, SDO.rangeIncludes, DataUnits[tree_node.unit.value]))


            if VSSType.ATTRIBUTE == tree_node.type:
                #graph.add((node, RDF.type, OWL.DatatypeProperty))
                graph.add((node, RDF.type, OWL.Class))
                graph.add((node, RDF.type, RDFS.Class))
                graph.add((node, RDFS.subClassOf, VssoConcepts.VEHICLE_STAT.uri))
                
            else:

                if (tree_node.data_type in datatypes.keys()):
                    datatypes[tree_node.data_type] += 1
                else:
                    datatypes[tree_node.data_type] = 1

                graph.add((node, RDF.type, OWL.Class))
                graph.add((node, RDF.type, RDFS.Class))
                graph.add((node, RDFS.subClassOf, VssoConcepts.VEHICLE_SIGNAL.uri))

                if VSSType.ACTUATOR == tree_node.type:
                    graph.add((node, RDFS.subClassOf, VssoConcepts.VEHICLE_ACT.uri))

            if (tree_node.enum):
                enums += 1


    file.write(graph.serialize(format='ttl').decode("utf-8"))

    print (duplication)
    print (duplication_vsso)
    print (datatypes)
    print (enums)



if __name__ == "__main__":
    #
    # Check that we have the correct arguments
    #
    opts, args = getopt.getopt(sys.argv[1:], "I:i:")

    # Always search current directory for include_file
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        elif o == "-i":
            id_spec = a.split(":")
            if len(id_spec) != 2:
                print("ERROR: -i needs a 'prefix:id_file' argument.")
                usage()

            [prefix, file_name] = id_spec
            vspec.db_mgr.create_signal_uuid_db(prefix, file_name)
        else:
            usage()

    if len(args) != 2:
        usage()

    try:
        tree = vspec.load_tree(args[0], include_dirs, False)
        ttl_out = open(args[1], "w")
        print_ttl_content(ttl_out, tree)
        ttl_out.write("\n")
        ttl_out.close()
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        exit(255)
