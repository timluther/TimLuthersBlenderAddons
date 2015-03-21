# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# <pep8 compliant>
# Clayworks export - based on obj exporter included with Blender

import os
import time
import struct
import bpy
import mathutils
import bpy_extras.io_utils
import math

class C3DInstance(object):
    def __init__(self, name, p, o, s, mesh_id):
        super(C3DInstance, self).__init__()
        self.name = name
        self.position = p
        self.orientation = o
        self.scale = s
        self.mesh_id = mesh_id

class ClassName(object):
    """docstring for ClassName"""
    def __init__(self, arg):
        super(ClassName, self).__init__()
        self.arg = arg
        
def footastic():
    doc = "The footastic property."
    def fget(self):
        return self._footastic
    def fset(self, value):
        self._footastic = value
    def fdel(self):
        del self._footastic
    return locals()
footastic = property(**footastic())


def make_hash(hashname):
    hash = 0x811c9dc5
    for c in hashname:
        hash *= 0x01000193
        hash ^= ord(c)
    return hash & 0xFFFFFFFF


def name_compat(name):
    if name is None:
        return 'None'
    else:
        return name.replace(' ', '_')

lightmap_material_texture = 'lightmap.png'
LIGHTMAP_MATERIAL_TEXTURE_HASH = make_hash(lightmap_material_texture)
lightmap_material = 'lightmap_material'
HASH_LIGHTMAP_MATERIAL = make_hash(lightmap_material)
    
