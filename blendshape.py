from maya import cmds
import importlib

from . import autorig_utility
importlib.reload(autorig_utility)

def meshattach(mesh_textfield:str,obj_textfield:str):
    """
    テキストボックスに入力されたTransform名からシェイプノードを取得してmesh_textfieldへ入れる

    Parameters
    ----------
        string mesh_textfield : シェイプ名を書き込むテキストボックス
        string obj_textfield : メッシュ(Transform)名のテキストボックス

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
    テキストボックスに入力されたオブジェクトの上流に繋がる指定タイプのノードを取得してself_textfieldへ入れる

    Parameters
    ----------
        string self_textfield : 見つかったノード名を書き込むテキストボックス
        string obj_textfield : 検索起点のオブジェクト名のテキストボックス
        string typ : 検索対象のノードタイプ (例: "blendShape")

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
    blendShapeノードが持つターゲット名の一覧をオプションメニューへ流し込む

    Parameters
    ----------
        list optionMenus : オプションメニュー入ったリスト
        string blendShape : blendShapeノード名のテキストボックス

    Returns
    -------
        無し
    """
    node = cmds.textField(blendShape,q=True,tx=True)
    blendShape_names = cmds.listAttr(node + ".weight", multi=True)

    for optionMenu in optionMenus:
        cmds.optionMenu(optionMenu, e=True, deleteAllItems=True, mvi=len(blendShape_names))
        for label in blendShape_names:
            cmds.menuItem(label=label, parent=optionMenu)


#--------------------------------------------------------------------------
# 以下、コントローラー(1軸/2軸 x 片方向/双方向)共通処理
#   create1x1con/create2x1con/create1x2con/create2x2conはいずれも
#   「土台(Grp+Con+Frame)を作る→ロックする→blendShapeへ接続する→名前ラベルを置く」
#   という同じ流れなので、共通部分を関数として切り出している。
#--------------------------------------------------------------------------

def _create_base(name:str, color, frame_position, frame_size):
    """
    BlendShapeコントローラー共通の土台(親グループ・コントローラー・枠)を作成する

    Parameters
    ----------
        string name : コントローラーの名前
        (r,g,b) color : コントローラーの色
        (x,y,z) frame_position : 枠のローカル位置
        (x,y,z) frame_size : 枠のスケール

    Returns
    -------
        (parent, controller, frame) : 作成した各オブジェのフルパス
    """
    parent = cmds.group(em=True,name=f"Grp_BlendShape_{name}")
    cmds.setAttr(f"{parent}.sx",10)
    cmds.setAttr(f"{parent}.sy",10)
    cmds.setAttr(f"{parent}.sz",10)

    controller = autorig_utility.create_nurvs(name,"scuare",rotate=(90,0,0))
    controller = cmds.rename(controller,f"Con_BlendShape_{name}")
    cmds.parent(controller,parent,r=False)
    cmds.makeIdentity(controller,a=True,s=True)

    frame = autorig_utility.create_nurvs(name,"scuare",position=frame_position,size=frame_size,rotate=(90,0,0))
    frame = cmds.rename(frame,f"Frame_BlendShape_{name}")
    cmds.parent(frame,parent,r=False)
    cmds.makeIdentity(frame,a=True,s=True)

    #color
    cmds.setAttr(f"{controller}.overrideEnabled", 1)
    cmds.setAttr(f"{controller}.overrideRGBColors", 1)  # RGBを有効に
    cmds.setAttr(f"{controller}.overrideColorRGB", color[0],color[1],color[2])
    cmds.setAttr(f"{frame}.overrideEnabled",1)
    cmds.setAttr(f"{frame}.overrideDisplayType",2)  #枠は選択不可のReference表示にする

    return parent, controller, frame

def _lock_controller(controller:str, free_translate=("ty",)):
    """
    コントローラーの移動のうちfree_translateに無い軸と、回転・スケールを全てLock&Hideする

    Parameters
    ----------
        string controller : 対象コントローラー
        tuple free_translate : ロックしない移動軸("tx","ty"のように指定)
    """
    for attr in ("tx","ty","tz"):
        if(attr not in free_translate):
            cmds.setAttr(f"{controller}.{attr}", lock=True, keyable=False, channelBox=False)
    for attr in ("rx","ry","rz","sx","sy","sz"):
        cmds.setAttr(f"{controller}.{attr}", lock=True, keyable=False, channelBox=False)

