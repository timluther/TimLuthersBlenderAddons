import glob
import PIL
import PIL.Image


def LowerPowerOf2(val):
    i = 1
    while (1 << i) < val:
        i = i + 1
    return 1 << (i - 1)


def NextPowerOf2(val):
    i = 1
    while (1 << i) <= val:
        i = i + 1
    return 1 << i


def clearImage(img, colour = (255, 255, 255, 0)):
    pixdata = img.load()
    for y in range(img.size[1]):
        for x in range(img.size[0]):
            pixdata[x, y] = colour


class PackNode(object):

    """
    Creates an area which can recursively pack other areas of smaller sizes into itself.
    """

    def __init__(self, area, padding):
        #if tuple contains two elements, assume they are width and height, and origin is (0,0)
        if len(area) == 2:
            area = (0, 0, area[0], area[1])
        self.area = area
        self.padding = padding

    def __repr__(self):
        return "<%s %s>" % (self.__class__.__name__, str(self.area))

    def get_width(self):
        return self.area[2] - self.area[0]

    def get_inner_area(self):
        return (self.area[0], self.area[1], self.area[2] - self.padding, self.area[3] - self.padding)

    width = property(fget=get_width)

    def get_height(self):
        return self.area[3] - self.area[1]
    height = property(fget=get_height)

    def insert(self, area):
        if hasattr(self, 'child'):
            a = self.child[0].insert(area)
            if a is None:
                return self.child[1].insert(area)
            return a

        area = PackNode(area, self.padding)
        if area.width <= self.width and area.height <= self.height:
            self.child = [None, None]
            self.child[0] = PackNode((self.area[0]+area.width + self.padding, self.area[1], self.area[2], self.area[1] + area.height + self.padding), self.padding)
            self.child[1] = PackNode((self.area[0], self.area[1]+area.height + self.padding, self.area[2], self.area[3]), self.padding)
            return PackNode((self.area[0], self.area[1], self.area[0]+area.width + self.padding, self.area[1]+area.height + self.padding), self.padding)

image_maxsize = (2048, 2048)
def PackImagesFromList(images, format = 'RGBA', minsize = (256, 256), padding = 4):
    size = minsize   # get a list of PNG files in the current directory
    tree = PackNode(size, padding)
    image = PIL.Image.new(format, size)
    clearImage(image)
    for area, name, img in images:
        print("Image: " + name + " : " + str(image) + " area : " + str(area))
        uv = tree.insert(img.size)
        if uv is None:
            newsize = (NextPowerOf2(minsize[0]), NextPowerOf2(minsize[1]))
            if newsize[0] > image_maxsize[0] and newsize[1] > image_maxsize[1]:
                raise ValueError('Overflow: cannot create pack.')

            print("Packsize too small, trying next power of 2: %i, %i " % newsize)
            return PackImagesFromList(images, format, newsize, padding)
        image.paste(img, uv.get_inner_area())
    return image, tree

def PackImages(wildcard, minsize = (256, 256)):
    names = glob.glob(wildcard)  # create a list of PIL Image objects, sorted by size
    format = 'RGBA'  # size of the image we are packing into
    images = sorted([(i.size[0] * i.size[1], name, i) for name, i in ((x, PIL.Image.open(x).convert(format)) for x in names)])

    return PackImagesFromList(images, format, minsize)