#http://www.blender.org/documentation/blender_python_api_2_65_8/bpy.types.Material.html?highlight=material#bpy.types.Material.diffuse_shader
def write_mtl(fw, scene, copy_set, mtl_dict):
    from mathutils import Color

    world = scene.world
    if world:
        world_amb = world.ambient_color
    else:
        world_amb = Color((0.0, 0.0, 0.0))

    #source_dir = os.path.dirname(bpy.data.filepath)
    #dest_dir = os.path.dirname(filepath)

    #file = open(filepath, "w", encoding="utf8", newline="\n")
    #fw = file.write

    #fw('# Blender MTL File: %r\n' % (os.path.basename(bpy.data.filepath) or "None"))
    #fw('# Material Count: %i\n' % len(mtl_dict))

    mtl_dict_values = list(mtl_dict.values())
    mtl_dict_values.sort(key=lambda m: m[0])

    # Write material/image combinations we have used.
    # Using mtl_dict.values() directly gives un-predictable order.
    #

    fw('    <CNodeGroup name=\'Textures\'>\n')
    fw('        <CTexture name=\'%s\' id=\'%i\' src=\'%s\' />\n' % (lightmap_material_texture, LIGHTMAP_MATERIAL_TEXTURE_HASH, lightmap_material_texture) )
    fw('    </CNodeGroup>\n')
 
    fw('    <CNodeGroup name=\'Materials\' id=\'555555\' >\n')
    fw('        <CDualTextureMaterial name=\'%s\' ' % lightmap_material)
    fw('id=\'%i\' ' % HASH_LIGHTMAP_MATERIAL)
    fw('texture1=\'%s\' />\n' % lightmap_material_texture)
 
    for mtl_mat_name, mat, face_img in mtl_dict_values:

        # Get the Blender data for the material and the image.
        # Having an image named None will make a bug, dont do it :)
        # Define a new material: matname_imgname
        fw('        <CFresnelLitMaterial name=\'%s\' ' % mtl_mat_name)
        fw('id=\'%i\' ' % make_hash(mtl_mat_name))
        fw('diffuse=\'argb(%.3f, %.3f, %.3f, %.3f)\' ' % (mat.diffuse_color[0], mat.diffuse_color[1], mat.diffuse_color[2], 1))

        #material_flags=''
        """
         diffuse='argb(1,1,1,1)'
         specular='argb(1,1,1,1)'
         specular_edge='argb(1,1,1,1)'
         specular_power='20'
         diffuse_texture='get_node_from_uid(652200255)'
         fresnel='1'
         fresnel_exp='1'
         shininess='1'
         min_shininess='0'
         max_shininess='1'
         blend_mode='BMset'
         uvgen='2147483647' />


        if mat:
            # convert from blenders spec to 0 - 1000 range.
            if mat.specular_shader == 'WARDISO':
                tspec = (0.4 - mat.specular_slope) / 0.0004
            else:
                tspec = (mat.specular_hardness - 1) * 1.9607843137254901
            fw('Ns %.6f\n' % tspec)
            del tspec

            fw('Ka %.6f %.6f %.6f\n' % (mat.ambient * world_amb)[:])  # Ambient, uses mirror colour,
            fw('Kd %.6f %.6f %.6f\n' % (mat.diffuse_intensity * mat.diffuse_color)[:])  # Diffuse
            fw('Ks %.6f %.6f %.6f\n' % (mat.specular_intensity * mat.specular_color)[:])  # Specular
            if hasattr(mat, "ior"):
                fw('Ni %.6f\n' % mat.ior)  # Refraction index
            else:
                fw('Ni %.6f\n' % 1.0)
            fw('d %.6f\n' % mat.alpha)  # Alpha (obj uses 'd' for dissolve)

            # 0 to disable lighting, 1 for ambient & diffuse only (specular color set to black), 2 for full lighting.
            if mat.use_shadeless:
                fw('illum 0\n')  # ignore lighting
            elif mat.specular_intensity == 0:
                fw('illum 1\n')  # no specular.
            else:
                fw('illum 2\n')  # light normaly

        else:
            #write a dummy material here?
            fw('Ns 0\n')
            fw('Ka %.6f %.6f %.6f\n' % world_amb[:])  # Ambient, uses mirror colour,
            fw('Kd 0.8 0.8 0.8\n')
            fw('Ks 0.8 0.8 0.8\n')
            fw('d 1\n')  # No alpha
            fw('illum 2\n')  # light normaly

        # Write images!
        if face_img:  # We have an image on the face!
            # write relative image path
            rel = bpy_extras.io_utils.path_reference(face_img.filepath, source_dir, dest_dir, path_mode, "", copy_set, face_img.library)
            fw('map_Kd %s\n' % rel)  # Diffuse mapping image

        if mat:  # No face image. if we havea material search for MTex image.
            image_map = {}
            # backwards so topmost are highest priority
            for mtex in reversed(mat.texture_slots):
                if mtex and mtex.texture.type == 'IMAGE':
                    image = mtex.texture.image
                    if image:
                        # texface overrides others
                        if mtex.use_map_color_diffuse and face_img is None:
                            image_map["map_Kd"] = image
                        if mtex.use_map_ambient:
                            image_map["map_Ka"] = image
                        if mtex.use_map_specular:
                            image_map["map_Ks"] = image
                        if mtex.use_map_alpha:
                            image_map["map_d"] = image
                        if mtex.use_map_translucency:
                            image_map["map_Tr"] = image
                        if mtex.use_map_normal:
                            image_map["map_Bump"] = image
                        if mtex.use_map_hardness:
                            image_map["map_Ns"] = image

            for key, image in image_map.items():
                filepath = bpy_extras.io_utils.path_reference(image.filepath, source_dir, dest_dir, path_mode, "", copy_set, image.library)
                fw('%s %s\n' % (key, repr(filepath)[1:-1]))
   """

        fw('/>\n')
    fw('    </CNodeGroup>\n')


def test_nurbs_compat(ob):
    if ob.type != 'CURVE':
        return False

    for nu in ob.data.splines:
        if nu.point_count_v == 1 and nu.type != 'BEZIER':  # not a surface and not bezier
            return True

    return False


