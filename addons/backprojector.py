import bpy
import sys
import os
from blendertools import *
from bpy_types import *
import bpy_extras
import json
from bpy.props import IntProperty, BoolProperty, FloatProperty, EnumProperty
import csv
from os.path import expanduser
import PIL
import image_packer

bl_info = {
	"name": "BackProjection tools",
	"author": "Tim Lewis",
	"version": (0, 0, 4),
	"blender": (2, 7, 0),
	"location": "Toolshelf",
	"description": "Tools back projection, i.e. rendering to a texture and then using that render to shade a the scene in realtime",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "OverPaint"
}

LAYER_BACKGROUND = 0
LAYER_POPPED_OUT = 1
LAYER_PICKUP	 = 2
LAYER_SCRATCH	 = 3

layer_names = ["background", "popped_out", "picked_up", "scratch"]

class viewportParams:

	def __init__(self, zoom=1.0, offset=[0, 0]):
		self.zoom = zoom
		self.offsetx = offset[0]
		self.offsety = offset[1]
		self.field_second = False
		self.field_odd = False


#Recreate camera matrix b/c blender doesn't give it to you
#thanks to Goran Milovanovic for doing the legwork
#http://blender.stackexchange.com/questions/16472/how-can-i-get-the-cameras-projection-matrix
def viewPlane(camd, winx, winy, xasp, yasp, params):
	#/* fields rendering */
	ycor = yasp / xasp
	use_fields = False
	if (use_fields):
		ycor *= 2

	def BKE_camera_sensor_size(p_sensor_fit, sensor_x, sensor_y):
		#/* sensor size used to fit to. for auto, sensor_x is both x and y. */
		if (p_sensor_fit == 'VERTICAL'):
			return sensor_y

		return sensor_x

	if (camd.type == 'ORTHO'):
		#/* orthographic camera */
		#/* scale == 1.0 means exact 1 to 1 mapping */
		pixsize = camd.ortho_scale
	else:
		#/* perspective camera */
		sensor_size = BKE_camera_sensor_size(camd.sensor_fit, camd.sensor_width, camd.sensor_height)
		pixsize = (sensor_size * camd.clip_start) / camd.lens

	#/* determine sensor fit */
	def BKE_camera_sensor_fit(p_sensor_fit, sizex, sizey):
		if (p_sensor_fit == 'AUTO'):
			if (sizex >= sizey):
				return 'HORIZONTAL'
			else:
				return 'VERTICAL'

		return p_sensor_fit

	sensor_fit = BKE_camera_sensor_fit(camd.sensor_fit, xasp * winx, yasp * winy)
	print("Sensor fit: " + sensor_fit)

	if (sensor_fit == 'HORIZONTAL'):
		viewfac = winx
	else:
		viewfac = ycor * winy
	print("winx: %f, winy: %f\n" % (winx, winy))
	pixsize /= viewfac

	#extra zoom factor
	pixsize *= 1 * params.zoom

	#/* compute view plane:
	# * fully centered, zbuffer fills in jittered between -.5 and +.5 */
	xmin = -0.5 * winx
	ymin = -0.5 * ycor * winy
	xmax =  0.5 * winx
	ymax =  0.5 * ycor * winy

	#/* lens shift and offset */
	dx = camd.shift_x * viewfac + winx * params.offsetx
	dy = camd.shift_y * viewfac + winy * params.offsety

	xmin += dx
	ymin += dy
	xmax += dx
	ymax += dy

	#/* fields offset */
	if (params.field_second):
		if (params.field_odd):
			ymin -= 0.5 * ycor
			ymax -= 0.5 * ycor
		else:
			ymin += 0.5 * ycor
			ymax += 0.5 * ycor

	#/* the window matrix is used for clipping, and not changed during OSA steps */
	#/* using an offset of +0.5 here would give clip errors on edges */
	print("Prescale window offsets x: %f..%f y:%f..%f\n" % (xmin, xmax, ymin, ymax))
	xmin *= pixsize
	xmax *= pixsize
	ymin *= pixsize
	ymax *= pixsize
	print("Final window offsets x: %f..%f y:%f..%f\n" % (xmin, xmax, ymin, ymax))

	return xmin, xmax, ymin, ymax


