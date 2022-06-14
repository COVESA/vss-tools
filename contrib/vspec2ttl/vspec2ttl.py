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

from anytree import PreOrderIter

import vspec
import getopt

from vspec.model.vsstree import VSSNode, VSSType

from rdflib import Graph, Literal, RDF, URIRef, BNode
from rdflib.namespace import RDFS, OWL, RDF,  SKOS
from enum import Enum


# There are two options of handling branches:
# 1. branches are handled as _subclasses_ of vehicle components
# 2. branches are handled as _instances_ of vehicle components
#
# As it's not decided for now, we can generate both by setting this
# variable to True or False. True means that branches are handled as
# subclasses of vehicle components. False means that branches are handled
# as instances of vehicle components.

COMPONENTS_AS_CLASSES = False

class VssoCoreConcepts (Enum):
###
# Class to define the concepts and their names for later references
###
    EMPTY =             ""
    BELONGS_TO =        "belongsToVehicleComponent"
    HOLDS_VALUE =       "vehiclePropertyValue"
    HAS_SIGNAL =        "hasDynamicVehicleProperty"
    HAS_ATTRIBUTE =     "hasStaticVehicleProperty"
    PART_OF_VEHICLE =   "partOfVehicle"
    PART_OF_VEH_COMP =  "partOf"
    HAS_COMP_INST =     "postionedAt"
    VSS_CLASSIFICATION ="vssFacetedClassification"
    VEHICLE =           "Vehicle"
    VEHICLE_SIGNAL =    "ObservableVehicleProperty"
    VEHICLE_ACT =       "ActuatableVehicleProperty"
    VEHICLE_COMP =      "VehicleComponent"
    VEHICLE_PROP =      "DynamicVehicleProperty"
    VEHICLE_STAT =      "StaticVehicleProperty"
    

    def __init__ (self, vsso_name):
        self.ns = "https://github.com/w3c/vsso-core#"
        self.vsso_name = vsso_name

    @property
    def uri(self):
        return URIRef(f'{self.ns}{self.value}')

    @property
    def uri_string(self):
        return f'{self.ns}{self.value}'


def setup_graph():
    ###
    # function to define the metadata of VSSo,
    # to define the used prefixes and namespaces,
    # and to crete the basic rdflib graph
    ###

    g = Graph()

    ontology_description_ttl = """
        @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
        @prefix owl: <http://www.w3.org/2002/07/owl#> .
        @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
        @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
        @prefix dcterms: <http://purl.org/dc/terms/> .
        @prefix vann: <http://purl.org/vocab/vann/> .
        @prefix vsso-core: <https://github.com/w3c/vsso-core#> .
        @prefix vsso: <https://github.com/w3c/vsso#> .
        @prefix skos: <http://www.w3.org/2004/02/skos/core#> .


        vsso: rdf:type owl:Ontology ;
            dcterms:title "VSSo: Vehicle Signal Specification Ontology";
            vann:preferredNamespaceUri "https://github.com/w3c/vsso#" ;
            dcterms:description "This ontology describes the car's attributes, branches and signals defined in the Vehicle Signal Specification." ;
            dcterms:license <http://creativecommons.org/licenses/by/4.0/> ;
            dcterms:creator "Benjamin Klotz"^^xsd:string ;
            dcterms:creator "Raphael Troncy"^^xsd:string ;
            dcterms:creator "Daniel Wilms"^^xsd:string;
            dcterms:contributor "Daniel Alvarez-Coello"^^xsd:string ;
            dcterms:contributor "Felix Loesch"^^xsd:string ;
            owl:versionInfo "v2.2"@en ;
            rdfs:seeAlso "https://github.com/COVESA/vehicle_signal_specification";
            vann:preferredNamespacePrefix "vsso";
            dcterms:abstract \"\"\"
            As the core ontology defined the structure, VSSo holds the vocabulary as defined by the standard catalogue.
            The main objective is, that VSSo doesn't diverege from the standard catalogue, so this is done automatically
            through tooling provided in the corresponding repository. The tooling takes the standard catalogue and maps it to
            concepts defined in the core ontology. The result is an OWL complient ontology, following the standard catalogue of VSS.
            \"\"\"@en .
        """

    g.parse(data=ontology_description_ttl, format="turtle")
    
    return g

def setTTLName (node):
    ###
    # function to set a unique name of a node
    # which is used in the ontology. Sets a combined name of
    # the node and its parent, if the parent is not `vehicle`.
    ###
    if node.ttl_name:
        return node.ttl_name
    if node.parent and node.parent.name != "Vehicle":
        ttl_name = node.parent.name + node.name
    else:    
        ttl_name = node.name
    node.ttl_name  = ttl_name
    return ttl_name 

