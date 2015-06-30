import bpy
import sys
import os
from blendertools import *
import bpy_types
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



GlobalOldMaterials = {}

def SetPreviewMaterial(mat):
	global GLobalOldMaterials
	for ob in bpy.data.objects:
		if ob.select == True and isinstance(ob.data, Mesh):
			GLobalOldMaterials[ob] = ob.material_slots



def CreateProjectionMaterial(image):
	mat = bpy.data.materials.new("OverpaintMaterial_%s" % image.name)
	nodes = mat.node_tree.nodes

	# get some specific node:
	# returns None if the node does not exist
	diffuse = nodes.get("Diffuse BSDF")
	node_texture = nodes.new(type="ShaderNodeTexImage")	
	node_texture.image = image
	links = mat.node_tree.links
	link = links.new(node_texture.outputs[0], diffuse.inputs[0])



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
		uvproj.scale_x = 0.86
		uvproj.scale_y = 0.46
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


		col.alignment = 'EXPAND'
		
	#	row.operator("view3d.apply_back_projection", icon='MOD_UVPROJECT')
		#row.operator(STR_start_render_cmd,  icon='MOD_UVPROJECT')
		
		#row = col.row()
		row.label(text="Save:")        
		#row.operator(STR_save_psd_cmd, text=STR_save_psd, icon='EXPORT')
		#row.operator(STR_save_fbx_cmd, text=STR_save_fbx, icon='EXPORT')

		#ob = context.active_object
		#layout.prop_search(ob, "textureName", bpy.data, "images")

def register():
	bpy.utils.register_class(VIEW3D_PT_BackProjector)
	bpy.utils.register_class(ApplyBackProjection)
	bpy.utils.register_class(RenderScene)
	bpy.utils.register_class(SavePSD)
	bpy.utils.register_class(SaveFBX)

def unregister():
	bpy.utils.unregister_class(VIEW3D_PT_BackProjector)

	bpy.utils.unregister_class(ApplyBackProjection)
	bpy.utils.unregister_class(RenderScene)
	bpy.utils.unregister_class(SavePSD)
	bpy.utils.unregister_class(SaveFBX)

if __name__ == "__main__":
	register()