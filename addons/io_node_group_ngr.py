bl_info = {
	"name": "Node Group to Python Script (.ngr)",
	"description": "Save node group as python file",
	"author": "Luca Rood",
	"version": (0, 1),
	"blender": (2, 68, 0),
	"location": "File > Import-Export > Node Group (.ngr)",
	"warning": "Test version, might contain bugs.",
	"category": "Import-Export"
	}

import bpy
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper


def export(context, filepath, group):
	groups = []
	groups.append(group)
	
	index = 0
	while len(groups) > index:
		for node in groups[index].node_tree.nodes:
			if node.type == 'GROUP':
				groups.append(node)
		index += 1
	
	for grp1 in groups:
		for grp2 in groups:
			if grp1 != grp2 and grp1.node_tree == grp2.node_tree:
				groups.remove(grp1)
	
	file = open(filepath, 'w')
	file.write("import bpy\n")
	file.write("groups = {}\n")
	
	for grp in reversed(groups):
		file.write("group = bpy.data.node_groups.new('{0}', '{1}')\n".format(grp.node_tree.name, grp.node_tree.bl_idname))
		file.write("group.use_fake_user = True\n")
		file.write("groups['{0}'] = group\n".format(grp.node_tree.name))
		
		file.write("nodes = []\n")
		for n_index, node in enumerate(grp.node_tree.nodes):
			file.write("nodes.append(group.nodes.new('{0}'))\n".format(node.bl_idname))
			if node.type == 'GROUP':
				file.write("nodes[{0}].node_tree = groups['{1}']\n".format(n_index, node.node_tree.name))
		
		for link in grp.node_tree.links:
			file.write("group.links.new(group.nodes[{0}].outputs[{1}], group.nodes[{2}].inputs[{3}], False)\n".format(list(grp.node_tree.nodes).index(link.from_node), list(link.from_node.outputs).index(link.from_socket), list(grp.node_tree.nodes).index(link.to_node), list(link.to_node.inputs).index(link.to_socket)))
		
		for n_index, node in enumerate(grp.node_tree.nodes):
			attrs = [attr for attr in dir(node) if not attr.startswith("__")]
			for attr in attrs:
				val = getattr(node, attr)
				try:
					setattr(node, attr, val)
					valid = True
				except:
					valid = False
				
				if valid == True:
					if isinstance(val, str):
						file.write("setattr(nodes[{0}], '{1}', {2})\n".format(n_index, attr, "'" + val + "'"))
					
					elif isinstance(val, int) or isinstance(val, float) or isinstance(val, bool) or val == None:
						file.write("setattr(nodes[{0}], '{1}', {2})\n".format(n_index, attr, val))
					
					elif attr == "node_tree":
						pass
					
					else:
						file.write("setattr(nodes[{0}], '{1}', {2})\n".format(n_index, attr, list(val)))
			
			for index, input in enumerate(node.inputs):
				attrs = [attr for attr in dir(input) if not attr.startswith("__")]
				for attr in attrs:
					val = getattr(input, attr)
					try:
						setattr(input, attr, val)
						valid = True
					except:
						valid = False
					
					if valid == True:
						if isinstance(val, str):
							file.write("setattr(nodes[{0}].inputs[{1}], '{2}', {3})\n".format(n_index, index, attr, "'" + val + "'"))
						
						elif isinstance(val, int) or isinstance(val, float) or isinstance(val, bool) or val == None:
							file.write("setattr(nodes[{0}].inputs[{1}], '{2}', {3})\n".format(n_index, index, attr, val))
						
						else:
							file.write("setattr(nodes[{0}].inputs[{1}], '{2}', {3})\n".format(n_index, index, attr, list(val)))
			
			for index, output in enumerate(node.outputs):
				attrs = [attr for attr in dir(output) if not attr.startswith("__")]
				for attr in attrs:
					val = getattr(output, attr)
					try:
						setattr(output, attr, val)
						valid = True
					except:
						valid = False
					
					if valid == True:
						if isinstance(val, str):
							file.write("setattr(nodes[{0}].outputs[{1}], '{2}', {3})\n".format(n_index, index, attr, "'" + val + "'"))
						
						elif isinstance(val, int) or isinstance(val, float) or isinstance(val, bool) or val == None:
							file.write("setattr(nodes[{0}].outputs[{1}], '{2}', {3})\n".format(n_index, index, attr, val))
						
						else:
							file.write("setattr(nodes[{0}].outputs[{1}], '{2}', {3})\n".format(n_index, index, attr, list(val)))
		
		attrs = [attr for attr in dir(grp.node_tree) if not attr.startswith("__")]
		for attr in attrs:
			val = getattr(grp.node_tree, attr)
			try:
				setattr(grp.node_tree, attr, val)
				valid = True
			except:
				valid = False
			
			if valid == True:
				if isinstance(val, str):
					file.write("setattr(group, '{0}', {1})\n".format(attr, "'" + val + "'"))
				
				elif isinstance(val, int) or isinstance(val, float) or isinstance(val, bool) or val == None:
					file.write("setattr(group, '{0}', {1})\n".format(attr, val))
				
				else:
					file.write("setattr(group, '{0}', {1})\n".format(attr, list(val)))
		
		for index, input in enumerate(grp.node_tree.inputs):
			attrs = [attr for attr in dir(input) if not attr.startswith("__")]
			for attr in attrs:
				val = getattr(input, attr)
				try:
					setattr(input, attr, val)
					valid = True
				except:
					valid = False
				
				if valid == True:
					if isinstance(val, str):
						file.write("setattr(group.inputs[{0}], '{1}', {2})\n".format(index, attr, "'" + val + "'"))
					
					elif isinstance(val, int) or isinstance(val, float) or isinstance(val, bool) or val == None:
						file.write("setattr(group.inputs[{0}], '{1}', {2})\n".format(index, attr, val))
					
					else:
						file.write("setattr(group.inputs[{0}], '{1}', {2})\n".format(index, attr, list(val)))
		
		for index, output in enumerate(grp.node_tree.outputs):
			attrs = [attr for attr in dir(output) if not attr.startswith("__")]
			for attr in attrs:
				val = getattr(output, attr)
				try:
					setattr(output, attr, val)
					valid = True
				except:
					valid = False
				
				if valid == True:
					if isinstance(val, str):
						file.write("setattr(group.outputs[{0}], '{1}', {2})\n".format(index, attr, "'" + val + "'"))
					
					elif isinstance(val, int) or isinstance(val, float) or isinstance(val, bool) or val == None:
						file.write("setattr(group.outputs[{0}], '{1}', {2})\n".format(index, attr, val))
					
					else:
						file.write("setattr(group.outputs[{0}], '{1}', {2})\n".format(index, attr, list(val)))
	
	file.flush()
	file.close()
	
	return {'FINISHED'}