def projectionMatrix(camd, scale = [1, 1], trans = [0, 0, 0], aspect = [1, 1]):
	r = bpy.context.scene.render

	print("Using resolution of %s:%s for render" % (r.resolution_x, r.resolution_y))
	left, right, bottom, top = viewPlane(camd, r.resolution_x, r.resolution_y , aspect[0], aspect[1], params = viewportParams())

	farClip, nearClip = camd.clip_end, camd.clip_start

	Xdelta = right - left
	Ydelta = top - bottom
	Zdelta = farClip - nearClip
	print("delta: %f ,%f, %f Trans: %f, %f, %f\n" % (Xdelta, Ydelta, Zdelta, trans[0], trans[1], trans[2]))
	return Matrix([
				[(nearClip * 2 / Xdelta) * scale[0], 0, 0, 0],
				[0, (nearClip * 2 / Ydelta) * scale[1], 0, 0],
				[(right + left) / Xdelta, (top + bottom) / Ydelta, (farClip + nearClip) / Zdelta, -1],
				[0, 0, 0 + (-2 * nearClip * farClip) / Zdelta, 1]]) * Matrix.Translation(trans).transposed()

def getActiveView():
	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			return area.spaces.active
	return None

#The views hold some sort of projection and view matrices but haven't so far been able to make these
#match the generated camera matrix above
def getActiveViewMatrix():
	for area in bpy.context.screen.areas:
		if area.type == 'VIEW_3D':
			return area.spaces.active.region_3d.perspective_matrix.transposed() * area.spaces.active.region_3d.view_matrix.transposed()
	return None


def Make2DScaleMatrix(scale):
	return Matrix([[scale[0], 0, 0, 0], [0, scale[1], 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])

#for a given object and camera, return the MVP. This should be an exact match to the UV projection
#modifier (not quite, at time of writing: some scaling is off, possibly something to do with image scale?)


def getActiveViewMVP(obj):
	projmat = getActiveViewMatrix()
	return obj.matrix_world.transposed() * projmat

def getLayerFilename(layer, ob = None):
	if ob is not None:
		return layer_names[layer] + "_" + ob.name + "_layer.png"
	else:
		return layer_names[layer] + "_layer.png"

def EnsureImageInner(name, filename, resolution = (256, 256)):
	image = None
	try:
		image = bpy.data.images[name]
		print("Found image " + str(image))
		if Equality(image.size, resolution) == False:
			print("Image found but size of " + name + " (%i, %i) does not match target (%i, %i)." % (image.size[0], image.size[1], resolution[0], resolution[1]))
		else:
			print("Found and using existing image: " + name)
	except Exception as inst:
		print(str(inst))
		print("Could not find " + name + " Creating new image at %i,%i resolution" % (resolution[0], resolution[1]))
		image = bpy.data.images.new(name, resolution[0], resolution[1])
	image.filepath = filename
	image.save()  # presave, allows for reload
	return image


def EnsureImage(layer, ob = None, Resolution = None):
	scene = bpy.context.scene
	layer_name = getLayerFilename(layer, ob)
	resolution = [scene.render.resolution_x, scene.render.resolution_y]
	if Resolution is not None:
		resolution = Resolution
	if ob is not None:
		bounds = getScreenSpaceBounds(ob, scene.camera)
		resolution = (bounds[1][0] - bounds[0][0], bounds[1][1] - bounds[0][1])
	print("trying to ensure image " + layer_name)
	image = EnsureImageInner(layer_name, GetBasePath() + "_" + layer_name, resolution)
	print("Image filename set to " + image.filepath)
	return image



class ApplyBackProjection(bpy.types.Operator):
	bl_idname = "view3d.apply_back_projection"
	bl_label = "Apply back projection"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)

	def execute(self, context):
		print("About to apply back projection")
		scene = bpy.context.scene
		ApplyBackProjectionToSelected(scene.camera, True)
		return {'FINISHED'}