def write_nurb(fw, ob, ob_mat):
    tot_verts = 0
    cu = ob.data

    # use negative indices
    for nu in cu.splines:
        if nu.type == 'POLY':
            DEG_ORDER_U = 1
        else:
            DEG_ORDER_U = nu.order_u - 1  # odd but tested to be correct

        if nu.type == 'BEZIER':
            print("\tWarning, bezier curve:", ob.name, "only poly and nurbs curves supported")
            continue

        if nu.point_count_v > 1:
            print("\tWarning, surface:", ob.name, "only poly and nurbs curves supported")
            continue

        if len(nu.points) <= DEG_ORDER_U:
            print("\tWarning, order_u is lower then vert count, skipping:", ob.name)
            continue

        pt_num = 0
        do_closed = nu.use_cyclic_u
        do_endpoints = (do_closed == 0) and nu.use_endpoint_u

        for pt in nu.points:
            fw('v %.6f %.6f %.6f\n' % (ob_mat * pt.co.to_3d())[:])
            pt_num += 1
        tot_verts += pt_num

        fw('g %s\n' % (name_compat(ob.name)))  # name_compat(ob.getData(1)) could use the data name too
        fw('cstype bspline\n')  # not ideal, hard coded
        fw('deg %d\n' % DEG_ORDER_U)  # not used for curves but most files have it still

        curve_ls = [-(i + 1) for i in range(pt_num)]

        # 'curv' keyword
        if do_closed:
            if DEG_ORDER_U == 1:
                pt_num += 1
                curve_ls.append(-1)
            else:
                pt_num += DEG_ORDER_U
                curve_ls = curve_ls + curve_ls[0:DEG_ORDER_U]
        fw('curv 0.0 1.0 %s\n' % (" ".join([str(i) for i in curve_ls])))  # Blender has no U and V values for the curve

        # 'parm' keyword
        tot_parm = (DEG_ORDER_U + 1) + pt_num
        tot_parm_div = float(tot_parm - 1)
        parm_ls = [(i / tot_parm_div) for i in range(tot_parm)]

        if do_endpoints:  # end points, force param
            for i in range(DEG_ORDER_U + 1):
                parm_ls[i] = 0.0
                parm_ls[-(1 + i)] = 1.0

        fw("parm u %s\n" % " ".join(["%.6f" % i for i in parm_ls]))

        fw('end\n')

    return tot_verts

"""
C struct
struct SCWBinHeader2
{
    UINT32 m_mesh_type;
    UINT32 m_ver;
    UINT32 m_vertex_format; 
    UINT32 m_vertex_count;
    UINT32 m_vertex_flags;   //contains the count of active channels in a channel based mesh
    UINT32 m_polygon_count;
};
"""

