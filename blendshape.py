from maya import cmds
from maya import OpenMaya
import importlib

from . import autorig_utility
importlib.reload(autorig_utility)

def meshattach(mesh_textfield:str,obj_textfield:str):
    """
    メッシュを選択

    Parameters
    ----------
        string textfield : Joint名のテキストボックス

    Returns
    -------
        無し
    """
    object = cmds.textField(obj_textfield,q=True,tx=True)
    object = cmds.ls(object,typ="transform",l=True)
    if(len(object)==0):
        cmds.warning("名前と一致するオブジェクトがありません")
    elif(len(object)>1):
        cmds.warning("複数のオブジェクトが名前と一致します")
    else:
        shape = cmds.listRelatives(object,s=True,f=True)[0]
        cmds.textField(mesh_textfield,edit=True,tx=shape)

def sourcenodeattach(self_textfield:str,obj_textfield:str,typ:str):
    """
    メッシュを選択

    Parameters
    ----------
        string textfield : Joint名のテキストボックス

    Returns
    -------
        無し
    """
    object = cmds.textField(obj_textfield,q=True,tx=True)
    object = cmds.ls(object,l=True)
    if(len(object)==0):
        cmds.warning("名前と一致するオブジェクトがありません")
    elif(len(object)>1):
        cmds.warning("複数のオブジェクトが名前と一致します")
    else:
        node = cmds.listConnections(object,s=True,d=False,t=typ)[0]
        node = cmds.ls(node,l=True)[0]
        cmds.textField(self_textfield,edit=True,tx=node)

def setOptionMenu(optionMenus:list,blendShape:str):
    """
    オプションメニューリストにブレンドシェイプ名入れる

    Parameters
    ----------
        list optionMenus : オプションメニュー入ったリスト

    Returns
    -------
        無し
    """
    node = cmds.textField(blendShape,q=True,tx=True)
    blendShape_names = cmds.listAttr(node + ".weight", multi=True)

    print(blendShape_names)
    print(optionMenus)

    for optionMenu in optionMenus:
        cmds.optionMenu(optionMenu, e=True, deleteAllItems=True, mvi=len(blendShape_names))
        for label in blendShape_names:
            cmds.menuItem(label=label, parent=optionMenu)

def create1x1con(blendShape_textfield:str, name_textfield:str, color_colorSlider:str, blendshape_optionmenu:str):
    """
    1*1コントローラー作成

    Parameters
    ----------
        string blendShape_textfield
        string name_textfield
        string color_colorSlider
        string blendshape_optionmenu

    Returns
    -------
        無し
    """
    blendshape = cmds.textField(blendShape_textfield,q=True,tx=True)
    name = cmds.textField(name_textfield,q=True,tx=True)
    color = cmds.colorSliderGrp(color_colorSlider,q=True,rgb=True)
    shape = cmds.optionMenu(blendshape_optionmenu,q=True,v=True)
    
    parent=cmds.group(em=True,name=f"Grp_BlendShape_{name}")
    cmds.setAttr(f"{parent}.sx",10)
    cmds.setAttr(f"{parent}.sy",10)
    cmds.setAttr(f"{parent}.sz",10)

    controller = autorig_utility.create_nurvs(name,"scuare",rotate=(90,0,0))
    controller = cmds.rename(controller,f"Con_BlendShape_{name}")
    cmds.parent(controller,parent,r=False)
    cmds.makeIdentity(controller,a=True,s=True)

    frame = autorig_utility.create_nurvs(name,"scuare",position=(0,5,0),size=(1.2,1.2,6.2),rotate=(90,0,0))
    frame = cmds.rename(frame,f"Frame_BlendShape_{name}")
    cmds.parent(frame,parent,r=False)
    cmds.makeIdentity(frame,a=True,s=True)

    cmds.setAttr( f"{controller}.tx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.tz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.rx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.ry", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.rz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.sx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.sy", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.sz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.tx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.ty", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.tz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.rx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.ry", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.rz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.sx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.sy", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.sz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f"{controller}.overrideEnabled", 1)
    cmds.setAttr(f"{controller}.overrideRGBColors", 1)  # RGBを有効に
    cmds.setAttr(f"{controller}.overrideColorRGB", color[0],color[1],color[2])
    cmds.setAttr(f"{frame}.overrideEnabled",1)
    cmds.setAttr(f"{frame}.overrideDisplayType",2)
    cmds.transformLimits(controller,ty=(0,1),ety=(1,1))

    cmds.connectAttr(f"{controller}.ty",f"{blendshape}.{shape}",f=True)

    if(name!=""):
        text = cmds.textCurves(t=name, o=True)
        text_parent=cmds.group(name=f"Name_BlendShape_{name}",em=True)
        textobjs = cmds.listRelatives(text,f=True,ad=True,typ="shape")
        for obj in textobjs:
            cmds.parent(obj,text_parent,r=False,s=True)
        cmds.delete(text)
        cmds.setAttr(f"{text_parent}.overrideEnabled",1)
        cmds.setAttr(f"{text_parent}.overrideDisplayType",2)
        cmds.setAttr( f"{text_parent}.sx", 1.5)
        cmds.setAttr( f"{text_parent}.sy", 1.5)
        cmds.setAttr( f"{text_parent}.sz", 1.5)
        bbox = cmds.exactWorldBoundingBox(text_parent)
        move = [
        (bbox[0] + bbox[3]) * -0.5,
        (bbox[1] + bbox[4]) * -0.5 + 12,
        (bbox[2] + bbox[5]) * -0.5
        ]
        cmds.xform(text_parent,t=move)
        cmds.parent(text_parent,parent)
        cmds.makeIdentity(text_parent,a=True,s=True)