class ApplyBackProjectionNoMod(bpy.types.Operator):
	bl_idname = "view3d.apply_back_projection_no_mod"
	bl_label = "Apply back projection direct (not using modifier)"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)

	def execute(self, context):
		print("About to apply back projection without modifier")
		ApplyBackProjectionToSelected(bpy.context.scene.camera, False)
		return {'FINISHED'}

class RenderScene(bpy.types.Operator):
	bl_idname = "view3d.render_scene"
	bl_label = "Render Scene"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
	PerObjectLayers = BoolProperty(default = True)
	RenderCombined = BoolProperty(default = True)

	def execute(self, context):
		print("About to render scene")
		RestoreSourceMaterials()
		SerialiseMaterials()  	  # save current materials off to json file
		scene = bpy.context.scene
		RenderResult = bpy.data.images["Render Result"]
		ApplyBackProjectionTo(scene.camera, False, lambda ob: True)

		##BACKGROUND LAYER##
		scene.render.use_border = False
		setCameraRayVisibility(True, func = lambda ob: ob.layers[0] == True)
		setCameraRayVisibility(False, func = lambda ob: ob.layers[1] == True)
		image = EnsureImage(LAYER_BACKGROUND)
		print("Setting scene render filepath: " + image.filepath)
		scene.render.filepath = image.filepath
		bpy.ops.render.render(write_still = True, layer = "RenderLayer")

		print("About to save render as " + image.filepath)
		RenderResult.save_render(image.filepath)
		image.reload()
		mat = FindOrCreateProjectionMaterial(image)
		SetPreviewMaterial(mat, lambda ob: ob.layers[0] == True)
		print("Completed")
		RenderCombined = True
		##POPPED OUT-LAYER##
		if self.PerObjectLayers:
			ObjectImagePairs = []
			scene.render.use_border = True
			scene.render.use_crop_to_border = True  # Make sure we crop so that the image file we create is small
			scene.cycles.film_transparent = True    # Ensure a transparent layer
			setCameraRayVisibility(False, func = lambda ob: ob.layers[0] == True) 	# turn off rendering of base layers
			for ob in scene.objects:												# Render each object seperately
				if isinstance(ob.data, Mesh):
					if ob.layers[1] == True:
						setCameraRayVisibility(False, func = lambda ob: ob.layers[1] == True) 	# turn off rendering of base layers			
						ob.cycles_visibility.camera = True   			 # Make object visible
						setRenderBoundsToObject(ob, scene.camera)  		 # ensure we only clip this image
						if isRenderImageTooSmall() == False:						
							image = EnsureImage(LAYER_POPPED_OUT, ob)
							ObjectImagePairs.append((image, ob))
							scene.render.filepath = image.filepath
							bpy.ops.render.render(write_still = True, layer = "RenderLayer")
							print("About to save render as " + image.filepath)
							RenderResult.save_render(image.filepath)
							image.reload()
							print("Completed")
						else:
							print("Image Size too small!" + ob.name + " " + str(getScreenSpaceBounds(ob, scene.camera)))
		scene.render.use_crop_to_border = False
		restoreRenderBounds()
		if RenderCombined:
			image = EnsureImage(LAYER_POPPED_OUT)
			setCameraRayVisibility(False, func = lambda ob: ob.layers[0] == True)
			setCameraRayVisibility(True, func = lambda ob: ob.layers[1] == True)
			scene.render.filepath = image.filepath
			bpy.ops.render.render(write_still = True, layer = "RenderLayer")
			RenderResult.save_render(image.filepath)
			image.reload()

			pilImages = [(convertBlenderToPIL(img), img.name) for img, ob in ObjectImagePairs]
			imagesortlist = sorted((img.size[0] * img.size[1], name, img) for img, name in pilImages)
			packedImages, tree = image_packer.PackImagesFromList(imagesortlist, 'RGBA', (256, 256))
			packedtexture_fn = GetBasePath() + "_texture_page.png"
			packedImages.save(packedtexture_fn)
			head, name = os.path.split(packedtexture_fn)
			EnsureImageInner(name, packedtexture_fn)	#reload as blender image
			#now traverse tree, offset UVs
			mat = FindOrCreateProjectionMaterial(image)
			SetPreviewMaterial(mat, lambda ob: ob.layers[1] == True)

		# Now pack all the sub images

		scene.cycles.film_transparent = False
		scene.render.use_border = False
		scratch = EnsureImage(LAYER_SCRATCH, Resolution = (1024, 1024))
		setCameraRayVisibility(True, lambda ob: True)
		#bpy.ops.render.render( write_still=True, layer="Overlay")
		#bpy.data.images['Render Result'].save_render("C:\\Users\\Tim\\Google Drive\\OysterWorld\\HOPA\\BlenderOutput\\layer1.png")
		return {'FINISHED'}

