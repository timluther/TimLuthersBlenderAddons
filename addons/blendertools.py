import bpy

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


def printObjectMaterials(obj):
	for m in obj.data.materials:		
		if m is not None:
			print(m.name)		


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
	if isinstance(obj.data, bpy_types.Mesh):		
		me = obj.data
		mod = obj.modifiers.new(modname, typename)	
	
def ApplyBackProjection(obj, camera):
	if isinstance(obj.data, bpy_types.Mesh):		
		print("got here")
		me = obj.data
		uvchan = None
		try:
			uvchan = me.uv_textures['ProjUV']
		except:
			uvchan = me.uv_textures.new('ProjUV')
		try:
			uvproj = obj.modifiers['UVProject']
		except :		
			uvproj = obj.modifiers.new("UVProject", 'UV_PROJECT')
		uvproj.use_image_override = True
		if camera == None:
			camera = bpy.data.cameras[0]
		uvproj.projectors[0].object = camera
		image = None
		try:
			bpy.data.images['RenderTarget']
		except:
			image = None
		uvproj.image = image
		uvproj.scale_x = 0.86
		uvproj.scale_y = 0.46
		uvproj.uv_layer='ProjUV'

def createModifierForAllSelected(modname):
	bpy.context.scene.objects.active = target

def startMeshUpdate(obj):
	if isinstance(obj.data, bpy_types.Mesh):		
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
	if isinstance(obj.data, bpy_types.Mesh):		
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

#more to remind myself about bpy.context.active_object
def ApplyBackProjectionToCurrent(camera):
	ApplyBackProjection(bpy.context.active_object, camera)

def ensure_uvs(obj):
	bm = startMeshUpdate(obj)
	if bm != None:
		print("About to create UVs for: " + obj.name)	
		uv_layer = bm.loops.layers.uv.verify()
		bm.faces.layers.tex.verify()  # currently blender needs both layers.	
		endMeshUpdate(obj, bm)

def applyBackProjectionToSelected(camera):
	for ob in bpy.data.objects:
		if ob.select == True:
			ApplyBackProjection(ob, camera)

def applyProjectionModifier():
	for ob in bpy.data.objects:
		if ob.select == True:
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
		if ob.select == True and isinstance(ob.data, bpy_types.Mesh):			
			if len(ob.material_slots) < 1:
				ob.data.materials.append(mat)
			else:
				ob.data.materials[0] = mat



def createuvs_withprojection():
	for ob in bpy.data.objects:
		if ob.select == True:
			projectXYuvs(ob)
		
def createuvs():
	for ob in bpy.data.objects:
		if ob.select == True:
			ensure_uvs(ob)		

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

def renderhideselected():
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.hide_render = True

def activateselected():
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.hide_select = False          

def disableselected():
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.hide_select = True           

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


