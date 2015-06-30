import bpy
import sys
import os
from blendertools import *
from bpy_types import *
import bpy_extras
from bpy.props import IntProperty, BoolProperty, FloatProperty, EnumProperty

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

pathBase = '/Users/Tim/Google Drive/OysterWorld/HOPA/BlenderOutput'



class ApplyBackProjection(bpy.types.Operator):
	bl_idname = "view3d.apply_back_projection"
	bl_label = "Apply back projection"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		print("About to apply back projection")
		ApplyBackProjectionToSelected(bpy.data.camera[0])
		return {'FINISHED'}

class RenderScene(bpy.types.Operator):
	bl_idname = "view3d.render_scene"
	bl_label = "Render Scene"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		print("About to render scene")				
		bpy.ops.render.render( write_still=True, layer="RenderLayer") 
		bpy.data.images['Render Result'].save_render("C:\\Users\\Tim\\Google Drive\\OysterWorld\\HOPA\\BlenderOutput\\layer0.png")
		bpy.ops.render.render( write_still=True, layer="Overlay") 
		bpy.data.images['Render Result'].save_render("C:\\Users\\Tim\\Google Drive\\OysterWorld\\HOPA\\BlenderOutput\\layer1.png")
		return {'FINISHED RENDER'}



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
	bl_label = "Save FBX"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		print("About to set preview material")
		mat = FindOrCreateProjectionMaterial("LivingRoom_NoTableStuff.png")
		SetPreviewMaterial(mat)
		return {'FINISHED'}



class CRestoreSourceMaterials(bpy.types.Operator):
	bl_idname = "view3d.restore_source_material"
	bl_label = "Save FBX"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		print("About to set preview material")		
		RestoreSourceMaterials()
		return {'FINISHED'}


def copylist(inlist)
	return [i in inlist]

GlobalOldMaterials = {}

def SetPreviewMaterial(mat):
	global GlobalOldMaterials
	for ob in bpy.data.objects:
		if ob.select == True and isinstance(ob.data, Mesh):
			GlobalOldMaterials[ob] = list(ob.data.materials)
			oldCount = len(ob.data.materials)
			ob.data.materials.clear()
			for i in range(oldCount):
				ob.data.materials.append(mat)


def RestoreSourceMaterials():
	global GlobalOldMaterials
	for ob in bpy.data.objects:
		if ob.select == True and isinstance(ob.data, Mesh):
			oldmaterials =  GlobalOldMaterials[ob]
			ob.data.materials.clear()			
			for mat in oldmaterials:
				ob.data.materials.append(mat)
	GlobalOldMaterials.clear()




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


def ApplyBackProjectionToObject(obj, camera):
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
		float ar = image.size[1] / image.size[0]
		uvproj.scale_x = 1.0
		uvproj.scale_y = ar
		uvproj.uv_layer='ProjUV'

#more to remind myself about bpy.context.active_object
def ApplyBackProjectionToCurrent(camera):
	ApplyBackProjectionToObject(bpy.context.active_object, camera)


def ApplyBackProjectionToSelected(camera):
	for ob in bpy.data.objects:
		if ob.select == True and isinstance(ob.data, Mesh):						
			ApplyBackProjectionToObject(ob, camera)



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