class CSavePSD(bpy.types.Operator):
	bl_idname = "view3d.save_psd"
	bl_label = "Save PSD"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)

	def execute(self, context):
		print("About to save PSD")
		return {'FINISHED'}

class CSaveFBX(bpy.types.Operator):
	bl_idname = "view3d.save_fbx"
	bl_label = "Save FBX"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)

	def execute(self, context):
		print("About to save FBX")
		return {'FINISHED'}


class CSaveMaterials(bpy.types.Operator):
	bl_idname = "view3d.save_materials"
	bl_label = "Save Materials"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)

	def execute(self, context):
		SerialiseMaterials()  	# save current materials off to json file
		return {'FINISHED'}

class CSetPreviewMaterial(bpy.types.Operator):
	bl_idname = "view3d.set_preview_material"
	bl_label = "Set Preview Material"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)

	def execute(self, context):
		print("About to set preview material")

		RestoreSourceMaterials()  # make sure we're not saving the wrong ones
		SerialiseMaterials()  	  # save current materials off to json file
		image = EnsureImage(LAYER_BACKGROUND)
		mat = FindOrCreateProjectionMaterial(image)
		SetPreviewMaterial(mat, lambda ob: ob.layers[0] == True)
		image = EnsureImage(LAYER_POPPED_OUT)
		mat = FindOrCreateProjectionMaterial(image)
		SetPreviewMaterial(mat, lambda ob: ob.layers[1] == True)
		return {'FINISHED'}

class CRestoreSourceMaterials(bpy.types.Operator):
	bl_idname = "view3d.restore_source_material"
	bl_label = "Restore source materials"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)

	def execute(self, context):
		print("About to set preview material")
		RestoreSourceMaterials()
		return {'FINISHED'}


def copylist(inlist):
	return [i in inlist]

def GetBasePath():
	path = os.path.splitext(bpy.data.filepath)[0]
	if len(path) == 0:
		path = os.path.join(os.path.expanduser('~'), "BlenderScene")
	return path


def GetSceneMaterialFilename():
	fname = GetBasePath()

	return  fname+ "_materials.csv"

def SceneMaterialsToMap():
	materialdb = {}
	for ob in bpy.data.objects:
		if isinstance(ob.data, Mesh):
			materialdb[ob.name] = [i.name for i in ob.data.materials if i is not None]
	return materialdb

def SerialiseMaterials():
	MaterialMap = SceneMaterialsToMap()
	fname = GetSceneMaterialFilename()
	print("Saving materials to: " + fname)
	s = open(fname, "w")
	json.dump(MaterialMap, s)
	s.close()

def LoadMaterials():
	fname = GetSceneMaterialFilename()
	print("Opening material file at: " + fname)
	return json.load(open(fname, "r"))

def SetPreviewMaterial(mat, func = lambda ob: True):
	for ob in bpy.data.objects:
		if isinstance(ob.data, Mesh) and func(ob):
			print("Setting material of " + ob.name + " to " + mat.name)
			oldCount = len(ob.data.materials)
			ob.data.materials.clear()
			for i in range(oldCount):
				ob.data.materials.append(mat)


