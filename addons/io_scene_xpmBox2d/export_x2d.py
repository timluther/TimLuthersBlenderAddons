# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>
# x2d export - based on obj exporter included with Blender

import os
import time
import struct
import bpy
import mathutils
import bpy_extras.io_utils
import math
from . import binaryFileBuilder


def writePosition(fw, position):
    fw("Position ")
    fw(str(position.x))
    fw(" ")
    fw(str(position.y))

def writeVerts(fw, collisionObject):
    verts = collisionObject.data.vertices
    for vert in verts:
        fw("\n\tVert " + str(vert.co.x) + " " + str(vert.co.y))

def writeEdges(fw, collisionObject):
    edges = collisionObject.data.edges
    for edge in edges:
        fw("\n\tEdge " + str(edge.vertices[0]) + " " + str(edge.vertices[1]))
        

def getEdges(collisionObject):
    edges = collisionObject.data.edges
    edge_list = list()
    for edge in edges:
        edge_list.append((edge.vertices[0], edge.vertices[1]))

    return edge_list

def getVerts(collisionObject):
    verts = collisionObject.data.vertices
    vert_list = list()
    mat = collisionObject.matrix_world
    print(mat)
    for vert in verts:
        tv = mat * vert.co
        vert_list.append((tv.x, tv.y, tv.z))

    return vert_list

def writeCircle(fw, collisionObject, objectCounter):
    inFileID = collisionObject.name.replace("Circle","",1)
    if inFileID == "":
        inFileID = str(objectCounter)
    fw("CIRCLE")    
    fw("\n\tID " + inFileID)    
    fw("\n\t")
    writePosition(fw, collisionObject.location)   
    fw("\n\tRadius ")
    radius = collisionObject.scale.x
    radius *= collisionObject.data.vertices[0].co.y
    fw(str(abs(radius)))
    fw("\n")

def writeBox(fw, collisionObject, objectCounter):
    inFileID = collisionObject.name.replace("Box","",1)
    if inFileID == "":
        inFileID = str(objectCounter)
    fw("BOX")
    fw("\n\tID " + inFileID)
    fw("\n\t")
    writePosition(fw, collisionObject.location)
    fw("\n\tWidth ")
    fw(str(abs(collisionObject.scale.x)))
    fw("\n\tHeight ")
    fw(str(abs(collisionObject.scale.y)))
    fw("\n")

def writePoly(fw, collisionObject, objectCounter):
    inFileID = collisionObject.name.replace("Poly","",1)
    if inFileID == "":
        inFileID = str(objectCounter)
    fw("POLY")
    fw("\n\tID " + inFileID)
    fw("\n\t")
    writePosition(fw, collisionObject.location)
    #writeVerts(fw, collisionObject)
    #writeEdges(fw, collisionObject)
    edges = getEdges(collisionObject)
    verts = getVerts(collisionObject)

    sorted_verts = list()
    working_edge = edges.pop(0)
    start_vert = working_edge[0]
    search_vert = working_edge[1]
    found_vert = working_edge[0]

    #Create a list of sorted vertices
    while start_vert != search_vert:        
        sorted_verts.append(verts[found_vert])  #Write the found_vert
        for edge in edges:  #Search edges for the search_vert
            if search_vert == edge[0]:
                found_vert = edge[0]
                search_vert = edge[1]
                edges.remove(edge)
                break
            elif search_vert == edge[1]:
                found_vert = edge[1]
                search_vert = edge[0]
                edges.remove(edge)
                break

    sorted_verts.append(verts[found_vert])
  
    #Check the winding on the verts
    northMost = 0
    eastMost = 0
    southMost = 0
    westMost = 0

    index = 0
    while index < len(sorted_verts):
        if sorted_verts[index][1] > sorted_verts[northMost][1]:
            northMost = index
        if sorted_verts[index][1] < sorted_verts[southMost][1]:
            southMost = index
        if sorted_verts[index][0] > sorted_verts[eastMost][0]:
            eastMost = index
        if sorted_verts[index][0] < sorted_verts[westMost][0]:
            westMost = index

        index += 1

    #Check the plygon winding
    vec_one = (sorted_verts[0][0] - sorted_verts[1][0], sorted_verts[0][1] - sorted_verts[1][1])
    vec_two = (sorted_verts[1][0] - sorted_verts[2][0], sorted_verts[1][1] - sorted_verts[2][1])

    cross_product = vec_one[0]*vec_two[1] - vec_one[1]*vec_two[0]

    print("Cross product of two vectors is %f" % cross_product)
    if cross_product < 0:
        print("Reversing poly")
        sorted_verts.reverse()

    #Write the vertices to the file
    for vert in sorted_verts:

        vertx = vert[0] * collisionObject.scale.x
        verty = vert[1] * collisionObject.scale.y
        vertz = vert[2];# * collisionObject.scale.y
        print(str(vertx) + ", " + str(verty) + "\n")
        #fw("\n\tVert %f %f" % (vertx, verty))
        fw("\n\tVert %f %f %f" % (vertx, verty, vertz))

    print("Wrote vertices")
    index = 0
    for vert in sorted_verts:
        fw("\n\tEdge " + str(index) + " ")
        index += 1        
        fw(str(index%len(sorted_verts)))

    fw("\n")


