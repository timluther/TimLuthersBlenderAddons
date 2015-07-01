import bpy
import sys
import os
from blendertools import *
from bpy_types import *
import bpy_extras
import json
from bpy.props import IntProperty, BoolProperty, FloatProperty, EnumProperty
import csv

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

pathBase = '/tmp/'


LAYER_BACKGROUND = 0
LAYER_POPPED_OUT = 1
LAYER_PICKUP     = 2

layer_names = ["background", "popped_out", "picked_up"]

#Recreate camera matrix b/c blender doesn't give it to you
#thanks to Goran Milovanovic for doing the legwork
#http://blender.stackexchange.com/questions/16472/how-can-i-get-the-cameras-projection-matrix
def viewPlane(camd, winx, winy, xasp, yasp):    
	#/* fields rendering */
	ycor = yasp / xasp
	use_fields = False
	if (use_fields):
	  ycor *= 2

	def BKE_camera_sensor_size(p_sensor_fit, sensor_x, sensor_y):
		#/* sensor size used to fit to. for auto, sensor_x is both x and y. */
		if (p_sensor_fit == 'VERTICAL'):
			return sensor_y;

		return sensor_x;

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

	if (sensor_fit == 'HORIZONTAL'):
	  viewfac = winx
	else:
	  viewfac = ycor * winy

	pixsize /= viewfac

	#/* extra zoom factor */
	pixsize *= 1 #params->zoom

	#/* compute view plane:
	# * fully centered, zbuffer fills in jittered between -.5 and +.5 */
	xmin = -0.5 * winx
	ymin = -0.5 * ycor * winy
	xmax =  0.5 * winx
	ymax =  0.5 * ycor * winy

	#/* lens shift and offset */
	dx = camd.shift_x * viewfac # + winx * params->offsetx
	dy = camd.shift_y * viewfac # + winy * params->offsety

	xmin += dx
	ymin += dy
	xmax += dx
	ymax += dy

	#/* fields offset */
	#if (params->field_second):
	#    if (params->field_odd):
	#        ymin -= 0.5 * ycor
	#        ymax -= 0.5 * ycor
	#    else:
	#        ymin += 0.5 * ycor
	#        ymax += 0.5 * ycor

	#/* the window matrix is used for clipping, and not changed during OSA steps */
	#/* using an offset of +0.5 here would give clip errors on edges */
	xmin *= pixsize
	xmax *= pixsize
	ymin *= pixsize
	ymax *= pixsize

	return xmin, xmax, ymin, ymax


def projectionMatrix(camd):
	r = bpy.context.scene.render
	left, right, bottom, top = viewPlane(camd, r.resolution_x, r.resolution_y, 1, 1)

	farClip, nearClip = camd.clip_end, camd.clip_start

	Xdelta = right - left
	Ydelta = top - bottom
	Zdelta = farClip - nearClip

	return Matrix([[nearClip * 2 / Xdelta, 0, 0, 0],
				  [0, nearClip * 2 / Ydelta, 0, 0],
				  [(right + left) / Xdelta, (top + bottom) / Ydelta, (farClip + nearClip) / Zdelta, -1 ],
				  [0, 0, (-2 * nearClip * farClip) / Zdelta ,1]])	


def projectionMatrix2(camd):
	r = bpy.context.scene.render
	left, right, bottom, top = viewPlane(camd, r.resolution_x, r.resolution_y, 1, 1)

	farClip, nearClip = camd.clip_end, camd.clip_start

	Xdelta = right - left
	Ydelta = top - bottom
	Zdelta = farClip - nearClip

	return Matrix([[nearClip * 2 / Xdelta, 0, (right + left) / Xdelta, 0],
					[0, nearClip * 2 / Ydelta, (top + bottom) / Ydelta,0 ],
					[0, 0,  (farClip + nearClip) / Zdelta, (-2 * nearClip * farClip) / Zdelta ],
					[0,0,-1,1]])

def getCamMat(cam, scale = 0.5):
	scalemat = Matrix.Scale(scale, 4)
	transmat = Matrix.Translation([0.5, 0.5, 0.0])
	projmat = projectionMatrix(cam.data)
	return  cam.matrix_world * projmat * scalemat.transposed() * transmat.transposed()


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