def _lock_frame(frame:str):
    """枠オブジェクトは表示専用のため全チャンネルをLock&Hideする"""
    for attr in ("tx","ty","tz","rx","ry","rz","sx","sy","sz"):
        cmds.setAttr(f"{frame}.{attr}", lock=True, keyable=False, channelBox=False)

def _add_name_text(name:str, parent:str, x_offset=0):
    """
    コントローラー上部に名前ラベルのテキストカーブを作成して配置する

    Parameters
    ----------
        string name : 表示する名前(空文字なら何もしない)
        string parent : 親にするGrp
        float x_offset : ラベルのX位置補正(2軸コントローラーで中央寄せするため)
    """
    if(name==""):
        return
    text = cmds.textCurves(t=name, o=True)
    text_parent = cmds.group(name=f"Name_BlendShape_{name}",em=True)
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
        (bbox[0] + bbox[3]) * -0.5 + x_offset,
        (bbox[1] + bbox[4]) * -0.5 + 12,
        (bbox[2] + bbox[5]) * -0.5
    ]
    cmds.xform(text_parent,t=move)
    cmds.parent(text_parent,parent)
    cmds.makeIdentity(text_parent,a=True,s=True)

def _connect_bidirectional_axis(controller_attr:str, blendshape:str, shape_pos:str, shape_neg:str):
    """
    -1~1の1アトリビュートで正負2つのブレンドシェイプを駆動する
    (0より大きければshape_posへそのまま、0より小さければ符号反転してshape_negへ流す)

    Parameters
    ----------
        string controller_attr : 駆動元アトリビュート("Con.ty"等)
        string blendshape : blendShapeノード名
        string shape_pos : 正方向で駆動するターゲット名
        string shape_neg : 負方向で駆動するターゲット名
    """
    #正方向 (値 > 0 のときだけそのまま流す)
    condition_pos = cmds.createNode("condition")
    cmds.connectAttr(controller_attr,f"{condition_pos}.firstTerm")
    cmds.setAttr(F"{condition_pos}.operation",2)  #Greater Than
    cmds.connectAttr(controller_attr,f"{condition_pos}.colorIfTrueR")
    cmds.setAttr(F"{condition_pos}.secondTerm",0)
    cmds.setAttr(F"{condition_pos}.colorIfFalseR",0)
    cmds.connectAttr(f"{condition_pos}.outColorR",f"{blendshape}.{shape_pos}",f=True)

    #負方向 (値 < 0 のときだけ符号反転(×-1)して流す)
    condition_neg = cmds.createNode("condition")
    floatMath_neg = cmds.createNode("floatMath")
    cmds.connectAttr(controller_attr,f"{condition_neg}.firstTerm")
    cmds.setAttr(F"{condition_neg}.operation",4)  #Less Than
    cmds.connectAttr(controller_attr,f"{condition_neg}.colorIfTrueR")
    cmds.setAttr(F"{condition_neg}.secondTerm",0)
    cmds.setAttr(F"{condition_neg}.colorIfFalseR",0)
    cmds.connectAttr(f"{condition_neg}.outColorR",f"{floatMath_neg}.floatA",f=True)
    cmds.setAttr(F"{floatMath_neg}.floatB",-1)
    cmds.setAttr(F"{floatMath_neg}.operation",2)  #Multiply
    cmds.connectAttr(f"{floatMath_neg}.outFloat",f"{blendshape}.{shape_neg}",f=True)