def write_binary_cw_file(filepath, me, materials, EXPORT_UV = True, EXPORT_KEEP_VERT_ORDER = True, EXPORT_POLYGROUPS = True, EXPORT_EDGES = False, EXPORT_NORMALS = True):
    fw = open(filepath, 'wb')
    if EXPORT_UV:
        faceuv = len(me.uv_textures) > 0
        if faceuv:
            uv_layer = me.tessface_uv_textures.active.data[:]
    else:
        faceuv = False

    #this is where we grab the faces - tessfaces are triangulated?
    # Make our own list so it can be sorted to reduce context switching
    face_index_pairs = [(face, index) for index, face in enumerate(me.tessfaces)]
    # faces = [ f for f in me.tessfaces ]
    # Sort by Material, then images
    # so we dont over context switch in the obj file.
    if EXPORT_KEEP_VERT_ORDER:
        pass
    elif faceuv:
        face_index_pairs.sort(key=lambda a: (a[0].material_index, hash(uv_layer[a[1]].image), a[0].use_smooth))
    elif len(materials) > 1:
        face_index_pairs.sort(key=lambda a: (a[0].material_index, a[0].use_smooth))
    else:
        # no materials
        face_index_pairs.sort(key=lambda a: a[0].use_smooth)
    # Set the default mat to no material and no image.
    contextMat = 0, 0  # Can never be this, so we will label a new material the first chance we get.
    contextSmooth = None  # Will either be true or false,  set bad to force initialization switch.

    me_verts = me.vertices[:]
    edge_count = len(me.loops)
    vertex_count = len(me_verts)

    if EXPORT_EDGES:
        edges = me.edges
    else:
        edges = []

    if not (len(face_index_pairs) + len(edges) + len(me.vertices)):  # Make sure there is somthing to write

        # clean up
        bpy.data.meshes.remove(me)
        return # dont bother with this mesh.        

    if EXPORT_NORMALS and face_index_pairs:
        me.calc_normals()
    print("Writing Clayworks binary mesh: %s \n " % filepath )
    ID_header = bytes('CWBN', 'UTF-8')
    ID_merged_vertices = bytes('FTAL', 'UTF-8') #merged vertices
    ID_vertex_channels = bytes('CWCB', 'UTF-8')
    ID_scene_id = bytes('CWSN', 'UTF-8')
    ID_VC_EDGE_PER_VERTEX = 0x7FFF0000
    fw.write(ID_header)          #CWBN
    fw.write(ID_vertex_channels) #CWCB
    ver = (0x1 << 16 | 0x2) 
    fw.write(struct.pack('i', ver)) #version
    vertex_format = 0x01000193
    fw.write(struct.pack('i', vertex_format)) #vertex format, not currently used
    fw.write(struct.pack('i', edge_count)) #vertex count - vertex per edge at the moment

    active_channel_count = 1 #positions

    uv_channel_count = len(me.uv_layers)
   #print("uv_channel_count: %i" % uv_channel_count)

    active_channel_count += uv_channel_count

    fw.write(struct.pack('i', active_channel_count))  #active channel count
    fw.write(struct.pack('i', len(me.polygons)))

    #start of vertex channel data
    #positions
    fw.write(struct.pack('i',0))       #channel 0 is position channel 0
    fw.write(struct.pack('i',3 << 16)) #format, refers to channel element count (for positions 3, shifted over)
    ecount = len(me_verts)
    fw.write(struct.pack('i',ecount)) #format, refers to position  count
    for v in me_verts:
        fw.write(struct.pack('fff', v.co[0], v.co[1], v.co[2]))
    uv_base_channel = 1
    for i in range(0, uv_channel_count):
        fw.write(struct.pack('i',uv_base_channel + i))       #channel 0 is position channel 0
        fw.write(struct.pack('i',2 << 16))     #format, refers to channel element (e.g. position is 3 for x,y,z) count
        uv_layer = me.uv_layers[i].data
        fw.write(struct.pack('i', len(uv_layer)))   #refers to the element count - i.e. the amount of points or uv coords (e.g. 8 positions for a cube)        
        #print("    UV group: %i" % i)
        for uv in uv_layer:
            fw.write(struct.pack('ff', uv.uv[0], -uv.uv[1])) #N.B. 'v' component is flipped
            #print("    UV: %r" % uv.uv)       

    #unique_vertices 
    #this is currently one half-edge per vertex (in blender-speak, one loop-edge per vertex)
    #Clayworks works by a system of vertex channels, the members of which can be any size between 1 and loop-edge-count
    #The following table maps these vertex channels on to unique vertices. Loop-edges then reference these unique vertices.
    #Blender doesn't do this - non positional information is not shared between vertices.
    #Ideally, at this point, I'd run a routine to scan through these and coallese them in to shared vertices, building up the index tables as I go along.
    #That's for version 2 (n.b. remove this message on version 2)    
    
    print("Unique vertex count: %i" % (edge_count ))
    for loop_index in range(0, edge_count):
        fw.write(struct.pack('i', me.loops[loop_index].vertex_index)) #position index - positions are not vertices but nevermind. 
        for channel_index in range(0, uv_channel_count):
            fw.write(struct.pack('i', loop_index)) #ideally, these would be unique.            

    curr_smooth_group = 1;
    for poly in me.polygons:
        #print("Edge count: %i" % poly.loop_total)
        fw.write(struct.pack('i', poly.loop_total)) #point count
        fw.write(struct.pack('h', 0)) #flags
        if poly.use_smooth:            
            smooth_group = 0
        else:
            smooth_group = curr_smooth_group
            curr_smooth_group = curr_smooth_group + 1
        
        fw.write(struct.pack('B', smooth_group  & 255)) #smoothgroup
        fw.write(struct.pack('B', poly.material_index & 255)) #material reference
        for idx in range(0, poly.loop_total):
            value = poly.loop_start + poly.loop_total - (idx + 1)
            fw.write(struct.pack('i', value))
            #print("    Vertex: %d" % value)

            
    print('File offset: %i\n' % fw.tell())
    fw.close();

 

