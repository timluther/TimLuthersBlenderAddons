def createImage(size):	
	import bpy
	import PIL.Image
	# blank image
	image = bpy.data.images.new("MyImage", width=size[0], height=size[1])
	pixels = [None] * size[0] * size[1]
	for x in range(size[0]):
		for y in range(size[1]):
			# assign RGBA to something useful
			r = x / size[0]
			g = y / size[1]
			b = (1 - r) * g
			a = 1.0
			pixels[(y * size[0]) + x] = [r, g, b, a]
	# flatten list
	pixels = [chan for px in pixels for chan in px]
	# assign pixels
	image.pixels = pixels
	# write image
	image.filepath_raw = "/tmp/temp.png"
	image.file_format = 'PNG'
	image.save()


def convertBlenderToPIL(img):
	pimg = PIL.Image.new("RGBA", img.size)
	pixels = img.pixels[:] # copy for speed
	convpix = []
	pixelCount = img.size[0] * img.size[1]
	for y in reversed(range(img.size[1])):
		base = (y * img.size[0]) << 2
		for x in range(img.size[0]):
			convpix.append((int(pixels[base] * 255), int(pixels[base + 1] * 255), int(pixels[base + 2] * 255), int(pixels[base + 3] * 255)))
			base += 4
	pimg.putdata(convpix)
	return pimg