def create1x1con(blendShape_textfield:str, name_textfield:str, color_colorSlider:str, blendshape_optionmenu:str):
    """
    1軸・片方向(0~1)のBlendShapeコントローラーを作成する

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

    parent,controller,frame = _create_base(name,color,frame_position=(0,5,0),frame_size=(1.2,1.2,6.2))
    _lock_controller(controller,free_translate=("ty",))
    _lock_frame(frame)
    cmds.transformLimits(controller,ty=(0,1),ety=(1,1))

    cmds.connectAttr(f"{controller}.ty",f"{blendshape}.{shape}",f=True)

    _add_name_text(name,parent)

def create2x1con(blendShape_textfield:str, name_textfield:str, color_colorSlider:str, blendshape_optionmenu1:str, blendshape_optionmenu2:str):
    """
    1軸・双方向(-1~1)のBlendShapeコントローラーを作成する

    Parameters
    ----------
        string blendShape_textfield
        string name_textfield
        string color_colorSlider
        string blendshape_optionmenu1
        string blendshape_optionmenu2

    Returns
    -------
        無し
    """
    blendshape = cmds.textField(blendShape_textfield,q=True,tx=True)
    name = cmds.textField(name_textfield,q=True,tx=True)
    color = cmds.colorSliderGrp(color_colorSlider,q=True,rgb=True)
    shape1 = cmds.optionMenu(blendshape_optionmenu1,q=True,v=True)
    shape2 = cmds.optionMenu(blendshape_optionmenu2,q=True,v=True)

    parent,controller,frame = _create_base(name,color,frame_position=(0,0,0),frame_size=(1.2,1.2,11.2))
    _lock_controller(controller,free_translate=("ty",))
    _lock_frame(frame)
    cmds.transformLimits(controller,ty=(-1,1),ety=(1,1))

    _connect_bidirectional_axis(f"{controller}.ty",blendshape,shape1,shape2)

    _add_name_text(name,parent)

def create1x2con(blendShape_textfield:str, name_textfield:str, color_colorSlider:str, blendshape_optionmenu1:str, blendshape_optionmenu2:str):
    """
    2軸・片方向(0~1 x 0~1)のBlendShapeコントローラーを作成する

    Parameters
    ----------
        string blendShape_textfield
        string name_textfield
        string color_colorSlider
        string blendshape_optionmenu1
        string blendshape_optionmenu2

    Returns
    -------
        無し
    """
    blendshape = cmds.textField(blendShape_textfield,q=True,tx=True)
    name = cmds.textField(name_textfield,q=True,tx=True)
    color = cmds.colorSliderGrp(color_colorSlider,q=True,rgb=True)
    shape1 = cmds.optionMenu(blendshape_optionmenu1,q=True,v=True)
    shape2 = cmds.optionMenu(blendshape_optionmenu2,q=True,v=True)

    parent,controller,frame = _create_base(name,color,frame_position=(5,5,0),frame_size=(6.2,1.2,6.2))
    _lock_controller(controller,free_translate=("tx","ty"))
    _lock_frame(frame)
    cmds.transformLimits(controller,ty=(0,1),ety=(1,1),tx=(0,1),etx=(1,1))

    cmds.connectAttr(f"{controller}.ty",f"{blendshape}.{shape1}",f=True)
    cmds.connectAttr(f"{controller}.tx",f"{blendshape}.{shape2}",f=True)

    _add_name_text(name,parent,x_offset=5)

def create2x2con(blendShape_textfield:str, name_textfield:str, color_colorSlider:str, blendshape_optionmenu1:str, blendshape_optionmenu2:str, blendshape_optionmenu3:str, blendshape_optionmenu4:str):
    """
    2軸・双方向(-1~1 x -1~1)のBlendShapeコントローラーを作成する

    Parameters
    ----------
        string blendShape_textfield
        string name_textfield
        string color_colorSlider
        string blendshape_optionmenu1
        string blendshape_optionmenu2
        string blendshape_optionmenu3
        string blendshape_optionmenu4

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

    parent,controller,frame = _create_base(name,color,frame_position=(0,0,0),frame_size=(11.2,1.2,11.2))
    _lock_controller(controller,free_translate=("tx","ty"))
    _lock_frame(frame)
    cmds.transformLimits(controller,ty=(-1,1),ety=(1,1),tx=(-1,1),etx=(1,1))

    _connect_bidirectional_axis(f"{controller}.ty",blendshape,shape1,shape2)
    _connect_bidirectional_axis(f"{controller}.tx",blendshape,shape3,shape4)

    _add_name_text(name,parent)
