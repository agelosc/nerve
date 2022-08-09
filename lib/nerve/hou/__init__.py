import nerve, hou

def GetSelectedNodes():
    sel = hou.selectedNodes()
    nodes = []
    for n in sel:
        args = {}
        args['type'] = n.type().name()
        args['name'] = n.name()
        args['path'] = n.path()

        nodes.append( Node(**args) )

    return nodes


class Node(nerve.Node):
    def __init__(self, **kwargs):
        nerve.Node.__init__(self, **kwargs)

        self.data['app'] = 'hou'

    def Create(self):
        path = nerve.Path(self.data['path'])

        pwd = path.GetRoot()
        hnode = hou.node('/'+pwd)
        if not hnode:
            raise Exception('invalid context /{}'.format(pwd))

        for i in range(2, len(path.segments)):
            pwd = path.GetRelative(i+1)
            print(pwd)