def write_file(filepath, objects, scene,
               EXPORT_TRI=False,
               EXPORT_EDGES=False,
               EXPORT_NORMALS=False,
               EXPORT_UV=True,
               EXPORT_MTL=True,
               EXPORT_APPLY_MODIFIERS=True,
               EXPORT_BLEN_OBS=True,
               EXPORT_GROUP_BY_OB=False,
               EXPORT_GROUP_BY_MAT=False,
               EXPORT_KEEP_VERT_ORDER=False,
               EXPORT_POLYGROUPS=False,
               EXPORT_CURVE_AS_NURBS=True,
               EXPORT_GLOBAL_MATRIX=None,
               EXPORT_PATH_MODE='AUTO',
               ):
    '''
    Basic write function. The context and options must be already set
    This can be accessed externaly
    eg.
    write( 'c:\\test\\foobar.obj', Blender.Object.GetSelected() ) # Using default options.
    '''

    if EXPORT_GLOBAL_MATRIX is None:
        EXPORT_GLOBAL_MATRIX = mathutils.Matrix()

    def veckey3d(v):
        return round(v.x, 6), round(v.y, 6), round(v.z, 6)

    def veckey2d(v):
        return round(v[0], 6), round(v[1], 6)

    def findVertexGroupName(face, vWeightMap):
        """
        Searches the vertexDict to see what groups is assigned to a given face.
        We use a frequency system in order to sort out the name because a given vetex can
        belong to two or more groups at the same time. To find the right name for the face
        we list all the possible vertex group names with their frequency and then sort by
        frequency in descend order. The top element is the one shared by the highest number
        of vertices is the face's group
        """
        weightDict = {}
        for vert_index in face.vertices:
            vWeights = vWeightMap[vert_index]
            for vGroupName, weight in vWeights:
                weightDict[vGroupName] = weightDict.get(vGroupName, 0.0) + weight

        if weightDict:
            return max((weight, vGroupName) for vGroupName, weight in weightDict.items())[1]
        else:
            return '(null)'

    print('Clayworks Export path: %r' % filepath)

    time1 = time.time()

    file = open(filepath, "w", encoding="utf8", newline="\n")
    fw = file.write

    # Write Header
    
    fw('<?xml version=\'1.0\' encoding=\'utf-8\' ?>\n')
    fw('<!-- Blender v%s Clayworks Export-->\n' % bpy.app.version_string)    

    fw('<v3d>\n')
    # Tell the obj file what material file to use.
    # if EXPORT_MTL:
    #    mtlfilepath = os.path.splitext(filepath)[0] + ".mtl"
    #   fw('mtllib %s\n' % repr(os.path.basename(mtlfilepath))[1:-1])  # filepath can contain non utf8 chars, use repr

    # Initialize totals, these are updated each object
    base_path = os.path.split(filepath)[0]
    print("Path: %s\n" % base_path)

    totverts = totuvco = totno = 1

    face_vert_index = 1

    globalNormals = {}

    # A Dict of Materials
    # (material.name, image.name):matname_imagename # matname_imagename has gaps removed.
    mtl_dict = {}

    copy_set = set()
    fw('<CScene name=\'scene\' id=\'13432\'>\n' )
    fw('    <CNodeGroup name=\'Meshes\' id=\'555558\' >\n')
    instances = []
    # Get all meshes
    for ob_main in objects:
        # ignore dupli children
        if ob_main.parent and ob_main.parent.dupli_type in {'VERTS', 'FACES'}:
        # XXX
            print(ob_main.name, 'is a dupli child - ignoring')
            continue
        obs = []
        if ob_main.dupli_type != 'NONE':
            # XXX
            print('creating dupli_list on', ob_main.name)
            ob_main.dupli_list_create(scene)

            obs = [(dob.object, dob.matrix) for dob in ob_main.dupli_list]

            # XXX debug print
            print(ob_main.name, 'has', len(obs), 'dupli children')
        else:
            obs = [(ob_main, ob_main.matrix_world, ob_main.location, ob_main.rotation_euler, ob_main.scale)]
             

        for ob, ob_mat, p, o, s in obs:               
            # Nurbs curve support
            if EXPORT_CURVE_AS_NURBS and test_nurbs_compat(ob):
                ob_mat = EXPORT_GLOBAL_MATRIX * ob_mat
                totverts += write_nurb(fw, ob, ob_mat)
                continue
            # END NURBS

            try:
                me = ob.to_mesh(scene, EXPORT_APPLY_MODIFIERS, 'PREVIEW')
            except RuntimeError:
                me = None

            if me is None:
                continue

            #me.transform(EXPORT_GLOBAL_MATRIX * ob_mat)

            materials = me.materials[:]
            material_names = [m.name if m else None for m in materials]

            # avoid bad index errors
            if not materials:
                materials = [None]
                material_names = [""]
            else:
                for mat in materials:
                    mtl_dict[mat.name] = mat.name, mat, "" #last parameter is 'face image'

            print(materials)
            #mat_data = mtl_dict[key] = mtl_name, materials[f_mat], f_image
            #mtl_rev_dict[mtl_name] = key
                          
            name1 = ob.name
            name2 = ob.data.name
            if name1 == name2:
                obnamestring = name_compat(name1)
            else:
                obnamestring = '%s_%s' % (name_compat(name1), name_compat(name2))
            matid = HASH_LIGHTMAP_MATERIAL;
            name_hash = make_hash(obnamestring)
            instances.extend([C3DInstance(obnamestring, p, o , s, name_hash)])
            mesh_url = obnamestring + ".cwm"
            absolute_mesh_url = base_path + "\\" + mesh_url;
            #should be relative
            #
            fw('        <CObjectRecipe name=\'%s\''  % obnamestring)
            fw(' id=\'%i\' >\n' % name_hash)
            fw('            <CMeshCacheGenerator ')
            fw(' material=\'get_node_from_uid(%i)\' ' % matid)
            fw(' url=\'%s\' />\n' % mesh_url)
            fw('        </CObjectRecipe> \n')
                           
            write_binary_cw_file(absolute_mesh_url, me, materials, EXPORT_UV, EXPORT_KEEP_VERT_ORDER , EXPORT_POLYGROUPS , EXPORT_EDGES, EXPORT_NORMALS)

            # clean up
            bpy.data.meshes.remove(me)

     
        if ob_main.dupli_type != 'NONE':
            ob_main.dupli_list_clear()

    fw('    </CNodeGroup>\n')
    # Now we have all our materials, save them

    if EXPORT_MTL:
        write_mtl( fw, scene, copy_set, mtl_dict)
    for instance in instances:
        fw('    <CPhysicalRenderInstance name=\'%s_instance\' flags=\'ESF_VISIBLE|ESF_ACTIVE\' position=\'p(%.3f, %.3f, %.3f)\' orientation=\'v(%.3f, %.3f, %.3f)\' scale=\'v(%.3f, %.3f, %.3f)\' mesh=\'get_node_from_uid(%i)\' />  \n' % (instance.name , instance.position.x, instance.position.y, instance.position.z, instance.orientation.x + (math.pi * 0.5), instance.orientation.y, instance.orientation.z, instance.scale.x, instance.scale.y, instance.scale.z, instance.mesh_id) )
        #ShopRoom' id='87003370' flags='ESF_VISIBLE' position='p(0.173305,0,0.0577726)' orientation='v(1.5708,0,0)' scale='v(1,1,1)' mask='2147483647' dynamic='0' mass='1' collision_mesh_type='ECOT_CYLINDER_Z' friction='1' angular_dampening='0' linear_dampening='0' max_torque='1e+009' max_speed='1000' mesh='get_node_from_uid(86976263)' />
    #  fw('v %.6f %.6f %.6f\n' % (ob_mat * pt.co.to_3d())[:])
 
    fw('</CScene>\n')
    fw('</v3d>\n')
    file.close()

    #scene, mtlfilepath, EXPORT_PATH_MODE
    # copy all collected files.
    bpy_extras.io_utils.path_reference_copy(copy_set)


    print("Clayworks format export time: %.2f" % (time.time() - time1))


