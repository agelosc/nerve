try:
    from importlib import reload
except:
    pass

import hou

import nerve
import nerve.hou
reload(nerve.hou)

def Nodes():
    hou.hipFile.clear(suppress_save_prompt=True)

    obj = hou.node('/obj')
    geo = obj.createNode('geo')
    sop = geo.createNode('null')
    sop.setSelected(True, True)

    print(hou.selectedNodes())

    nodes = nerve.hou.GetSelectedNodes()
    hou.hipFile.clear(suppress_save_prompt=True)
    for node in nodes:
        node.Create()