def RestoreSourceMaterials():
	try:
		materials = LoadMaterials()  # retrieve current materials from json file
	except:
		print("failed to load material file.")
	try:
		for ob in bpy.data.objects:
			if isinstance(ob.data, Mesh):
				try:
					oldmaterials =  materials[ob.name]
					if len(oldmaterials) > 0:
						ob.data.materials.clear()
						for mat in oldmaterials:
							ob.data.materials.append(bpy.data.materials[mat])
				except:
					print("Old scene not found")
		materials.clear()
	except:
		print("Problem with materials restore")


def ensureUVChannels(obj):
	uvoffsetchan = None  # offsets in to the texture page
	uvchandivw = None
	uvchan = None
	zwchan = None
	try:
		uvchandivw = obj.data.uv_textures['ProjUVdivW']
	except:
		uvchandivw = obj.data.uv_textures.new('ProjUVdivW')
	try:
		uvchan = obj.data.uv_textures['ProjUV']
	except:
		uvchan = obj.data.uv_textures.new('ProjUV')
	try:
		zwchan = obj.data.uv_textures['ProjUVZW']
	except:
		zwchan = obj.data.uv_textures.new('ProjUVZW')
	try:
		uvoffsetchan = obj.data.uv_textures['UVOffset']
	except:
		uvoffsetchan = obj.data.uv_textures.new('UVOffset')

	return uvchan, zwchan, uvchandivw


def createNode(group, typeName, pos, name = ""):
	node = group.nodes.new(type = typeName)
	if name != "":
		node.name = name
	node.location = pos
	return node

def removeAllUnusedNodeGroups():
	count = len(bpy.data.node_groups)
	offset = 0
	while count > 0:
		try:
			bpy.data.node_groups.remove(bpy.data.node_groups[offset])
		except:
			print("Cannot remove " + bpy.data.node_groups[offset].name)
			offset = offset + 1
		count = count - 1

def CreatePerspectiveCorrectGroup(name):
	uvp = bpy.data.node_groups.new(name, 'ShaderNodeTree')
	xgap = 200
	cx = 0
	ygap = 200

	uv_xyinput = createNode(uvp, "ShaderNodeAttribute", (cx, 0))
	uv_xyinput.attribute_name = 'ProjUV'
	uv_zwinput = createNode(uvp, "ShaderNodeAttribute", (cx, ygap))
	uv_zwinput.attribute_name = 'ProjUVZW'
	cx += xgap
	sepUVXY = createNode(uvp, "ShaderNodeSeparateXYZ", (cx, 0))
	sepUVZW = createNode(uvp, "ShaderNodeSeparateXYZ", (cx, ygap))
	cx += xgap
	divideX = createNode(uvp, "ShaderNodeMath", (cx, 0), "DivideX")
	divideX.operation = 'DIVIDE'
	divideY = createNode(uvp, "ShaderNodeMath", (cx, ygap), "DivideY")
	divideY.operation = 'DIVIDE'
	cx += xgap
	combineXYZ = createNode(uvp, "ShaderNodeCombineXYZ", (cx, 0))
	output = uvp.nodes.new('NodeGroupOutput')
	cx += xgap
	output.location = (cx, 0)
	uvp.links.new(uv_xyinput.outputs[1], sepUVXY.inputs[0])
	uvp.links.new(uv_zwinput.outputs[1], sepUVZW.inputs[0])
	uvp.links.new(sepUVXY.outputs[0], divideX.inputs[0])
	uvp.links.new(sepUVXY.outputs[1], divideY.inputs[0])
	uvp.links.new(sepUVZW.outputs[1], divideX.inputs[1])
	uvp.links.new(sepUVZW.outputs[1], divideY.inputs[1])
	uvp.links.new(divideX.outputs[0], combineXYZ.inputs[0])
	uvp.links.new(divideY.outputs[0], combineXYZ.inputs[1])
	uvp.links.new(sepUVXY.outputs[2], combineXYZ.inputs[2])
	uvp.links.new(combineXYZ.outputs[0], output.inputs[0])
	return uvp

