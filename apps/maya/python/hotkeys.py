import maya.cmds as cmds

cmds.hotkey(keyShortcut='s', alt=True, name=('ScriptEditorNameCommand'))
cmds.savePrefs(hk=True)