#for a given object and camera, return the MVP. This should be an exact match to the UV projection
#modifier (not quite, at time of writing: some scaling is off, possibly something to do with image scale?)
def getMVP(obj, cam, scale = 0.5):
	scalemat = Matrix.Scale(scale, 4)
	transmat = Matrix.Translation([0.5, 0.5, 0.0])
	projmat = projectionMatrix(cam.data)
	cam_matrix = cam.matrix_world
	#cam_matrix = cam.matrix_world
	#cam_matrix_cheeky_translate = Matrix.Translation(cam_matrix.translation).transposed()
	#cam_matrix = cam.matrix_world.to_3x3().to_4x4() #* cam_matrix_cheeky_translate
	#return obj.matrix_world.transposed() * cam_matrix * projmat * scalemat.transposed() * transmat.transposed()
	

	#return scalemat * transmat
	return projmat * scalemat.transposed() * transmat.transposed()
	

	#return transmat * scalemat * projmat.inverted()
	#return (obj.matrix_world * cam_matrix * projmat * scalemat * transmat).transposed()
	#return  scalemat *transmat* projmat.inverted() * cam_matrix * obj.matrix_world

def getActiveViewMVP(obj):
	projmat = getActiveViewMatrix()	
	return obj.matrix_world.transposed() * projmat

def getLayerFilename(layer):
	return os.path.join(pathBase, layer_names[layer] + ".png")

def EnsureImage(layer):
	layer_name = layer_names[layer]+".png"
	try:
		image = bpy.data.images[layer_name]
	except:
		scene = bpy.context.scene
		image = bpy.data.images.new(layer_name, scene.render.resolution_x, scene.render.resolution_y)		
		image.filepath = getLayerFilename(layer)
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

class RenderScene(bpy.types.Operator):
	bl_idname = "view3d.render_scene"
	bl_label = "Render Scene"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		print("About to render scene")		
		RestoreSourceMaterials()
		ApplyBackProjectionTo(bpy.context.scene.camera, False, lambda ob: True)
	
		image = EnsureImage(LAYER_BACKGROUND)
		image.filepath = getLayerFilename(LAYER_BACKGROUND)
		filename = getLayerFilename(LAYER_BACKGROUND)
		bpy.ops.render.render( write_still=True, layer="RenderLayer") 

		bpy.data.images['Render Result'].save_render(filename)
		image.reload()

		mat = FindOrCreateProjectionMaterial(image)
		SetPreviewMaterial(mat)

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



class CSetPreviewMaterial(bpy.types.Operator):
	bl_idname = "view3d.set_preview_material"
	bl_label = "Set Preview Material"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		print("About to set preview material")

		image = EnsureImage(LAYER_BACKGROUND)	
		mat = FindOrCreateProjectionMaterial(image)
		SetPreviewMaterial(mat)
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

def GetSceneMaterialFilename(scenename):	
	return os.path.join(os.getenv("HOME"), scenename + "_materials.csv")

def SceneMaterialsToMap():	
	materialdb = {}
	for ob in bpy.data.objects:
		if isinstance(ob.data, Mesh):
			materialdb[ob.name] = [i.name for i in ob.data.materials]
	return materialdb 

def SerialiseMaterials():
	MaterialMap = SceneMaterialsToMap()
	s = open(GetSceneMaterialFilename(bpy.context.scene.name), "w")
	json.dump(MaterialMap, s)
	s.close()	

def LoadMaterials():
	return json.load(open(GetSceneMaterialFilename(bpy.context.scene.name), "r"))	


def SetPreviewMaterial(mat):
	RestoreSourceMaterials() #make sure we're not saving the wrong ones	
	SerialiseMaterials() #save current materials off to json file
	for ob in bpy.data.objects:
		if isinstance(ob.data, Mesh):
			oldCount = len(ob.data.materials)
			ob.data.materials.clear()
			for i in range(oldCount):
				ob.data.materials.append(mat)


def RestoreSourceMaterials():
	GlobalOldMaterials = LoadMaterials() #retrieve current materials from json file
	for ob in bpy.data.objects:
		if isinstance(ob.data, Mesh):
			try:
				oldmaterials =  GlobalOldMaterials[ob.name]
				ob.data.materials.clear()			
				for mat in oldmaterials:
					ob.data.materials.append(bpy.data.materials[mat])
			except:
				print("Old scene not found")
	GlobalOldMaterials.clear()


def ensureUVChannels(obj):
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
	
		
	return uvchan, zwchan, uvchandivw

def FindOrCreateProjectionMaterial(image):
	matname = "OverpaintMaterial_%s" % image.name
	try:
		mat = bpy.data.materials[matname]
		return mat
	except:
		mat = bpy.data.materials.new(matname)
		mat.use_nodes = True
		nodes = mat.node_tree.nodes
		diffuse = nodes.get("Diffuse BSDF")
		node_texture = nodes.new(type="ShaderNodeTexImage")	
		node_texture.image = image
		links = mat.node_tree.links
		link = links.new(node_texture.outputs[0], diffuse.inputs[0])
		node_attribute = nodes.new(type="ShaderNodeAttribute")
		node_attribute.attribute_name="ProjUV"
		link = links.new(node_attribute.outputs[1], node_texture.inputs[0])
		return mat



