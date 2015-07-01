import bpy
from bpy_types import *
from bpy_extras import *
from mathutils import *
import bmesh
import sys
import os

def removeimage(img):
	imgobj = bpy.data.images[img]
	imgobj.user_clear()
	bpy.data.images.remove(imgobj)

def removematerial(mat):
	matobj = bpy.data.materials[mat]
	matobj.user_clear()
	bpy.data.materials.remove(matobj)


def findduplicateimages():
	for i in bpy.data.images:
		if ".0" in i.name:
			print(i.name)

def removeduplicateimages():
	for i in bpy.data.images:
		if ".0" in i.name:
			print("Removing: " + i.name)
			removeimage(i.name)

def removeduplicatematerials():
	for i in bpy.data.materials:
		if ".0" in i.name:
			print("Removing: " + i.name)
			removematerial(i.name)

def selectallobjectswithduplicates():
	for m in bpy.data.objects:
		for ms in m.material_slots:
			if ".0" in ms.name:
				print(ms)
				m.select = True

def setSelectionOfObjectAndChildren(obj, status):
	obj.select = status
	for i in obj.children:
		setSelectionOfObjectAndChildren(i, status)

def selectAllChildren():
	for ob in bpy.data.objects:
		if ob.select:
			setSelectionOfObjectAndChildren(ob, True)


def printObjectMaterials(obj):
	for m in obj.data.materials:		
		if m is not None:
			print(m.name)		


def getWorldSpaceBoundingBox(ob):
	return [ob.matrix_world * Vector(corner) for corner in ob.bound_box]

def getCamSpaceBoundingBox(ob, camera):
	scene = bpy.context.scene
	wsbb = getWorldSpaceBoundingBox(ob)
	cam_coord = [object_utils.world_to_camera_view(scene, camera, Vector(corner)) for corner in wsbb]
	return cam_coord

def getCamSpaceVertexPositions(ob, camera):
	scene = bpy.context.scene	
	cam_coord = [object_utils.world_to_camera_view(scene, camera, Vector(position.co * ob.matrix_world + ob.matrix_world.translation )) for position in ob.data.vertices]
	return cam_coord


def getBounds3D(coords):
	x1 = 10000 
	y1 = 10000
	z1 = 10000
	x2 = -10000
	y2 = -10000
	z2 = -10000
	for pt in coords:
		if pt[0] < x1:  #x
			x1 = pt[0]
		if pt[1] < y1:  #y
			y1 = pt[1]
		if pt[2] < z1:  #z
			z1 = pt[2]
		if pt[0] > x2:  #x2
			x2 = pt[0]
		if pt[1] > y2:  #x2
			y2 = pt[1]
		if pt[2] > z2:  #z2
			z2 = pt[2]
	return ((x1,y1,z1),(x2,y2,z2))


def getBounds2D(screen_coords):
	x1 = 10000 
	y1 = 10000
	x2 = -10000
	y2 = -10000
	for pt in screen_coords:
		if pt[0] < x1:  #x
			x1 = pt[0]
		if pt[1] < y1:  #y
			y1 = pt[1]
		if pt[0] > x2:  #x2
			x2 = pt[0]
		if pt[1] > y2:  #x2
			y2 = pt[1]
	return ((x1,y1),(x2,y2))

def min(a, b):
	return a if a < b else b

def max(a, b):
	return a if a > b else b

def mergeBounds(a, b):
	return ((min(a[0][0], b[0][0]), min(a[0][1], b[0][1])), (max(a[1][0], b[1][0]), max(a[1][1], b[1][1])))


	


def getScreenSpaceBoundsNoScale(ob, camera, useBounds = False):
	scene = bpy.context.scene
	cam_coord = None
	if useBounds:
		cam_coord = getCamSpaceBoundingBox(ob, camera)
	else:
		cam_coord = getCamSpaceVertexPositions(ob, camera)		
	render_scale = scene.render.resolution_percentage / 100
	render_size = (int(scene.render.resolution_x * render_scale),int(scene.render.resolution_y * render_scale))	
	screen_coords = [(pt.x, pt.y) for pt in cam_coord]
	bounds = getBounds2D(screen_coords)
	return bounds

def getScreenSpaceBounds(ob, camera, useBounds = False):
	bounds = getScreenSpaceBoundsNoScale(ob, camera, useBounds)
	render_scale = scene.render.resolution_percentage / 100	
	render_size = ((scene.render.resolution_x * render_scale),(scene.render.resolution_y * render_scale))	
	return ((bounds[0][0] * render_size[0], bounds[0][1] * render_size[1]), (bounds[1][0] * render_size[0], bounds[1][0] * render_size[1]))