def FindOrCreateProjUVGroup():
	try:
		uvp = bpy.data.node_groups['UVPerspectiveCorrect']
		return uvp
	except:
		return CreatePerspectiveCorrectGroup('UVPerspectiveCorrect')

def FindOrCreateProjectionMaterial(image):
	matname = "OverpaintMaterial_%s" % image.name
	try:
		mat = bpy.data.materials[matname]
		nodes = mat.node_tree.nodes
		imagetex = mat.node_tree.nodes.get("Image Texture")
		imagetex.image = image
		return mat
	except:
		mat = bpy.data.materials.new(matname)
		mat.use_nodes = True
		nodes = mat.node_tree.nodes
		diffuse = nodes.get("Diffuse BSDF")
		node_texture = nodes.new(type="ShaderNodeTexImage")
		node_texture.image = image
		links = mat.node_tree.links
		links.new(node_texture.outputs[0], diffuse.inputs[0])
		projectedUV = FindOrCreateProjUVGroup()
		group_instance = nodes.new(type="ShaderNodeGroup")
		group_instance.node_tree = projectedUV

		links.new(group_instance.outputs[0], node_texture.inputs[0])
		return mat

def projectUVs(obj, objToViewMatrix, projectionMatrix):
	print("About to perform back projection on "+obj.name)
	if isinstance(obj.data, Mesh):
		#first, ensure we have the required UV channel
		ensureUVChannels(obj)
		try:
			uvproj = obj.modifiers['UVProject']
			print("Disabling UV projection modifier as projection UV values are being written directly")
			uvproj.show_render = False
			uvproj.show_viewport = False
			uvproj.show_in_editmode = False
		except:
			print("No projection modifier active, no need to disable.")

		#MVP = objmat * view * proj.transposed()
		#projected_vertices = [p.co * MVP for p in ob.data.vertices]
		bmesh = startMeshUpdate(obj)
		uv_layer = bmesh.loops.layers.uv['ProjUV']
		uvw_layer = bmesh.loops.layers.uv['ProjUVZW']
		uvdivw_layer = bmesh.loops.layers.uv['ProjUVdivW']
		fidx = 0
		#fcount = len(bmesh.faces)
		for f in bmesh.faces:
			vidx = 0
			#vcount = len(f.loops)
			for l in f.loops:
				luv = l[uv_layer]
				uvw = l[uvw_layer]
				luvdivw = l[uvdivw_layer]
				#if luv.select:
				# apply the location of the vertex as a UV
				p = l.vert.co * objToViewMatrix

				#print("Processing vertex %i/%i of poly %i/%i : " % (vidx, vcount, fidx, fcount)+ str(p))
				vres = Vector([p.x, p.y, p.z, 0.0]) * projectionMatrix
				w = vres.w if vres.w != 0.0 else 1.0
				luvdivw.uv = vres.xy / w
				luv.uv = vres.xy
				uvw.uv = (vres.z, w)
				vidx = vidx + 1
			++fidx
		endMeshUpdate(obj, bmesh)
	else:
		print(str(obj) + " is not a mesh object")


def offsetUVs(obj, camera, useBounds, TextureAtlasNode):
	bmesh = startMeshUpdate(obj)
	uvoffset_chan = bmesh.loops.layers.uv['UVOffset']
	bounds = getScreenSpaceBoundsNoScale(obl, camera, useBounds)
	area = TextureAtlasNode.area
	uvoffset = (-bounds[0][0] + area[0][0], -bounds[0][1] + area[0][1])
	#although this is a single value, for now there is no way of doing per object instance shader properties
	for f in bmesh.faces:
		for l in f.loops:
			luvoffset = l[uvoffset_chan]
			luvoffset.uv = uvoffset

	endMeshUpdate(obj, bmesh)

def performBackProjectionOnObjectActiveView(obj):
	MVP = getActiveViewMVP(obj)
	projectUVs(obj, MVP)


