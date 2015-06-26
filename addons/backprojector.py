import bpy
import sys
import os
sys.path.append(os.path.dirname(__file__)) #hack to make sure we can access modules on the same path as this file
import blendertools

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
    "category": "Projection"}


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

#more to remind myself about bpy.context.active_object
def ApplyBackProjectionToCurrent(camera):
    ApplyBackProjection(bpy.context.active_object, camera)


def applyBackProjectionToSelected(camera):
    for ob in bpy.data.objects:
        if ob.select == True:
            ApplyBackProjection(ob, camera)


class CApplyBackProjection(bpy.types.Operator):   #nb: CamelCase
    bl_idname = "view3d.apply_back_projection" #nb underscore_case
    bl_label = "Apply Back Projection"
    trigger = BoolProperty(default = False)
    mode = BoolProperty(default = False)
         
    def execute(self, context):
        applyBackProjectionToSelected(bpy.data.camera[0])
        return {'FINISHED'}

class CStartBackProjectionRender(bpy.types.Operator):   #nb: CamelCase
    bl_idname = "view3d.start_back_projection_render" #nb underscore_case
    bl_label = "Start back projection render"
    trigger = BoolProperty(default = False)
    mode = BoolProperty(default = False)
         
    def execute(self, context):        
        return {'FINISHED'}

class CSavePSD(bpy.types.Operator):   #nb: CamelCase
    bl_idname = "view3d.save_psd" #nb underscore_case
    bl_label = "Start back projection render"
    trigger = BoolProperty(default = False)
    mode = BoolProperty(default = False)
         
    def execute(self, context):        
        return {'FINISHED'}

class CSaveFBX(bpy.types.Operator):   #nb: CamelCase
    bl_idname = "view3d.save_fbx" #nb underscore_case
    bl_label = "Start back projection render"
    trigger = BoolProperty(default = False)
    mode = BoolProperty(default = False)
         
    def execute(self, context):        
        return {'FINISHED'}



class BackProjector(bpy.types.Panel):
    """Back projection tools"""
    bl_label = "Custom Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Add Objects:")

        split = layout.split()
        col = split.column(align=True)

        col.operator("view3d.apply_back_projection", text="Apply modifiers", icon='MOD_UVPROJECT')
        col.operator("view3d.start_back_projection_render", text="Start render", icon='RENDER_STILL')
        col.operator("view3d.save_psd", text="Save PSD", icon='EXPORT')
        col.operator("view3d.save_fbx", text="Save FBX", icon='EXPORT')

def register():
    bpy.utils.register_class(BackProjector)

def unregister():
    bpy.utils.unregister_class(BackProjector)

if __name__ == "__main__":
    register()