def getScreenSpaceBoundsOfSelection(camera, useBounds = False):
	bounds = ((100000,100000), (-100000, -100000))
	for i in bpy.context.scene.objects:
		if i.select and isinstance(i.data, Mesh):
			bounds = mergeBounds(bounds, getScreenSpaceBoundsNoScale(i, camera, useBounds))
	return bounds

def getScreenSpaceBoundsWithLayerMask(camera, useBounds = False, layermask = 0):
	bounds = ((100000,100000), (-100000, -100000))
	for i in bpy.context.scene.objects:
		if i.layermask and isinstance(i.data, Mesh):
			bounds = mergeBounds(bounds, getScreenSpaceBoundsNoScale(i, camera, useBounds))
	return bounds
#int(scene.render.resolution_x * render_scale) * render_size[0],
#int(scene.render.resolution_y * render_scale) * render_size[1],
	  
def setRenderBoundsToObject(ob, camera, useBounds = False):
	bounds = getScreenSpaceBoundsNoScale(ob, camera, useBounds)
	bpy.context.scene.render.use_border = True		
	print(bounds)
	bpy.context.scene.render.border_min_x = bounds[0][0]
	bpy.context.scene.render.border_max_x = bounds[1][0]
	bpy.context.scene.render.border_min_y = bounds[0][1]
	bpy.context.scene.render.border_max_y = bounds[1][1]
	print("Render Bounds: " + "min_x: " + str(bpy.context.scene.render.border_min_x) + ", " + "max_x: " + str(bpy.context.scene.render.border_max_x) + ", " + "min_y: " + str(bpy.context.scene.render.border_min_y) + ", " + "max_y: " + str(bpy.context.scene.render.border_max_y) )

def setRenderBoundsToSelection(camera, useBounds = False):
	bounds = getScreenSpaceBoundsOfSelection(camera)
	bpy.context.scene.render.use_border = True		
	print(bounds)
	bpy.context.scene.render.border_min_x = bounds[0][0]
	bpy.context.scene.render.border_max_x = bounds[1][0]
	bpy.context.scene.render.border_min_y = bounds[0][1]
	bpy.context.scene.render.border_max_y = bounds[1][1]
	print("Render Bounds: " + "min_x: " + str(bpy.context.scene.render.border_min_x) + ", " + "max_x: " + str(bpy.context.scene.render.border_max_x) + ", " + "min_y: " + str(bpy.context.scene.render.border_min_y) + ", " + "max_y: " + str(bpy.context.scene.render.border_max_y) )


def restoreRenderBounds():
	bpy.context.scene.render.border_min_x = 0
	bpy.context.scene.render.border_max_x = 1
	bpy.context.scene.render.border_min_y = 0
	bpy.context.scene.render.border_max_y = 1

def replaceDuplicatedMaterialReferences():
	for o in bpy.data.objects:
		try:
			for m in o.data.materials:
				if m is not None:
					if ".0" in m.name:
						print("found a potentially duplicated material: " + m.name)
						matname = m.name.split(".0")[0]
						try:
							matobj = bpy.data.materials[matname]
							print("Replacing " + m.name + " with " + matname)
							m.data.materials[m.name] = matobj
						except KeyError:
							print(matname + " wasn't found, can't replace.")
		except AttributeError as e:
			print(o.name + " has no materials, ignoring. Error #" + str(e))



def replaceDuplicatedMaterialSlotReferences():
	for o in bpy.data.objects:
		try:
			for m in o.material_slots:
				if m is not None:
					if ".0" in m.name:
						print("found a potentially duplicated material: " + m.name)
						matname = m.name.split(".0")[0]
						try:
							matobj = bpy.data.materials[matname]
							print("Replacing " + m.name + " with " + matname)
							m.material = matobj
						except KeyError:
							print(matname + " wasn't found, can't replace.")
		except AttributeError as e:
			print(o.name + " has no material slots, ignoring. Error #" + str(e))



def hash_mesh(mesh):
	INVALID_HASH = 0xFFFFFFFF
	HASH_INIT = 0x811c9dc5
	HASH_PRIME = 0x01000193
	HASH_MASK = 0x7FFFFFFF
	hash = HASH_INIT
	vertexcount = len(mesh.vertices)
	polygoncount = len(mesh.polygons)
	hash = ((hash * HASH_PRIME) ^ vertexcount) & 0xFFFFFFFF
	hash = ((hash * HASH_PRIME) ^ polygoncount) & 0xFFFFFFFF
	for v in mesh.vertices:
		hash = ((hash * HASH_PRIME) ^ int(v.normal.x * 1000.0)) & 0xFFFFFFFF
		hash = ((hash * HASH_PRIME) ^ int(v.normal.y * 1000.0)) & 0xFFFFFFFF
		hash = ((hash * HASH_PRIME) ^ int(v.normal.z * 1000.0)) & 0xFFFFFFFF
	return hash & 0xFFFFFFFF


