#! /usr/bin/env python
import sys
#import bpy
from array import array


types = ('CIRCLE', 'BOX', 'POLY', 'END')	#Different types found in the file and the end of file statement

def readWriteCircle(in_file, out_file):
	print("Writing")
	xpos = 0.0
	ypos = 0.0
	radius = 0.0

	while True:
		pos = in_file.tell()
		text = in_file.readline()

		string_list = text.split()
		
		i = string_list.pop(0)
		
		if i in types:
			in_file.seek(pos)
			print("Breaking from Circle to write %s" % i)
			break
		elif i == 'Position':
			xpos = string_list.pop(0)
			ypos = string_list.pop(0)
		elif i == 'Radius':
			radius = string_list.pop(0)
	
	out_file.append(0.0)
	out_file.append(float(xpos))
	out_file.append(float(ypos))
	out_file.append(float(radius))

def readWriteBox(in_file, out_file):
	xpos = 0.0
	ypos = 0.0
	width = 0.0
	height = 0.0

	while True:
		pos = in_file.tell()
		text = in_file.readline()

		string_list = text.split()
		
		i = string_list.pop(0)

		if i in types:
			in_file.seek(pos)
			print("Breaking from Box to write %s" % i)
			break
		elif i == 'Position':
			xpos = string_list.pop(0)
			ypos = string_list.pop(0)
		elif i == 'Width':
			width = string_list.pop(0)
		elif i == 'Height':
			height = string_list.pop(0)
	
	out_file.append(1.0)
	out_file.append(float(xpos))
	out_file.append(float(ypos))
	out_file.append(float(width))
	out_file.append(float(height))

def readWritePoly(in_file, out_file): #format-[2.0, xpos, ypos, num_verts, vertxpos, vertypos ... num_edges, vertone, verttwo...]
	xpos = 0.0
	ypos = 0.0
	verts = list()
	edges = list()

	while True:
		pos = in_file.tell()
		text = in_file.readline()

		string_list = text.split()
		i = string_list.pop(0)

		if i in types:
			in_file.seek(pos)
			print("Breaking from Poly to write %s" % i)
			break
		elif i == 'Position':
			xpos = float(string_list.pop(0))
			ypos = float(string_list.pop(0))
		elif i == 'Vert':
			xval = float(string_list.pop(0))
			yval = float(string_list.pop(0))
			verts.append((xval, yval))
		elif i == 'Edge':
			firstvert = float(string_list.pop(0))
			secondvert = float(string_list.pop(0))
			edges.append((firstvert, secondvert))

	out_file.append(2.0)
	out_file.append(xpos)
	out_file.append(ypos)
	out_file.append(float(len(verts)))

	for vert in verts:
		#print("Vert - " + str(vert[0]) + " - " + str(vert[1]))
		out_file.append(vert[0])
		out_file.append(vert[1])

	out_file.append(float(len(edges)))

	for edge in edges:
		#print("Edge - " + str(edge[0]) + " - " + str(edge[1]))
		out_file.append(edge[0])
		out_file.append(edge[1])

def readWriteFile(file_name):
	
	text_file = open(file_name, 'r')
	binary_file = list()

	while True:
		text = text_file.readline()
		if text == '':
			break

		if text.find('CIRCLE') == 0:
			readWriteCircle(text_file, binary_file)
		elif text.find('BOX') == 0:
			readWriteBox(text_file, binary_file)
		elif text.find('POLY') == 0:
			readWritePoly(text_file, binary_file)
		elif text.find('END') == 0:
			binary_file.append(496.0)	#End of file number
			break
		else:
			print(text)

	file_name += 'b'
	out_file = open(file_name, 'wb')
	out_data = array('f', binary_file)
	out_data.tofile(out_file)
	text_file.close();
	out_file.close();

	
#If this is run as the main function, read and write the file

if __name__ == '__main__':
	if len(sys.argv) != 2:
		sys.exit("Wrong number of arguments (" + str(len(sys.argv)) + ") given")

	print("About to save box2D collision objects")
	
	readWriteFile(sys.argv[1])	
