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

class BackProjector(bpy.types.Panel):
    """A Custom Panel in the Viewport Toolbar"""
    bl_label = "Custom Panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.label(text="Add Objects:")

        split = layout.split()
        col = split.column(align=True)

        col.operator("mesh.primitive_plane_add", text="Plane", icon='MESH_PLANE')
        col.operator("mesh.primitive_torus_add", text="Torus", icon='MESH_TORUS')

def register():
    bpy.utils.register_class(BackProjector)

def unregister():
    bpy.utils.unregister_class(BackProjector)

if __name__ == "__main__":
    register()