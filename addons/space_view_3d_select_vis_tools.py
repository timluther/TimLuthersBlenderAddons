
# space_view_3d_select_vis_tools.py Copyright (C) 2015, Tim Lewis
#
# Multiple display tools for fast navigate/interact with the viewport
#
# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

bl_info = {
	"name": "Selection visibility tools",
	"author": "Tim Lewis",
	"version": (0, 0, 4),
	"blender": (2, 7, 0),
	"location": "Toolshelf",
	"description": "Tools for toggling visibility, render visibility and selectability of selected objects",
	"warning": "",
	"wiki_url": "",
	"tracker_url": "",
	"category": "Selection"}

import bpy





from bpy.props import IntProperty, BoolProperty, FloatProperty, EnumProperty

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

def setlayermaskforallselected(layermask):
	scene = bpy.context.scene
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.layers = layermask

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



class ShowAllSelected(bpy.types.Operator):   #nb: CamelCase
	bl_idname = "view3d.show_all_selected" #nb underscore_case
	bl_label = "Show all"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		showselected()
		return {'FINISHED'}

class HideAllSelected(bpy.types.Operator):    
	bl_idname = "view3d.hide_all_selected"
	bl_label = "Hide all"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		hideselected()     
		return {'FINISHED'}

class ShowRenderAllSelected(bpy.types.Operator):   #nb: CamelCase
	bl_idname = "view3d.render_show_all_selected" #nb underscore_case
	bl_label = "Show all in render"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		rendershowselected()
		return {'FINISHED'}

class HideRenderAllSelected(bpy.types.Operator):    
	bl_idname = "view3d.render_hide_all_selected"
	bl_label = "Hide all in render"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		renderhideselected()     
		return {'FINISHED'}             

class ActivateAllSelected(bpy.types.Operator):   #nb: CamelCase
	bl_idname = "view3d.activate_all_selected" #nb underscore_case
	bl_label = "Activate all"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		activateselected()
		return {'FINISHED'}

class DeactivateAllSelected(bpy.types.Operator):    
	bl_idname = "view3d.deactivate_all_selected"
	bl_label = "Deactivate all"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		deactivateselected()     
		return {'FINISHED'}     

class EnableRigidBodyAllSelected(bpy.types.Operator):   #nb: CamelCase
	bl_idname = "view3d.enable_rigid_body_all_selected" #nb underscore_case
	bl_label = "Enable rigid bodies"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		enablerigidbodyonselected()
		return {'FINISHED'}

class DisableRigidBodyAllSelected(bpy.types.Operator):    
	bl_idname = "view3d.disable_rigid_body_all_selected"
	bl_label = "Disable rigid bodies"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
		 
	def execute(self, context):
		disablerigidbodyonselected()     
		return {'FINISHED'}   
	
#SelectionHelp
class SelectionHelp(bpy.types.Operator):
	"""Operator that runs Fast navigate in modal mode"""
	bl_idname = "view3d.fast_navigate_operator"
	bl_label = "Fast Navigate"
	trigger = BoolProperty(default = False)
	mode = BoolProperty(default = False)
	 
	def execute(self, context):        
		a = 10

class AddLocationKeyframes(bpy.types.Operator):
	bl_idname= "view3d.add_location_keyframes"
	bl_label="location"
	def execute(self,context):
		addselectedobjectskeyframes("location")
 
class AddVisibilityKeyframes(bpy.types.Operator):
	bl_idname= "view3d.add_visibility_keyframes"
	bl_label="visibility"
	def execute(self,context):
		addselectedobjectskeyframes("hide")
		return {'FINISHED'}   



class AddRenderVisibilityKeyframes(bpy.types.Operator):
	bl_idname= "view3d.add_render_visibility_keyframes"
	bl_label="Render visibility"
	def execute(self,context):
		addselectedobjectskeyframes("hide_render")
		return {'FINISHED'}   



class AddActiveStatusKeyframes(bpy.types.Operator):
	bl_idname= "view3d.add_active_status_keyframes"
	bl_label="Selection active"
	def execute(self,context):
		addselectedobjectskeyframes("hide_select")
		return {'FINISHED'}   



class AddRigidBodyEnableKeyframes(bpy.types.Operator):
	bl_idname= "view3d.add_rigid_body_enable_keyframes"
	bl_label="Rigid body enabled"
	def execute(self,context):
		addselectedobjectsrigidbodykeyframes("enabled")
		return {'FINISHED'}   


	

bpy.types.Scene.TestProp1 = bpy.props.BoolProperty(
		default = True,
		description = "Activate for fast navigate in edit mode too")

bpy.types.Scene.TestNumericProperty = bpy.props.IntProperty(
		default = 30,
		min = 1,
		max = 500,
		soft_min = 10,
		soft_max = 250,
		description = "testing")

