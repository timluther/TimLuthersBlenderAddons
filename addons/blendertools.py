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

import sys
file = open(filepath, "w")
sys.stdout = file
sys.stdout = sys.__stdout__ #reset
file.close()