def create2x1con(blendShape_textfield:str, name_textfield:str, color_colorSlider:str, blendshape_optionmenu1:str, blendshape_optionmenu2:str):
    """
    2*1コントローラー作成

    Parameters
    ----------
        string blendShape_textfield
        string name_textfield
        string color_colorSlider
        string blendshape_optionmenu
        string blendshape_optionmenu

    Returns
    -------
        無し
    """
    blendshape = cmds.textField(blendShape_textfield,q=True,tx=True)
    name = cmds.textField(name_textfield,q=True,tx=True)
    color = cmds.colorSliderGrp(color_colorSlider,q=True,rgb=True)
    shape1 = cmds.optionMenu(blendshape_optionmenu1,q=True,v=True)
    shape2 = cmds.optionMenu(blendshape_optionmenu2,q=True,v=True)
    
    parent=cmds.group(em=True,name=f"Grp_BlendShape_{name}")
    cmds.setAttr(f"{parent}.sx",10)
    cmds.setAttr(f"{parent}.sy",10)
    cmds.setAttr(f"{parent}.sz",10)

    controller = autorig_utility.create_nurvs(name,"scuare",rotate=(90,0,0))
    controller = cmds.rename(controller,f"Con_BlendShape_{name}")
    cmds.parent(controller,parent,r=False)
    cmds.makeIdentity(controller,a=True,s=True)

    frame = autorig_utility.create_nurvs(name,"scuare",position=(0,0,0),size=(1.2,1.2,11.2),rotate=(90,0,0))
    frame = cmds.rename(frame,f"Frame_BlendShape_{name}")
    cmds.parent(frame,parent,r=False)
    cmds.makeIdentity(frame,a=True,s=True)

    cmds.setAttr( f"{controller}.tx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.tz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.rx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.ry", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.rz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.sx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.sy", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.sz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.tx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.ty", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.tz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.rx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.ry", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.rz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.sx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.sy", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.sz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f"{controller}.overrideEnabled", 1)
    cmds.setAttr(f"{controller}.overrideRGBColors", 1)  # RGBを有効に
    cmds.setAttr(f"{controller}.overrideColorRGB", color[0],color[1],color[2])
    cmds.setAttr(f"{frame}.overrideEnabled",1)
    cmds.setAttr(f"{frame}.overrideDisplayType",2)
    cmds.transformLimits(controller,ty=(-1,1),ety=(1,1))

    #1つ目
    condition1 = cmds.createNode("condition")
    cmds.connectAttr(f"{controller}.ty",f"{condition1}.firstTerm")
    cmds.setAttr(F"{condition1}.operation",2)
    cmds.connectAttr(f"{controller}.ty",f"{condition1}.colorIfTrueR")
    cmds.setAttr(F"{condition1}.secondTerm",0)
    cmds.setAttr(F"{condition1}.colorIfFalseR",0)
    cmds.connectAttr(f"{condition1}.outColorR",f"{blendshape}.{shape1}",f=True)
    #2つ目
    condition2 = cmds.createNode("condition")
    floatMath1 = cmds.createNode("floatMath")
    cmds.connectAttr(f"{controller}.ty",f"{condition2}.firstTerm")
    cmds.setAttr(F"{condition2}.operation",4)
    cmds.connectAttr(f"{controller}.ty",f"{condition2}.colorIfTrueR")
    cmds.setAttr(F"{condition2}.secondTerm",0)
    cmds.setAttr(F"{condition2}.colorIfFalseR",0)
    cmds.connectAttr(f"{condition2}.outColorR",f"{floatMath1}.floatA",f=True)
    cmds.setAttr(F"{floatMath1}.floatB",-1)
    cmds.setAttr(F"{floatMath1}.operation",2)
    cmds.connectAttr(f"{floatMath1}.outFloat",f"{blendshape}.{shape2}",f=True)


    if(name!=""):
        text = cmds.textCurves(t=name, o=True)
        text_parent=cmds.group(name=f"Name_BlendShape_{name}",em=True)
        textobjs = cmds.listRelatives(text,f=True,ad=True,typ="shape")
        for obj in textobjs:
            cmds.parent(obj,text_parent,r=False,s=True)
        cmds.delete(text)
        cmds.setAttr(f"{text_parent}.overrideEnabled",1)
        cmds.setAttr(f"{text_parent}.overrideDisplayType",2)
        cmds.setAttr( f"{text_parent}.sx", 1.5)
        cmds.setAttr( f"{text_parent}.sy", 1.5)
        cmds.setAttr( f"{text_parent}.sz", 1.5)
        bbox = cmds.exactWorldBoundingBox(text_parent)
        move = [
        (bbox[0] + bbox[3]) * -0.5,
        (bbox[1] + bbox[4]) * -0.5 + 12,
        (bbox[2] + bbox[5]) * -0.5
        ]
        cmds.xform(text_parent,t=move)
        cmds.parent(text_parent,parent)
        cmds.makeIdentity(text_parent,a=True,s=True)