def performBackProjectionOnObject(obj, camera, uvoffset = [0.5, 0.5, 0.0], scale = [0.5, 0.5, 1.0], aspect=[1, 1]):
	print("About to apply uvs with offset:%f,%f and scale: %f,%f and aspect ratios (?)%f %f\n" % (uvoffset[0], uvoffset[1], scale[0], scale[1], aspect[0], aspect[1]))
	Projection = projectionMatrix(camera.data, scale, uvoffset, aspect)
	ObjToView =  (bpy.context.scene.camera.matrix_world.inverted() * obj.matrix_world).transposed()
	projectUVs(obj, ObjToView, Projection)

def ApplyBackProjectionToObject(obj, camera, useModifier = True,  layer= LAYER_BACKGROUND):
	if isinstance(obj.data, bpy_types.Mesh):
		ensureUVChannels(obj)
		if useModifier:
			image = EnsureImage(layer)
			ar = 1.0 if image is None and image.size[0] != 0 else image.size[1] / image.size[0]

			print("Using modifier on " + obj.name)
			try:
				uvproj = obj.modifiers['UVProject']
			except:
				uvproj = obj.modifiers.new("UVProject", 'UV_PROJECT')
			uvproj.use_image_override = True
			if camera is None:
				camera = bpy.data.cameras[0]
			uvproj.show_render = True
			uvproj.show_viewport = True
			uvproj.show_in_editmode = True
			uvproj.projectors[0].object = camera
			uvproj.image = image
			uvproj.scale_x = 1.0
			uvproj.scale_y = ar
			uvproj.uv_layer = 'ProjUVDivW'  # save in predivided UV channel
		else:
			print("Baking UVs on " + obj.name)

			offset = [0.5, 0.5, 0.0]
			try:
				offset = bpy.context.scene['Offset']
			except:
				pass
			scale = [0.5, 0.5, 0.0]
			try:
				scale = bpy.context.scene['Scale']
			except:
				pass
			aspect = [1, 1, 1]
			try:
				aspect = bpy.context.scene['Aspect']
			except:
				pass

			performBackProjectionOnObject(obj, camera, offset, scale, aspect)
			print("Finished baking UVs")

#more to remind myself about bpy.context.active_object
def ApplyBackProjectionToCurrent(camera):
	ApplyBackProjectionToObject(bpy.context.active_object, camera)

def ApplyBackProjectionTo(camera, usemodifier, func,  layer= LAYER_BACKGROUND):
	i = 0
	count =  len(bpy.data.objects)
	for ob in bpy.data.objects:
		print("Object name:" + ob.name)

	for ob in bpy.data.objects:
		print("Processing object %i of %i" % (i, count))
		if isinstance(ob.data, Mesh) and func(ob):
			ApplyBackProjectionToObject(ob, camera, usemodifier, layer)
		print("Finished processing object %i of %i (%s)" % (i, count, ob.name))
		i = i + 1
	print("Finished processing objects")


def ApplyBackProjectionToSelected(camera, usemodifier, layer = LAYER_BACKGROUND):
	ApplyBackProjectionTo(camera, usemodifier, lambda ob: ob.select, layer)


#
#    Store properties in the active scene
#
def initSceneProperties():
	print("Initialising properties")
	bpy.types.Scene.MyInt = bpy.props.IntProperty(
		name = "Integer",
		description = "Enter an integer")

	bpy.types.Scene.MyFloat = bpy.props.FloatProperty(
		name = "Float",
		description = "Enter a float",
		default = 33.33,
		min = -100,
		max = 100)

	bpy.types.Scene.Scale = bpy.props.FloatVectorProperty(
		name = "Scale",
		description = "Scale Value",
		subtype="TRANSLATION",
		default = (0.5, 0.5, 1.0),
		min = 0.001,
		max = 2.0)

	bpy.types.Scene.Offset = bpy.props.FloatVectorProperty(
		name = "Offset",
		description = "Offset",
		subtype="TRANSLATION",
		default = (0.5, 0.5, 0.0),
		min = -1.0,
		max = 1.0)

	bpy.types.Scene.Aspect = bpy.props.FloatVectorProperty(
		name = "Aspect",
		description = "Aspect",
		subtype="TRANSLATION",
		default = (1, 1, 1),
		min = -1.0,
		max = 1.0)

	bpy.types.Scene.MyBool = bpy.props.BoolProperty(
		name = "Boolean",
		description = "True or False?")

	bpy.types.Scene.MyEnum = EnumProperty(
		items = [('Eine', 'Un', 'One'),
				('Zwei', 'Deux', 'Two'),
				('Drei', 'Trois', 'Three')],
				name = "Ziffer")


	bpy.types.Scene.MyString = bpy.props.StringProperty(
		name = "String")
	return