def projectUVs(obj, matrix):
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
		for f in bmesh.faces:
			for l in f.loops:
				luv = l[uv_layer]
				uvw = l[uvw_layer]
				luvdivw = l[uvdivw_layer]
				
				#if luv.select:
					# apply the location of the vertex as a UV
				p = l.vert.co
				vres = Vector([p.x, p.y, p.z, 1.0]) * matrix
				
				w = vres.w if vres.w != 0.0 else 1.0 				
				luvdivw.uv = vres.xy / w								
				luv.uv = vres.xy
				uvw.uv = [vres.z, w]

		endMeshUpdate(obj, bmesh)
	else:
		print(str(obj) + " is not a mesh object")

def performBackProjectionOnObjectActiveView(obj):
	MVP = getActiveViewMVP(obj)
	projectUVs(obj, MVP)


def performBackProjectionOnObject(obj, camera, uvoffset = [0,0], scale = 0.5,imageSize=[1024,1024]):
	MVP = getMVP( obj, camera, scale)
	projectUVs(obj, MVP)
 

def ApplyBackProjectionToObject(obj, camera, useModifier = True):
	if isinstance(obj.data, bpy_types.Mesh):        
		print("got here")
		me = obj.data
		scene = bpy.context.scene
		ensureUVChannels(obj)
		image = EnsureImage(LAYER_BACKGROUND)			
		ar = 1.0 if image == None else image.size[1] / image.size[0]

		if useModifier:
			print("Using modifier on " + obj.name)
			try:
				uvproj = obj.modifiers['UVProject']
			except :        
				uvproj = obj.modifiers.new("UVProject", 'UV_PROJECT')
			uvproj.use_image_override = True
			if camera == None:
				camera = bpy.data.cameras[0]
			uvproj.show_render = True
			uvproj.show_viewport = True
			uvproj.show_in_editmode = True
			uvproj.projectors[0].object = camera			
			uvproj.image = image						
			uvproj.scale_x = 1.0
			uvproj.scale_y = ar
			uvproj.uv_layer='ProjUV'
		else:
			print("Baking UVs on " + obj.name)
			performBackProjectionOnObject(obj, camera, [0,0], 0.5, image.size)




#more to remind myself about bpy.context.active_object
def ApplyBackProjectionToCurrent(camera):
	ApplyBackProjectionToObject(bpy.context.active_object, camera)

def ApplyBackProjectionTo(camera, usemodifier, func):
	for ob in bpy.data.objects:
		if func(ob) and isinstance(ob.data, Mesh):						
			ApplyBackProjectionToObject(ob, camera, usemodifier)


def ApplyBackProjectionToSelected(camera, usemodifier):
	ApplyBackProjectionTo(camera, usemodifier, lambda ob: ob.select)


class VIEW3D_PT_BackProjector(bpy.types.Panel):
	"""Overpainting tools"""	
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'TOOLS'

	bl_category = "OverPaint"
	bl_label = "OverPaint"

	def draw(self, context):
		layout = self.layout

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
		row.operator("view3d.save_psd", icon="MOD_UVPROJECT")
		row.operator("view3d.save_fbx", icon="MOD_UVPROJECT")
		row = col.row()    
		row.label(text="Rendered material preview:")
		row = col.row()    
		split = layout.split()
		row.operator("view3d.set_preview_material", icon="MOD_UVPROJECT")
		row.operator("view3d.restore_source_material", icon="MOD_UVPROJECT")


		col.alignment = 'EXPAND'
		
	#	
		#ob = context.active_object
		#layout.prop_search(ob, "textureName", bpy.data, "images")

def register():
	bpy.utils.register_class(VIEW3D_PT_BackProjector)
	bpy.utils.register_class(ApplyBackProjection)
	bpy.utils.register_class(RenderScene)
	bpy.utils.register_class(CSavePSD)
	bpy.utils.register_class(CSaveFBX)
	bpy.utils.register_class(CSetPreviewMaterial)
	bpy.utils.register_class(CRestoreSourceMaterials)

def unregister():
	bpy.utils.unregister_class(VIEW3D_PT_BackProjector)

	bpy.utils.unregister_class(ApplyBackProjection)
	bpy.utils.unregister_class(RenderScene)
	bpy.utils.unregister_class(CSavePSD)
	bpy.utils.unregister_class(CSaveFBX)
	bpy.utils.unregister_class(CSetPreviewMaterial)
	bpy.utils.unregister_class(CRestoreSourceMaterials)

if __name__ == "__main__":
	register()