def _write(context, filepath,
              EXPORT_TRI,  # ok
              EXPORT_EDGES,
              EXPORT_NORMALS,  # not yet
              EXPORT_UV,  # ok
              EXPORT_MTL,
              EXPORT_APPLY_MODIFIERS,  # ok
              EXPORT_BLEN_OBS,
              EXPORT_GROUP_BY_OB,
              EXPORT_GROUP_BY_MAT,
              EXPORT_KEEP_VERT_ORDER,
              EXPORT_POLYGROUPS,
              EXPORT_CURVE_AS_NURBS,
              EXPORT_SEL_ONLY,  # ok
              EXPORT_ANIMATION,
              EXPORT_GLOBAL_MATRIX,
              EXPORT_PATH_MODE,
              ):  # Not used

    base_name, ext = os.path.splitext(filepath)
    context_name = [base_name, '', '', ext]  # Base name, scene name, frame number, extension

    scene = context.scene

    # Exit edit mode before exporting, so current object states are exported properly.
    if bpy.ops.object.mode_set.poll():
        bpy.ops.object.mode_set(mode='OBJECT')

    orig_frame = scene.frame_current

    # Export an animation?
    if EXPORT_ANIMATION:
        scene_frames = range(scene.frame_start, scene.frame_end + 1)  # Up to and including the end frame.
    else:
        scene_frames = [orig_frame]  # Dont export an animation.

    # Loop through all frames in the scene and export.
    for frame in scene_frames:
        if EXPORT_ANIMATION:  # Add frame to the filepath.
            context_name[2] = '_%.6d' % frame

        scene.frame_set(frame, 0.0)
        if EXPORT_SEL_ONLY:
            objects = context.selected_objects
        else:
            objects = scene.objects

        full_path = ''.join(context_name)

        # erm... bit of a problem here, this can overwrite files when exporting frames. not too bad.
        # EXPORT THE FILE.
        write_file(full_path, objects, scene,
                   EXPORT_TRI,
                   EXPORT_EDGES,
                   EXPORT_NORMALS,
                   EXPORT_UV,
                   EXPORT_MTL,
                   EXPORT_APPLY_MODIFIERS,
                   EXPORT_BLEN_OBS,
                   EXPORT_GROUP_BY_OB,
                   EXPORT_GROUP_BY_MAT,
                   EXPORT_KEEP_VERT_ORDER,
                   EXPORT_POLYGROUPS,
                   EXPORT_CURVE_AS_NURBS,
                   EXPORT_GLOBAL_MATRIX,
                   EXPORT_PATH_MODE,
                   )

    scene.frame_set(orig_frame, 0.0)

    # Restore old active scene.