class ExportNGR(bpy.types.Operator, ExportHelper):
	bl_idname = "export_node_group.ngr"
	bl_label = 'Export NGR'
	bl_description = "Save selected node group to python script (.ngr)"

	filename_ext = ".ngr"
	filter_glob = StringProperty(default="*.ngr", options={'HIDDEN'})
	
	active_group = None
	
	@classmethod
	def poll(cls, context):
		valid = False
		
		size = 0.0
		main_area = None
		for area in context.screen.areas:
			if area.type == 'NODE_EDITOR' and area.width * area.height > size:
				size = area.width * area.height
				main_area = area
		
		if main_area != None:
			try:
				if main_area.spaces[0].node_tree.nodes.active.type == 'GROUP':
					valid = True
			
			except:
				pass
		
		return valid
	
	def invoke(self, context, event):
		size = 0.0
		main_area = None
		for area in context.screen.areas:
			if area.type == 'NODE_EDITOR' and area.width * area.height > size:
				size = area.width * area.height
				main_area = area
		
		self.active_group = main_area.spaces[0].node_tree.nodes.active
		
		self.filepath = self.active_group.node_tree.name + ".ngr"
		context.window_manager.fileselect_add(self)
		return {'RUNNING_MODAL'}
	
	def execute(self, context):
		return export(context, self.filepath, self.active_group)


class ImportNGR(bpy.types.Operator, ImportHelper):
	bl_idname = "import_node_group.ngr"
	bl_label = 'Import NGR'
	bl_description = "Import node group from file (.ngr)"

	filename_ext = ".ngr"
	filter_glob = StringProperty(default="*.ngr", options={'HIDDEN'})
	
	def execute(self, context):
		exec(compile(open(self.filepath).read(), self.filepath, 'exec'))
		
		return {'FINISHED'}


def menu_func_export(self, context):
	self.layout.operator(ExportNGR.bl_idname, text="Node Group (.ngr)")

def menu_func_import(self, context):
	self.layout.operator(ImportNGR.bl_idname, text="Node Group (.ngr)")

def register():
	bpy.utils.register_module(__name__)
	
	bpy.types.INFO_MT_file_import.append(menu_func_import)
	bpy.types.INFO_MT_file_export.append(menu_func_export)

def unregister():
	bpy.utils.unregister_module(__name__)
	
	bpy.types.INFO_MT_file_import.remove(menu_func_import)
	bpy.types.INFO_MT_file_export.remove(menu_func_export)