class VIEW3D_PT_BackProjector(bpy.types.Panel):
	"""Overpainting tools"""
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'

	bl_category = "OverPaint"
	bl_label = "OverPaint"

	initSceneProperties()
	#def __init__(self):
	#	print("Initialising BackProjector")
	#

	def execute(self, context):
		if self.Initialised is False:
			print("initialising")
			self.Initialised = True
		return {'FINISHED'}


	def draw(self, context):
		global lastScale
		global lastOffset
		global count
		layout = self.layout
		scn = context.scene
		row = layout.row(align=True)
		row.alignment = 'LEFT'

		row.label(text="Back Projection:")

		split = layout.split()
		col = split.column(align=True)

		col = layout.column()
		row = col.row()
		row.operator("view3d.apply_back_projection", icon="MOD_UVPROJECT")
		row.operator("view3d.render_scene", icon="MOD_UVPROJECT")
		row = col.row()
		row.operator("view3d.apply_back_projection_no_mod", icon="MOD_UVPROJECT")

		row = col.row()
		row.operator("view3d.save_psd", icon="MOD_UVPROJECT")
		row.operator("view3d.save_fbx", icon="MOD_UVPROJECT")
		row = col.row()
		row.label(text="Rendered material preview:")
		row = col.row()
		row.operator("view3d.save_materials", icon="MOD_UVPROJECT")
		row = col.row()

		row.operator("view3d.set_preview_material", icon="MOD_UVPROJECT")
		row.operator("view3d.restore_source_material", icon="MOD_UVPROJECT")
		row = col.row()
		row.label(text="Render offsets:")
		row = col.row()
		row.prop(scn, 'Scale')
		row = col.row()
		row.prop(scn, 'Offset')
		row = col.row()
		row.prop(scn, 'Aspect')

		col.alignment = 'EXPAND'


def pre_save(dummy):
	print("Saving.. restoring original materials (can be lost by blender file optimisation)")
	RestoreSourceMaterials()



	#
		#ob = context.active_object
		#layout.prop_search(ob, "textureName", bpy.data, "images")

def register():
	bpy.utils.register_class(VIEW3D_PT_BackProjector)
	bpy.utils.register_class(ApplyBackProjection)
	bpy.utils.register_class(ApplyBackProjectionNoMod)
	bpy.utils.register_class(RenderScene)
	bpy.utils.register_class(CSavePSD)
	bpy.utils.register_class(CSaveFBX)
	bpy.utils.register_class(CSetPreviewMaterial)
	bpy.utils.register_class(CSaveMaterials)
	bpy.utils.register_class(CRestoreSourceMaterials)
	bpy.app.handlers.save_pre.append(pre_save)

def unregister():
	bpy.utils.unregister_class(VIEW3D_PT_BackProjector)
	bpy.utils.unregister_class(ApplyBackProjection)
	bpy.utils.unregister_class(ApplyBackProjectionNoMod)
	bpy.utils.unregister_class(RenderScene)
	bpy.utils.unregister_class(CSavePSD)
	bpy.utils.unregister_class(CSaveFBX)
	bpy.utils.unregister_class(CSetPreviewMaterial)
	bpy.utils.unregister_class(CSaveMaterials)
	bpy.utils.unregister_class(CRestoreSourceMaterials)
	bpy.app.handlers.save_pre.remove(pre_save)

if __name__ == "__main__":
	register()