#   orig_scene.makeCurrent()
#   Window.WaitCursor(0)


'''
Currently the exporter lacks these features:
* multiple scene export (only active scene is written)
* particles
'''


def save(operator, context, filepath="",
         use_triangles=False,
         use_edges=True,
         use_normals=False,
         use_uvs=True,
         use_materials=True,
         use_apply_modifiers=True,
         use_blen_objects=True,
         group_by_object=False,
         group_by_material=False,
         keep_vertex_order=False,
         use_vertex_groups=False,
         use_nurbs=True,
         use_selection=True,
         use_animation=False,
         global_matrix=None,
         path_mode='AUTO'
         ):

    _write(context, filepath,
           EXPORT_TRI=use_triangles,
           EXPORT_EDGES=use_edges,
           EXPORT_NORMALS=use_normals,
           EXPORT_UV=use_uvs,
           EXPORT_MTL=use_materials,
           EXPORT_APPLY_MODIFIERS=use_apply_modifiers,
           EXPORT_BLEN_OBS=use_blen_objects,
           EXPORT_GROUP_BY_OB=group_by_object,
           EXPORT_GROUP_BY_MAT=group_by_material,
           EXPORT_KEEP_VERT_ORDER=keep_vertex_order,
           EXPORT_POLYGROUPS=use_vertex_groups,
           EXPORT_CURVE_AS_NURBS=use_nurbs,
           EXPORT_SEL_ONLY=use_selection,
           EXPORT_ANIMATION=use_animation,
           EXPORT_GLOBAL_MATRIX=global_matrix,
           EXPORT_PATH_MODE=path_mode,
           )

    return {'FINISHED'}



