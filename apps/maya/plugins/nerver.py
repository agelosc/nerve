import sys
import nerve
import maya.OpenMaya as OpenMaya
import maya.OpenMayaUI as OpenMayaUI


# callback
class PyExternalDropCallback(OpenMayaUI.MExternalDropCallback):
    instance = None

    def __init__(self):
        OpenMayaUI.MExternalDropCallback.__init__(self)
        

    def externalDropCallbacOLD( self, doDrop, controlName, data ):
        str = ("External Drop:  doDrop = %d,  controlName = %s" % (doDrop, controlName))
        
        # Mouse button
        if data.mouseButtons() & OpenMayaUI.MExternalDropData.kLeftButton:
            str += ", LMB"
        if data.mouseButtons() & OpenMayaUI.MExternalDropData.kMidButton:
            str += ", MMB"
        if data.mouseButtons() & OpenMayaUI.MExternalDropData.kRightButton:
            str += ", RMB"
            
        # Key modifiers
        if data.keyboardModifiers() & OpenMayaUI.MExternalDropData.kShiftModifier:
            str += ", SHIFT"
        if data.keyboardModifiers() & OpenMayaUI.MExternalDropData.kControlModifier:
            str += ", CONTROL"
        if data.keyboardModifiers() & OpenMayaUI.MExternalDropData.kAltModifier:
            str += ", ALT"
            
        # Data
        if data.hasText():
            #sys.stdout.write('HAS TEXT\n')
            str += (", text = %s" % data.text())
        if data.hasUrls():
            #sys.stdout.write('HAS URL\n')
            urls = data.urls()
            for (i,url) in enumerate(urls):
                str += (", url[%d] = %s" % (i, url))
            # end
        if data.hasHtml():
            #sys.stdout.write('HAS HTML\n')
            str += (", html = %s" % data.html())
        if data.hasColor():
            #sys.stdout.write('HAS COLOR\n')
            color = data.color()
            str += (", color = (%d, %d, %d, %d)" % (color.r, color.g, color.b, color.a))
        if data.hasImage():
            #sys.stdout.write('HAS IMAGE\n')
            str += (", image = true")
        str += "\n"
        sys.stdout.write( str )
        

        return OpenMayaUI.MExternalDropCallback.kMayaDefault

    def externalDropCallback( self, doDrop, controlName, data ):
      from xml.dom.minidom import parseString

      if doDrop and data.hasHtml():
        #sys.stdout.write(data.html())
        url = data.urls()[0]
        if '?' in url:
            host,get = url.split('?')
            if host == 'http://localhost:8000/assets/':
                data = {}
                for pair in get.split('&'):
                    key,val = pair.split('=')
                    data[key] = val

                asset = nerve.Asset(**data)
                sys.stdout.write(asset)
                
                #sys.stdout.write(data)

        #sys.stdout.write(data.urls())
        
        return OpenMayaUI.MExternalDropCallback.kMayaDefault

        
# end


# Initialize the plug-in
def initializePlugin(plugin):
    try:
        PyExternalDropCallback.instance = PyExternalDropCallback()
        OpenMayaUI.MExternalDropCallback.addCallback( PyExternalDropCallback.instance )
        sys.stdout.write("Successfully registered plug-in: Nerver\n")
    except:
        sys.stderr.write("Failed to register plug-in: Nerver\n")
        raise
# end
        

# Uninitialize the plug-in
def uninitializePlugin(plugin):
    try:
        OpenMayaUI.MExternalDropCallback.removeCallback( PyExternalDropCallback.instance )
        sys.stdout.write("Successfully deregistered plug-in: Nerver\n")
    except:
        sys.stderr.write("Failed to deregister plug-in: Nerver\n")
        raise