def create1x2con(blendShape_textfield:str, name_textfield:str, color_colorSlider:str, blendshape_optionmenu1:str, blendshape_optionmenu2:str):
    """
    1*2コントローラー作成

    Parameters
    ----------
        string blendShape_textfield
        string name_textfield
        string color_colorSlider
        string blendshape_optionmenu
        string blendshape_optionmenu

    Returns
    -------
        無し
    """
    blendshape = cmds.textField(blendShape_textfield,q=True,tx=True)
    name = cmds.textField(name_textfield,q=True,tx=True)
    color = cmds.colorSliderGrp(color_colorSlider,q=True,rgb=True)
    shape1 = cmds.optionMenu(blendshape_optionmenu1,q=True,v=True)
    shape2 = cmds.optionMenu(blendshape_optionmenu2,q=True,v=True)
    
    parent=cmds.group(em=True,name=f"Grp_BlendShape_{name}")
    cmds.setAttr(f"{parent}.sx",10)
    cmds.setAttr(f"{parent}.sy",10)
    cmds.setAttr(f"{parent}.sz",10)

    controller = autorig_utility.create_nurvs(name,"scuare",rotate=(90,0,0))
    controller = cmds.rename(controller,f"Con_BlendShape_{name}")
    cmds.parent(controller,parent,r=False)
    cmds.makeIdentity(controller,a=True,s=True)

    frame = autorig_utility.create_nurvs(name,"scuare",position=(5,5,0),size=(6.2,1.2,6.2),rotate=(90,0,0))
    frame = cmds.rename(frame,f"Frame_BlendShape_{name}")
    cmds.parent(frame,parent,r=False)
    cmds.makeIdentity(frame,a=True,s=True)

    cmds.setAttr( f"{controller}.tz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.rx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.ry", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.rz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.sx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.sy", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.sz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.tx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.ty", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.tz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.rx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.ry", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.rz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.sx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.sy", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.sz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f"{controller}.overrideEnabled", 1)
    cmds.setAttr(f"{controller}.overrideRGBColors", 1)  # RGBを有効に
    cmds.setAttr(f"{controller}.overrideColorRGB", color[0],color[1],color[2])
    cmds.setAttr(f"{frame}.overrideEnabled",1)
    cmds.setAttr(f"{frame}.overrideDisplayType",2)
    cmds.transformLimits(controller,ty=(0,1),ety=(1,1),tx=(0,1),etx=(1,1))

    cmds.connectAttr(f"{controller}.ty",f"{blendshape}.{shape1}",f=True)
    cmds.connectAttr(f"{controller}.tx",f"{blendshape}.{shape2}",f=True)

    if(name!=""):
        text = cmds.textCurves(t=name, o=True)
        text_parent=cmds.group(name=f"Name_BlendShape_{name}",em=True)
        textobjs = cmds.listRelatives(text,f=True,ad=True,typ="shape")
        for obj in textobjs:
            cmds.parent(obj,text_parent,r=False,s=True)
        cmds.delete(text)
        cmds.setAttr(f"{text_parent}.overrideEnabled",1)
        cmds.setAttr(f"{text_parent}.overrideDisplayType",2)
        cmds.setAttr( f"{text_parent}.sx", 1.5)
        cmds.setAttr( f"{text_parent}.sy", 1.5)
        cmds.setAttr( f"{text_parent}.sz", 1.5)
        bbox = cmds.exactWorldBoundingBox(text_parent)
        move = [
        (bbox[0] + bbox[3]) * -0.5 + 5,
        (bbox[1] + bbox[4]) * -0.5 + 12,
        (bbox[2] + bbox[5]) * -0.5
        ]
        cmds.xform(text_parent,t=move)
        cmds.parent(text_parent,parent)
        cmds.makeIdentity(text_parent,a=True,s=True)