def testFunction(context, filepath):
    print("Finding the collision group")
    groups = bpy.data.groups
    collisionGroup = 0

    '''Find a collision group'''
    for group in groups:
        if group.name == "CollisionGroup":
            collisionGroup = group

    '''Exit if no collision group has been found'''
    if collisionGroup == 0:
        print("Failed to find collision group!")
        return 'None'

    '''Open a file to write to'''
    file = open(filepath, "w", encoding="utf8", newline="\n")
    fw = file.write
    objectCounter = 0
    for collisionObject in collisionGroup.objects:
        '''Write Circle Objects'''
        if collisionObject.name.find("Circle") == 0:
            writeCircle(fw, collisionObject, objectCounter)

        '''Write Box Objects '''
        if collisionObject.name.find("Box") == 0:
            writeBox(fw, collisionObject, objectCounter)
            
        if collisionObject.name.find("Poly") == 0:
            writePoly(fw, collisionObject, objectCounter)

        objectCounter = objectCounter + 1
    fw('END')
    file.close()


def save(operator, context, filepath="",
         use_triangles=False,
         use_edges=True,
         use_normals=False,
         use_uvs=True,
         use_materials=True,
         use_apply_modifiers=True,
         use_blen_objects=True,
         group_by_object=False,
         group_by_material=False,
         keep_vertex_order=False,
         use_vertex_groups=False,
         use_nurbs=True,
         use_selection=True,
         use_animation=False,
         global_matrix=None,
         path_mode='AUTO'
         ):

    '''
    _write(context, filepath,
           EXPORT_TRI=use_triangles,
           EXPORT_EDGES=use_edges,
           EXPORT_NORMALS=use_normals,
           EXPORT_UV=use_uvs,
           EXPORT_MTL=use_materials,
           EXPORT_APPLY_MODIFIERS=use_apply_modifiers,
           EXPORT_BLEN_OBS=use_blen_objects,
           EXPORT_GROUP_BY_OB=group_by_object,
           EXPORT_GROUP_BY_MAT=group_by_material,
           EXPORT_KEEP_VERT_ORDER=keep_vertex_order,
           EXPORT_POLYGROUPS=use_vertex_groups,
           EXPORT_CURVE_AS_NURBS=use_nurbs,
           EXPORT_SEL_ONLY=use_selection,
           EXPORT_ANIMATION=use_animation,
           EXPORT_GLOBAL_MATRIX=global_matrix,
           EXPORT_PATH_MODE=path_mode,
           )
    '''
    testFunction(context, filepath)

    binaryFileBuilder.readWriteFile(filepath)

    return {'FINISHED'}