bpy.types.Scene.TestEnum = bpy.props.EnumProperty(
		items = [('Item1', 'Item1', 'The first item'), 
			('Item2', 'Item2', 'The second item'),
			], 
		name = "TestEnum")
	
class VIEW3D_PT_SelectionHelp(bpy.types.Panel):
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_category = "Selection"
	bl_label = "Selection"
	#bl_options = {'DEFAULT_CLOSED'}
	
	def draw(self, context):
		layout = self.layout
		
		# Tools   
		scene = context.scene
		row = layout.row(align=True)
		row.alignment = 'LEFT'
		row.operator("selection.fast_navigate_operator", icon ='TEXTURE_SHADED')
		
		layout.label(" For all selected objects:")
		row = layout.row()
		#
		"""
		box.prop(scene,"TestEnum")
		box.prop(scene, "TestProp1", "Test Prop")
	  
		box.prop(scene, "TestNumericProperty", "TestValue")
		box.alignment = 'LEFT'
"""
		# Tools
		col = layout.column()       
		col.alignment = 'EXPAND'
		
		row.operator("view3d.show_all_selected" , icon ='RESTRICT_VIEW_OFF')
		row.operator("view3d.hide_all_selected" , icon ='RESTRICT_VIEW_ON')       
		row = col.row()
		row.operator("view3d.render_show_all_selected", icon='RESTRICT_VIEW_OFF')
		row.operator("view3d.render_hide_all_selected", icon='RESTRICT_VIEW_OFF')
		row = col.row()
		row.operator("view3d.activate_all_selected", icon='RESTRICT_VIEW_OFF')
		row.operator("view3d.deactivate_all_selected", icon='RESTRICT_VIEW_OFF')
		row = col.row()
		row.operator("view3d.enable_rigid_body_all_selected", icon='RESTRICT_VIEW_OFF')
		row.operator("view3d.disable_rigid_body_all_selected", icon='RESTRICT_VIEW_OFF')
		row = col.row()                

class VIEW3D_PT_KeyframeHelp(bpy.types.Panel):
	bl_space_type = "VIEW_3D"
	bl_region_type = "TOOLS"
	bl_category = "Selection"
	bl_label = "Keyframes"
	#bl_options = {'DEFAULT_CLOSED'}
	
	def draw(self, context):
		layout = self.layout
		
		# Tools   
		scene = context.scene
		row = layout.row(align=True)
		row.alignment = 'LEFT'
		row.operator("selection.fast_navigate_operator", icon ='TEXTURE_SHADED')
		
		layout.label("Add the following properties as keyframe for selected objects:")
		row = layout.row()
		#
		"""
		box.prop(scene,"TestEnum")
		box.prop(scene, "TestProp1", "Test Prop")
	  
		box.prop(scene, "TestNumericProperty", "TestValue")
		box.alignment = 'LEFT'
"""
		# Tools
		col = layout.column()       
		col.alignment = 'EXPAND'
		row = col.row()
		row.operator("view3d.add_location_keyframes" , icon ='RESTRICT_VIEW_OFF')
		row = col.row()
		row.operator("view3d.add_visibility_keyframes" , icon ='RESTRICT_VIEW_OFF')
		row.operator("view3d.add_render_visibility_keyframes" , icon ='RESTRICT_VIEW_OFF')
		row = col.row()
		row.operator("view3d.add_active_status_keyframes" , icon ='RESTRICT_VIEW_OFF')
		row.operator("view3d.add_rigid_body_enable_keyframes" , icon ='RESTRICT_VIEW_OFF')


class HelloWorldPanel(bpy.types.Panel):
	bl_idname = "OBJECT_PT_hello_world"
	bl_label = "Hello World"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "object"

	def draw(self, context):
		self.layout.label(text="Hello World")


# register the classes
def register():
	
	bpy.utils.register_class(VIEW3D_PT_KeyframeHelp)
	bpy.utils.register_class(VIEW3D_PT_SelectionHelp)    
	bpy.utils.register_class(AddLocationKeyframes)
	bpy.utils.register_class(AddVisibilityKeyframes)
	bpy.utils.register_class(AddRenderVisibilityKeyframes)
	bpy.utils.register_class(AddActiveStatusKeyframes)
	bpy.utils.register_class(AddRigidBodyEnableKeyframes)
	bpy.utils.register_module(__name__) 
	pass 

def unregister():
	bpy.utils.unregister_class(VIEW3D_PT_SelectionHelp)
	bpy.utils.unregister_class(VIEW3D_PT_KeyframeHelp)
	bpy.utils.unregister_module(__name__)
	pass 

if __name__ == "__main__": 
	register() 