#print("Mesh " + m.name + " has...")
#		print("\t" + str(vcount) + " vertices")
#		print("\t" + str(pcount) + " polygons")

def findPotenteialDuplicatedMeshes():
	meshtable = {}
	for m in bpy.data.meshes:			
		meshhash = hash_mesh(m)
		try:
			table = meshtable[meshhash]
			table.append(m)
		except KeyError:		
			meshtable[meshhash] = [m]
	return meshtable

def printUniqueMeshes(mt, threshold):
	for mte in mt:
		meshlist = mt[mte]
		meshcount = len(meshlist)
		if meshcount > threshold:
			vcount = len(meshlist[0].vertices)
			pcount = len(meshlist[0].polygons)
			print(str(meshcount) + " meshes with " + str(vcount)  + " vertices, " + str(pcount) + " polygons: " + " and a hash of " + str(mte))
			for m in mt[mte]:
				if len(m.vertices) != vcount:
					print("error, hash collision: " + m.name + " does not have correct number of vertices")
				print(m.name + ", ", end='')
			print(".")


def contains(list, filter):
    for x in list:
        if filter(x):
            return True
    return False


def find(list, filter):
    for x in list:
        if filter(x):
            return x
    return None


def removeDuplicateMeshReferences(duplicateAmountThreshold = 1):
	mt = findPotenteialDuplicatedMeshes()
	for meshlistkey in mt:		
		meshlist = mt[meshlistkey]
		meshcount = len(meshlist)
		if meshcount > duplicateAmountThreshold:
			for ob in bpy.data.objects:
				if ob.data in meshlist:
					if ob.data != meshlist[0].name:
						print("Replacing duplicate mesh data block " + ob.data.name + " with " + meshlist[0].name)
						ob.data = meshlist[0]
				
					

def printMeshStats(minvcount):
	for m in bpy.data.meshes:
		if (len(m.vertices) > minvcount):
			print(m.name + " vertex count: " + str(len(m.vertices)) + ", " + " polygon count: " + str(len(m.polygons)))


	

def createModifierForObject(modname, typename):
	if isinstance(obj.data, Mesh):		
		me = obj.data
		mod = obj.modifiers.new(modname, typename)	
	



def createModifierForAllSelected(modname, typename):	
	for ob in bpy.data.objects:
		if ob.select == True and isinstance(ob.data, Mesh):
			createModifierForObject(modname, typename)


def startMeshUpdate(obj):
	if isinstance(obj.data, Mesh):		
		me = obj.data
		if me.is_editmode:
			# Gain direct access to the mesh
			bm = bmesh.from_edit_mesh(me)
		else:
			# Create a bmesh from mesh
			# (won't affect mesh, unless explicitly written back)
			bm = bmesh.new()
			bm.from_mesh(me)		
		return bm
	else:
		return None

def endMeshUpdate(obj, bm):
	if isinstance(obj.data, Mesh):		
		me = obj.data
		if me.is_editmode:
				bmesh.update_edit_mesh(me)
		else:
			bm.to_mesh(me)
			me.update()
		bm.free()
		del bm

def projectXYuvs(obj):
	# adjust UVs
	bm = startMeshUpdate(obj)
	if bm != None:
		uv_layer = bm.loops.layers.uv.verify()
		print("About to create UVs for: " + obj.name)
		bm.faces.layers.tex.verify()  # currently blender needs both layers.	
		startMeshUpdate(obj)
		for f in bm.faces:
			for l in f.loops:
				luv = l[uv_layer]
				if luv.select:
					# apply the location of the vertex as a UV
					luv.uv = l.vert.co.xy
		endMeshUpdate(obj, bm)


def ensureUVs(obj):
	bm = startMeshUpdate(obj)
	if bm != None:
		print("About to create UVs for: " + obj.name)	
		uv_layer = bm.loops.layers.uv.verify()
		bm.faces.layers.tex.verify()  # currently blender needs both layers.	
		endMeshUpdate(obj, bm)

def applyProjectionModifierToAlSelected():
	for ob in bpy.data.objects:
		if ob.select == True and isinstance(ob.data, Mesh):
			projectXYuvs(ob)


