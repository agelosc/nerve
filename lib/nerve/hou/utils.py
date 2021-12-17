import hou

def ObjectMergeSelection():
    sel = hou.selectedNodes()
    for n in sel:
        object_merge = n.parent().createNode('object_merge', node_name='in_%s'%n.name())
        object_merge.moveToGoodPosition(move_inputs=False, move_unconnected=False)
        object_merge.setColor( hou.Color(0.188, 0.529, 0.459) )
        object_merge.parm('objpath1').set( object_merge.relativePathTo(n) )
        
def BlastToGroup():
    sel = hou.selectedNodes()
    groupText = ''
    for n in sel:
        groupText+= n.parm('group').eval()  + ' '
    
    grp = sel[0].parent().createNode('groupcreate')
    grp.parm('basegroup').set(groupText)
    grp.moveToGoodPosition(move_inputs=False, move_unconnected=False)
    
        
    