def print_ttl_content(file, tree):
    ###
    # function to create & print the content of the ontology
    # in turtle format.
    ###

    tree_node: VSSNode
    name_list = []
    vsso_name_list = []
    duplication = {}
    duplication_vsso = {}
    datatypes = {}
    namespace = "https://github.com/w3c/vsso#"


    graph = setup_graph()

    for tree_node in PreOrderIter(tree): #< iterate over the tree in preorder
        # start with setting the unique name of the node
        name = setTTLName(tree_node)

        # check if the original name is already used
        # and store for later analysis
        if tree_node.name in name_list:
            if tree_node.name in duplication.keys():
                duplication [tree_node.name] += 1
            else:
                duplication [tree_node.name] = 2
        else:
            name_list.append (tree_node.name)

        # check if combined name is unique, otherwise
        # use the parents unique name and combine with the node name
        if name in vsso_name_list:
            name = setTTLName(tree_node.parent) + tree_node.name
            
            if name in duplication_vsso.keys():
                duplication_vsso [name] += 1
            else:
                duplication_vsso [name] = 2
        else:
            vsso_name_list.append (name)

        # set the URI for the node  
        node = URIRef(namespace + name)

        # basic metadata, independent of node type
        graph.add((node, RDFS.label, Literal(name,"en")))
        graph.add((node, VssoCoreConcepts.VSS_CLASSIFICATION.uri, Literal(tree_node.qualified_name('.'),"en")))
        graph.add((node, SKOS.definition, Literal(tree_node.description,"en")))

        # if a comment is set in the VSS node add the comment to the ontology
        if tree_node.comment:
            graph.add((node, RDFS.comment, Literal(tree_node.comment,"en")))
        
        # branch nodes as vsso:VehicleComponent subclasses if variable is set accordingly
        if VSSType.BRANCH == tree_node.type and COMPONENTS_AS_CLASSES:
            if tree_node.parent:
                graph.add((node, RDF.type, OWL.Class))
                graph.add((node, RDFS.subClassOf, VssoCoreConcepts.VEHICLE_COMP.uri))

                b = BNode()
                graph.add((b, RDF.type, OWL.Restriction))
                graph.add((b, OWL.onProperty, VssoCoreConcepts.PART_OF_VEH_COMP.uri))
                if "Vehicle" == setTTLName(tree_node.parent):
                    graph.add((b, OWL.allValuesFrom, VssoCoreConcepts.VEHICLE.uri))
                else:
                    graph.add((b, OWL.allValuesFrom, URIRef(namespace + setTTLName(tree_node.parent))))

                graph.add((node, RDFS.subClassOf, b))
                print( [x.name if x.type != VSSType.BRANCH else None for x in tree_node.children])
        # branch nodes as vsso:VehicleComponent instances if variable is set accordingly
        elif VSSType.BRANCH == tree_node.type and not COMPONENTS_AS_CLASSES:
            graph.add ((node, RDF.type, VssoCoreConcepts.VEHICLE_COMP.uri))
            if tree_node.parent:
                graph.add((node, VssoCoreConcepts.PART_OF_VEH_COMP.uri, URIRef(namespace + setTTLName(tree_node.parent))))
            
                
        # attributes, sensors & actuators
        else:             
            if VSSType.ATTRIBUTE == tree_node.type:
                graph.add((node, RDF.type, OWL.Class))
                graph.add((node, RDFS.subClassOf, VssoCoreConcepts.VEHICLE_STAT.uri))
                if COMPONENTS_AS_CLASSES:
                    b = BNode()
                    graph.add((b, RDF.type, OWL.Restriction))
                    graph.add((b, OWL.onProperty, VssoCoreConcepts.BELONGS_TO.uri))
                    if "Vehicle" == setTTLName(tree_node.parent):
                        graph.add((b, OWL.allValuesFrom, VssoCoreConcepts.VEHICLE.uri))
                    else:
                        graph.add((b, OWL.allValuesFrom, URIRef(namespace + setTTLName(tree_node.parent))))

                    graph.add((node, RDFS.subClassOf, b))
                
            else: # < vss actuators & sensors 
                # check different datatypes in use
                if (tree_node.data_type in datatypes.keys()):
                    datatypes[tree_node.data_type] += 1
                else:
                    datatypes[tree_node.data_type] = 1

                graph.add((node, RDF.type, VssoCoreConcepts.VEHICLE_SIGNAL.uri))
                graph.add((node, VssoCoreConcepts.BELONGS_TO.uri, URIRef(namespace + setTTLName(tree_node.parent))))
                
                if VSSType.ACTUATOR == tree_node.type:
                    graph.add((node, RDF.type, VssoCoreConcepts.VEHICLE_ACT.uri))

    # write the file and print the metadata.
    file.write(graph.serialize(format='ttl'))
    for ns, url in graph.namespaces():
        print(f"@prefix {ns}: <{url}>")
    print (duplication)
    print (duplication_vsso)
    print (datatypes)

def usage():
    print(f"""
Usage: {sys.argv[0]} [options] vspec_file ttl_file

  where [options] are:

  -I include_dir       Add include directory to search for included vspec
                       files. Can be used multiple timees.

  vspec_file           The vehicle specification file to parse.

  ttl_file             The file to output the ttl data to.
""")
    sys.exit(255)

if __name__ == "__main__":
    #
    # Check that we have the correct arguments
    #
    opts, args = getopt.getopt(sys.argv[1:], "I:")

    # Always search current directory for include_file
    include_dirs = ["."]
    for o, a in opts:
        if o == "-I":
            include_dirs.append(a)
        else:
            usage()

    if len(args) != 2:
        usage()

    try:
        tree = vspec.load_tree(args[0], include_dirs, False, expand_inst=False)
        ttl_out = open(args[1], "w")
        print_ttl_content(ttl_out, tree)
        ttl_out.write("\n")
        ttl_out.close()
    except vspec.VSpecError as e:
        print(f"Error: {e}")
        exit(255)
