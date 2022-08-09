from wand.image import Image as WImage

imgpath = 'C:/Users/lemon/Desktop/default-cover.jpg'

def Save():
    with WImage(filename='C:/Users/lemon/Desktop/sunset.exr') as img:
        img.format = 'jpeg'
        img.save(filename='C:/Users/lemon/Desktop/sunset.jpg')

def Clipboard():
    with WImage(filename='clipboard:') as img:
        img.save(filename='C:/Users/lemon/Desktop/test.jpg')