def create2x2con(blendShape_textfield:str, name_textfield:str, color_colorSlider:str, blendshape_optionmenu1:str, blendshape_optionmenu2:str, blendshape_optionmenu3:str, blendshape_optionmenu4:str):
    """
    2*1コントローラー作成

    Parameters
    ----------
        string blendShape_textfield
        string name_textfield
        string color_colorSlider
        string blendshape_optionmenu
        string blendshape_optionmenu
        string blendshape_optionmenu
        string blendshape_optionmenu

    Returns
    -------
        無し
    """
    blendshape = cmds.textField(blendShape_textfield,q=True,tx=True)
    name = cmds.textField(name_textfield,q=True,tx=True)
    color = cmds.colorSliderGrp(color_colorSlider,q=True,rgb=True)
    shape1 = cmds.optionMenu(blendshape_optionmenu1,q=True,v=True)
    shape2 = cmds.optionMenu(blendshape_optionmenu2,q=True,v=True)
    shape3 = cmds.optionMenu(blendshape_optionmenu3,q=True,v=True)
    shape4 = cmds.optionMenu(blendshape_optionmenu4,q=True,v=True)
    
    parent=cmds.group(em=True,name=f"Grp_BlendShape_{name}")
    cmds.setAttr(f"{parent}.sx",10)
    cmds.setAttr(f"{parent}.sy",10)
    cmds.setAttr(f"{parent}.sz",10)

    controller = autorig_utility.create_nurvs(name,"scuare",rotate=(90,0,0))
    controller = cmds.rename(controller,f"Con_BlendShape_{name}")
    cmds.parent(controller,parent,r=False)
    cmds.makeIdentity(controller,a=True,s=True)

    frame = autorig_utility.create_nurvs(name,"scuare",position=(0,0,0),size=(11.2,1.2,11.2),rotate=(90,0,0))
    frame = cmds.rename(frame,f"Frame_BlendShape_{name}")
    cmds.parent(frame,parent,r=False)
    cmds.makeIdentity(frame,a=True,s=True)

    cmds.setAttr( f"{controller}.tz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.rx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.ry", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.rz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.sx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.sy", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{controller}.sz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.tx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.ty", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.tz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.rx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.ry", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.rz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.sx", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.sy", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{frame}.sz", lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f"{controller}.overrideEnabled", 1)
    cmds.setAttr(f"{controller}.overrideRGBColors", 1)  # RGBを有効に
    cmds.setAttr(f"{controller}.overrideColorRGB", color[0],color[1],color[2])
    cmds.setAttr(f"{frame}.overrideEnabled",1)
    cmds.setAttr(f"{frame}.overrideDisplayType",2)
    cmds.transformLimits(controller,ty=(-1,1),ety=(1,1),tx=(-1,1),etx=(1,1))

    #1つ目
    condition1 = cmds.createNode("condition")
    cmds.connectAttr(f"{controller}.ty",f"{condition1}.firstTerm")
    cmds.setAttr(F"{condition1}.operation",2)
    cmds.connectAttr(f"{controller}.ty",f"{condition1}.colorIfTrueR")
    cmds.setAttr(F"{condition1}.secondTerm",0)
    cmds.setAttr(F"{condition1}.colorIfFalseR",0)
    cmds.connectAttr(f"{condition1}.outColorR",f"{blendshape}.{shape1}",f=True)
    #2つ目
    condition2 = cmds.createNode("condition")
    floatMath1 = cmds.createNode("floatMath")
    cmds.connectAttr(f"{controller}.ty",f"{condition2}.firstTerm")
    cmds.setAttr(F"{condition2}.operation",4)
    cmds.connectAttr(f"{controller}.ty",f"{condition2}.colorIfTrueR")
    cmds.setAttr(F"{condition2}.secondTerm",0)
    cmds.setAttr(F"{condition2}.colorIfFalseR",0)
    cmds.connectAttr(f"{condition2}.outColorR",f"{floatMath1}.floatA",f=True)
    cmds.setAttr(F"{floatMath1}.floatB",-1)
    cmds.setAttr(F"{floatMath1}.operation",2)
    cmds.connectAttr(f"{floatMath1}.outFloat",f"{blendshape}.{shape2}",f=True)
    #3つ目
    condition1 = cmds.createNode("condition")
    cmds.connectAttr(f"{controller}.tx",f"{condition1}.firstTerm")
    cmds.setAttr(F"{condition1}.operation",2)
    cmds.connectAttr(f"{controller}.tx",f"{condition1}.colorIfTrueR")
    cmds.setAttr(F"{condition1}.secondTerm",0)
    cmds.setAttr(F"{condition1}.colorIfFalseR",0)
    cmds.connectAttr(f"{condition1}.outColorR",f"{blendshape}.{shape3}",f=True)
    #4つ目
    condition2 = cmds.createNode("condition")
    floatMath1 = cmds.createNode("floatMath")
    cmds.connectAttr(f"{controller}.tx",f"{condition2}.firstTerm")
    cmds.setAttr(F"{condition2}.operation",4)
    cmds.connectAttr(f"{controller}.tx",f"{condition2}.colorIfTrueR")
    cmds.setAttr(F"{condition2}.secondTerm",0)
    cmds.setAttr(F"{condition2}.colorIfFalseR",0)
    cmds.connectAttr(f"{condition2}.outColorR",f"{floatMath1}.floatA",f=True)
    cmds.setAttr(F"{floatMath1}.floatB",-1)
    cmds.setAttr(F"{floatMath1}.operation",2)
    cmds.connectAttr(f"{floatMath1}.outFloat",f"{blendshape}.{shape4}",f=True)


    if(name!=""):
        text = cmds.textCurves(t=name, o=True)
        text_parent=cmds.group(name=f"Name_BlendShape_{name}",em=True)
        textobjs = cmds.listRelatives(text,f=True,ad=True,typ="shape")
        for obj in textobjs:
            cmds.parent(obj,text_parent,r=False,s=True)
        cmds.delete(text)
        cmds.setAttr(f"{text_parent}.overrideEnabled",1)
        cmds.setAttr(f"{text_parent}.overrideDisplayType",2)
        cmds.setAttr( f"{text_parent}.sx", 1.5)
        cmds.setAttr( f"{text_parent}.sy", 1.5)
        cmds.setAttr( f"{text_parent}.sz", 1.5)
        bbox = cmds.exactWorldBoundingBox(text_parent)
        move = [
        (bbox[0] + bbox[3]) * -0.5,
        (bbox[1] + bbox[4]) * -0.5 + 12,
        (bbox[2] + bbox[5]) * -0.5
        ]
        cmds.xform(text_parent,t=move)
        cmds.parent(text_parent,parent)
        cmds.makeIdentity(text_parent,a=True,s=True)