def save_mesh(operator, context, filepath="",
         use_triangles=False,
         use_edges=True,
         use_normals=False,
         use_uvs=True,
         use_materials=True,
         use_apply_modifiers=True,
         use_blen_objects=True,
         group_by_object=False,
         group_by_material=False,
         keep_vertex_order=False,
         use_vertex_groups=False,
         use_nurbs=True,
         use_selection=True,
         use_animation=False,
         global_matrix=None,
         path_mode='AUTO'
         ):

        
    for ob_main in objects:
    # ignore dupli children
    if ob_main.parent and ob_main.parent.dupli_type in {'VERTS', 'FACES'}:
    # XXX
        print(ob_main.name, 'is a dupli child - ignoring')
        continue
    obs = []
    if ob_main.dupli_type != 'NONE':
        # XXX
        print('creating dupli_list on', ob_main.name)
        ob_main.dupli_list_create(scene)
        obs = [(dob.object, dob.matrix) for dob in ob_main.dupli_list]
        # XXX debug print
        print(ob_main.name, 'has', len(obs), 'dupli children')
    else:
        obs = [(ob_main, ob_main.matrix_world, ob_main.location, ob_main.rotation_euler, ob_main.scale)]
    

    outmesh = None;
    
    #bm = bmesh.new()   # create an empty BMesh

    for ob, ob_mat, p, o, s in obs:               
       
        try:
            outmesh = ob.to_mesh(scene, EXPORT_APPLY_MODIFIERS, 'PREVIEW')
            break
        except RuntimeError:
            me = None

        if me is None:
            continue
        outmesh.merge(me)



    # Finish up, write the bmesh back to the mesh
    #bm.to_mesh(me)
    #bm.free()  # free and prevent further access

    write_binary_cw_file(filepath, outmesh, materials = None, EXPORT_UV = use_uvs, EXPORT_KEEP_VERT_ORDER = True, EXPORT_POLYGROUPS = false, EXPORT_EDGES = use_edges, EXPORT_NORMALS = use_normals):


    return {'FINISHED'}