def removeUnusedMaterials():
	D = bpy.data
	delete_list = []
	for i in D.materials:
		if i.users == 0:
			delete_list.append(i)
	print("Found " + str(len(delete_list)) + " materials that had no users, deleting them now.") 
	for i in delete_list:
		D.materials.remove(i)



def applyMaterialToSelectedObjects(mat = None):
	D = bpy.data
	if mat == None:
		try:
			mat = D.materials['Material']
		except:
			mat = D.Materials[0];
	for ob in bpy.data.objects:			
		if ob.select == True and isinstance(ob.data, Mesh):			
			if len(ob.material_slots) < 1:
				ob.data.materials.append(mat)
			else:
				ob.data.materials[0] = mat
	bpy.data.scenes[0].update()




def enableOnlyLayer(layerName):
	for i in bpy.context.scene.render.layers:
		i.use = i.name == layerName			 


def RenderEachObject():
	for ob in bpy.data.objects:
		if ob.select == True and isinstance(ob.data, Mesh):	
			ApplyBackProjectionToObject(ob, camera)



	#	print("About to render scene")	
	#bpy.ops.render.render(layer="RenderLayer") # write_still=True
	#enableOnlyLayer("RenderLayer")
	#bpy.data.images['Render Result'].save_render("C:\\Users\\Tim\\Google Drive\\OysterWorld\\HOPA\\BlenderOutput\\layer0.png")
	#bpy.data.images['Render Result'].
	#print("Rendered layer 0")	
	#enableOnlyLayer("Overlay")
	#bpy.ops.render.render() 
	#bpy.data.images['Render Result'].save_render("C:\\Users\\Tim\\Google Drive\\OysterWorld\\HOPA\\BlenderOutput\\layer1.png")
	#return {'FINISHED RENDER'}


def createuvs_withprojection():
	for ob in bpy.data.objects:
		if ob.select == True:
			projectXYuvs(ob)
		
def createuvs():
	for ob in bpy.data.objects:
		if ob.select == True:
			ensureUVs(ob)		

def hideselected():
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.hide = True

def showselected():
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.hide = False

def showall():
	for ob in bpy.data.objects:     
		ob.hide = False     

def rendershowselected():
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.hide_render = False
	bpy.data.scenes[0].update()

def setCameraRayVisibility(status):
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.cycles_visibility.camera = status
	bpy.data.scenes[0].update()

def renderhideselected():
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.hide_render = True
	bpy.data.scenes[0].update()

def activateselected():
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.hide_select = False          
	bpy.data.scenes[0].update()

def disableselected():
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.hide_select = True           
	bpy.data.scenes[0].update()

def disablerigidbodyonselected():
	for ob in bpy.data.objects:
		if ob.select == True and ob.rigid_body != None:
			ob.rigid_body.enabled = False                       


def setnameforallselected(name):
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.name = name

def enablerigidbodyonselected():
	for ob in bpy.data.objects:
		if ob.select == True and ob.rigid_body != None:
			ob.rigid_body.enabled = True

def int_to_blender_layers(intmask):
	retarray = []
	for i in range(0,20):
		retarray.append((intmask & (1 << i)) != 0)
	return retarray

def print_array(array):
	for i in array:
		print(i)


def orlayermaskforallselected(layermask):
	scene = bpy.context.scene
	for ob in bpy.data.objects:
		if ob.select == True:
			for i in range(0, len(ob.layers)):
				ob.layers[i] |= layermask[i]

def setlayermaskforallselected(layermask):
	scene = bpy.context.scene
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.layers = layermask

def setAllSelectedToCurrentLayers():
	scene = bpy.context.scene	
	setlayermaskforallselected(scene.layers);


def orAllSelectedWithCurrentLayers():
	scene = bpy.context.scene	
	orlayermaskforallselected(scene.layers);


def addselectedobjectsrigidbodykeyframes(kfname):
	scene = bpy.context.scene
	for ob in bpy.data.objects:
		if ob.select == True and ob.rigid_body != None:
			ob.rigid_body.keyframe_insert(data_path=kfname, frame=scene.frame_current)

def addselectedobjectskeyframes(kfname):
	scene = bpy.context.scene
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.keyframe_insert(data_path=kfname, frame=scene.frame_current)      

def objectinfo(object, spacing=10, collapse=1):
	methodList = [e for e in dir(object) if callable(getattr(object, e))]
	processFunc = collapse and (lambda s: " ".join(s.split())) or (lambda s: s)
	print("\n".join(["%s %s" %
					 (method.ljust(spacing),
					  processFunc(str(getattr(object, method).__doc__)))
					 for method in methodList]))


