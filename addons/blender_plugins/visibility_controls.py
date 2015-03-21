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

def addselectedobjectrigidbodyenablekeyframes():
	i = 0;
	scene = bpy.context.scene
	for ob in bpy.data.objects:
		if ob.select == True and ob.rigid_body != None:
			ob.rigid_body.keyframe_insert(data_path="enabled", frame=scene.frame_current)			
		++i


def addselectedobjectspositionkeyframes():
	i = 0;
	scene = bpy.context.scene
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.keyframe_insert(data_path="location", frame=scene.frame_current)			
		++i

def addselectedobjectsvisibilitykeyframes():
	i = 0;
	scene = bpy.context.scene
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.keyframe_insert(data_path="hide", frame=scene.frame_current)			
		++i	

def addselectedobjectsrendervisibilitykeyframes():
	i = 0;
	scene = bpy.context.scene
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.keyframe_insert(data_path="hide_render", frame=scene.frame_current)			
		++i	

def addselectedobjectsactivekeyframes():
	i = 0;
	scene = bpy.context.scene
	for ob in bpy.data.objects:
		if ob.select == True:
			ob.keyframe_insert(data_path="hide_select", frame=scene.frame_current)			
		++i	

def objectinfo(object, spacing=10, collapse=1):
	methodList = [e for e in dir(object) if callable(getattr(object, e))]
	processFunc = collapse and (lambda s: " ".join(s.split())) or (lambda s: s)
	print("\n".join(["%s %s" %
					 (method.ljust(spacing),
					  processFunc(str(getattr(object, method).__doc__)))
					 for method in methodList]))