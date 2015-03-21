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

# Script copyright (C) Campbell Barton
# Contributors: Campbell Barton, Jiri Hnidek, Paolo Ciccone

"""
This script imports a Wavefront OBJ files to Blender.

Usage:
Run this script from "File->Import" menu and then load the desired OBJ file.
Note, This loads mesh objects and materials only, nurbs and curves are not supported.

http://wiki.blender.org/index.php/Scripts/Manual/Import/wavefront_obj
"""

import os
import time
import bpy
import mathutils
import math
from bpy_extras.io_utils import unpack_list, unpack_face_list
from bpy_extras.image_utils import load_image

def checkLine(line):
    if line.find("CIRCLE") == 0:
        return True
    if line.find("BOX") == 0:
        return True
    if line.find("POLY") == 0:
        return True
    if line == "":
        return True

    return False

def getNames():
    names = []
    for i in bpy.data.objects:
        names.append(i.name)

    return names

def readPoly(inputFile):
    position = [0.0,0.0]
    ID = "POLY"
    verts = []
    edges = []

    while True:
        oldPos = inputFile.tell()
        line = inputFile.readline()
        if checkLine(line):
            inputFile.seek(oldPos)
            break

        split = line.split()
        if split[0] == "ID":
            ID += split[1]
        if split[0] == "Position":
            position[0] = float(split[1])
            position[1] = float(split[2])
        if split[0] == "Vert":
            vert = (float(split[1]), float(split[2]), 0)
            verts.append(vert)
        if split[0] == "Edge":
            edge = (int(split[1]), int(split[2]))
            edges.append(edge)
        
    print("Loaded in a Polygon")
    print("\tID = " + ID)
    print("\tPosition = " + str(position))
    for vert in verts:
        print("\tVert = " + str(vert))
    for edge in edges:
        print("\tEdge = " + str(edge))
        

    mesh = bpy.data.meshes.new("PolyMesh")
    mesh.from_pydata(verts,edges,[])

    scene = bpy.context.scene
    obj = bpy.data.objects.new(ID, mesh)
    obj.name = ID
    obj.location.x = position[0]
    obj.location.y = position[1]
    scene.objects.link(obj)


def readCircle(inputFile):
    radius = 1.0
    position = [0.0, 0.0]
    ID = "Circle"

    for x in range(0,300):
        oldPos = inputFile.tell()
        line = inputFile.readline()
        if checkLine(line):
            inputFile.seek(oldPos)
            break

        split = line.split()
        if split[0] == "ID":
            ID += split[1]
        if split[0] == "Position":
            position[0] = float(split[1])
            position[1] = float(split[2])
        if split[0] == "Radius":
            radius = float(split[1])

    print("Loaded in Circle:")
    print("\tID = " + ID)
    print("\tRadius = " + str(radius))
    print("\tPosition = " + str(position))

    verts = []
    edges = []
    resolution = 32
    for i in range(0,resolution):
        theta = (i / resolution)*math.pi*2  #Get theta in radians
        verts.append((1.0 * math.sin(theta), 1.0 * math.cos(theta), 0.0))
        next = i+1
        if next >= resolution:
            next = 0
        edges.append((i, next))

    mesh = bpy.data.meshes.new("CircleMesh")
    mesh.from_pydata(verts,edges,[])

    obj = bpy.data.objects.new(ID, mesh)
    obj.name = ID
    obj.location.x = position[0]
    obj.location.y = position[1]
    obj.scale.x = radius
    obj.scale.y = radius
    bpy.context.scene.objects.link(obj)

    '''
    names = getNames()

    for name in names:
        print(name)

    bpy.ops.mesh.primitive_circle_add(radius=radius*2, location=(position[0], position[1], 0))
    
    count = 0
    for obj in bpy.data.objects:
        if names[count] != obj.name:
            thisCircle = obj
            break
    print("Setting values on object currently known as " + thisCircle.name)
    thisCircle.name = ID
    '''

def readBox(inputFile):
    width = 0.0
    height = 0.0
    position = [0.0,0.0]
    ID = "Box"

    for x in range(0,4):
        line = inputFile.readline()
        split = line.split()
        if split[0] == "ID":
            ID += split[1]
        if split[0] == "Position":
            position[0] = float(split[1])
            position[1] = float(split[2])
        if split[0] == "Width":
            width = float(split[1])
        if split[0] == "Height":
            height = float(split[1])

    print("Loaded in a Box")
    print("\tID = " + ID)
    print("\tPosition = " + str(position))
    print("\tWidth = " + str(width))
    print("\tHeight = " + str(height))

    verts = [(1.0,1.0,0.0),(1.0,-1.0,0.0),(-1.0,-1.0,0.0),(-1.0,1.0,0.0)]
    edges = [(0,1),(1,2),(2,3),(3,0)]

    mesh = bpy.data.meshes.new("CircleMesh")
    mesh.from_pydata(verts,edges,[])

    obj = bpy.data.objects.new(ID, mesh)
    obj.name = ID
    obj.location.x = position[0]
    obj.location.y = position[1]
    obj.scale.x = width
    obj.scale.y = height
    bpy.context.scene.objects.link(obj)
    

def load(operator, context, filepath,
         global_clamp_size=0.0,
         use_ngons=True,
         use_smooth_groups=True,
         use_edges=True,
         use_split_objects=True,
         use_split_groups=True,
         use_image_search=True,
         use_groups_as_vgroups=False,
         global_matrix=None,
         ):
    '''
    Called by the user interface or another script.
    load_obj(path) - should give acceptable results.
    This function passes the file and sends the data off
        to be split into objects and then converted into mesh objects
    '''
    filepath = os.fsencode(filepath)

    print("Parsing file...")
    inputFile = open(filepath, 'r')
    
    while True:
        line = inputFile.readline()
        if line == "":
            print("Reached the end of the file...")
            break
        
        if line.find("POLY") == 0:
            readPoly(inputFile)
        if line.find("CIRCLE") == 0:
            readCircle(inputFile)
        if line.find("BOX") == 0:
            readBox(inputFile)

    return {'FINISHED'}
# NOTES (all line numbers refer to 2.4x import_obj.py, not this file)
# check later: line 489
# can convert now: edge flags, edges: lines 508-528
# ngon (uses python module BPyMesh): 384-414
# NEXT clamp size: get bound box with RNA
# get back to l 140 (here)
# search image in bpy.config.textureDir - load_image
# replaced BPyImage.comprehensiveImageLoad with a simplified version that only checks additional directory specified, but doesn't search dirs recursively (obj_image_load)
# bitmask won't work? - 132
# uses bpy.sys.time()
