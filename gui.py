from maya import cmds
import importlib

from . import auto_apply
importlib.reload(auto_apply)
from . import autorig_preparation
importlib.reload(autorig_preparation)
from . import autorig_createBase
importlib.reload(autorig_createBase)
from . import blendshape
importlib.reload(blendshape)
from . import fbx_shape_rename
importlib.reload(fbx_shape_rename)
from . import picker
importlib.reload(picker)
from . import control_shape
importlib.reload(control_shape)
from . import rig_import
importlib.reload(rig_import)

def create_window():
    """
    ウィンドウを表示する

    Parameters
    ----------
        無し

    Returns
    -------
        無し
    """
    windowname = "AutoRigForHumanoid"

    #古いウィンドウ削除 新規作成
    if cmds.window(windowname, exists=True):
        cmds.deleteUI(windowname)
    cmds.window(windowname)

    # メインレイアウト作成
    main_layout = cmds.scrollLayout(horizontalScrollBarThickness=16, verticalScrollBarThickness=16, childResizable=True)

    #各レイアウト読み込み
    show_picker(main_layout)
    unity_fbx_frame(main_layout)
    fbx_frame(main_layout)
    create_frame = cmds.frameLayout(label="リギング",parent=main_layout,collapsable=True)
    setup_list = humanoid_setup(create_frame)
    autorig_frame(create_frame,setup_list[1],setup_list[0])
    control_shape_frame(create_frame)
    rig_import_frame(create_frame)
    blendshape_frame(main_layout,setup_list[0])

    #タブの表示
    cmds.showWindow(windowname)

def show_picker(parent_layout:str):
    """
    ピッカー表示

    Parameters
    ----------
        string parent_layout : 親のレイアウト名

    Returns
    -------
        list [character_name,textField_dic]
    """
    #フレーム
    picker_frame = cmds.frameLayout(label="Picker",parent=parent_layout,collapsable=True)

    cmds.button(label="Picker表示",h=50,command=lambda *_:picker.show_ui())

def unity_fbx_frame(parent_layout:str):
    frame = cmds.frameLayout(label="Unity FBX", parent=parent_layout, collapsable=True)
    cmds.button(
        label="Unity用FBXエクスポーターを開く",
        parent=frame,
        height=40,
        annotation="元シーンを保護してアニメーション付きFBXを書き出す画面を開きます。",
        command=_show_unity_fbx_export,
    )

def _show_unity_fbx_export(*_):
    from . import unity_fbx_export
    unity_fbx_export.show()

def fbx_frame(parent_layout:str):
    """
    FBXから日本語削除

    Parameters
    ----------
        string parent_layout : 親のレイアウト名

    Returns
    -------
        list [character_name,textField_dic]
    """
    #フレーム
    fbx_frame = cmds.frameLayout(label="Edit FBX",parent=parent_layout,collapsable=True)

    path_list=[]

    cmds.rowLayout(nc=3,adjustableColumn=2,p=fbx_frame)
    cmds.text(label="Import FBX :")
    import_fbx_path = cmds.textField()
    path_list.append(import_fbx_path)
    cmds.button(label="参照",command=lambda *_:fbx_shape_rename.import_path(path_list))

    cmds.rowLayout(nc=3,adjustableColumn=2,p=fbx_frame)
    cmds.text(label="Json :")
    json_path = cmds.textField()
    path_list.append(json_path)
    cmds.button(label="参照",command=lambda *_:fbx_shape_rename.json_path(path_list))

    cmds.rowLayout(nc=3,adjustableColumn=2,p=fbx_frame)
    cmds.text(label="Export FBX :")
    export_fbx_path = cmds.textField()
    path_list.append(export_fbx_path)
    cmds.button(label="参照",command=lambda *_:fbx_shape_rename.export_path(path_list))

    cmds.rowLayout(nc=1,adjustableColumn=2,p=fbx_frame)
    cmds.button(label="Json出力",command=lambda *_:fbx_shape_rename.export_json(path_list))

    cmds.rowLayout(nc=2,adjustableColumn=3,p=fbx_frame)
    option = cmds.optionMenu(label="モード")
    cmds.menuItem( label="Kay To Value", )
    cmds.menuItem( label="Value To Kay", )
    cmds.button(label="FBX出力",command=lambda *_:fbx_shape_rename.export_fbx_init(path_list,cmds.optionMenu(option,q=True,sl=True)))

    cmds.rowLayout(nc=1,adjustableColumn=1,p=fbx_frame)
    cmds.button(label="Import FBX",command=lambda *_:fbx_shape_rename.import_fbx())

    cmds.rowLayout(nc=1,adjustableColumn=1,p=fbx_frame)
    cmds.button(label="Freeze Scale",command=lambda *_:fbx_shape_rename.fix_skin_scale_offset())

def _joint_field(parent:str, label:str, key:str, textField_dic:dict, str_cw:int):
    """
    「ラベル・入力欄・割り当てボタン・選択ボタン」の1行を作成し、textField_dicへ{key: 入力欄}を登録する。
    joint系の入力欄はどれもこの並びの繰り返しのため、共通処理として切り出している。

    Parameters
    ----------
        string parent : 親のレイアウト名
        string label : 表示ラベル
        string key : textField_dicへ登録するキー(joint_name.jsonのキーと対応させる)
        dictionary textField_dic : 登録先の辞書
        int str_cw : ラベル列の幅

    Returns
    -------
        string : 作成した入力欄(textField)の名前
    """
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=parent)
    cmds.text(label=f"{label} : ")
    field = cmds.textField()
    textField_dic[key]=field
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(field))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(field))
    return field

def humanoid_setup(parent_layout:str):
    """
    モデルの情報入力する場所作る

    Parameters
    ----------
        string parent_layout : 親のレイアウト名

    Returns
    -------
        list [character_name,textField_dic]
    """
    #フレーム
    setup_frame = cmds.frameLayout(label="初期設定",parent=parent_layout,collapsable=True)
    #名前幅
    str_cw=120

    #名前
    cmds.rowLayout(nc=2,adjustableColumn=2,p=setup_frame)
    cmds.text(label="キャラクター名 : ")
    character_name = cmds.textField(tx="name")

    textField_dic = body_frame(setup_frame,str_cw)
    textField_dic |= head_frame(setup_frame,str_cw)
    textField_dic |= hand_frame(setup_frame,str_cw,"l","Left")
    textField_dic |= hand_frame(setup_frame,str_cw,"r","Right")

    auto_apply_frame(setup_frame,textField_dic)

    return [character_name,textField_dic]

def body_frame(setup_frame:str, str_cw:int):
    """
    Bodyの入力欄

    Parameters
    ----------
        string setup_frame : 親のレイアウト名
        int str_cw : 文字の横幅

    Returns
    -------
        dictionary : テキストフィールドの辞書
    """
    textField_dic={}

    body_tab = cmds.frameLayout(label="Body",parent=setup_frame,collapsable=True,p=setup_frame)

    #Body
    body_part_frame = cmds.frameLayout(label="Body",parent=body_tab,collapsable=True,p=setup_frame)
    _joint_field(body_part_frame,"Hips","c_hips",textField_dic,str_cw)
    _joint_field(body_part_frame,"Spine","c_spine",textField_dic,str_cw)
    _joint_field(body_part_frame,"Chest","c_chest",textField_dic,str_cw)
    _joint_field(body_part_frame,"Upper Chest","c_upperChest",textField_dic,str_cw)

    #Arm(Left→Rightの順に表示。左右対称なので共通処理でまとめる)
    for side,side_label in (("l","Left"),("r","Right")):
        arm_frame = cmds.frameLayout(label=f"{side_label} Arm",parent=body_tab,collapsable=True,p=setup_frame)
        _joint_field(arm_frame,"Shoulder",f"{side}_shoulder",textField_dic,str_cw)
        _joint_field(arm_frame,"Upper Arm",f"{side}_upperArm",textField_dic,str_cw)
        _joint_field(arm_frame,"Lower Arm",f"{side}_lowerArm",textField_dic,str_cw)
        _joint_field(arm_frame,"Hand",f"{side}_hand",textField_dic,str_cw)

    #Leg(Left→Rightの順に表示)
    for side,side_label in (("l","Left"),("r","Right")):
        leg_frame = cmds.frameLayout(label=f"{side_label} Leg",parent=body_tab,collapsable=True,p=setup_frame)
        _joint_field(leg_frame,"Upper Leg",f"{side}_upperLeg",textField_dic,str_cw)
        _joint_field(leg_frame,"Lower Leg",f"{side}_lowerLeg",textField_dic,str_cw)
        _joint_field(leg_frame,"Foot",f"{side}_foot",textField_dic,str_cw)
        _joint_field(leg_frame,"Toes",f"{side}_toes",textField_dic,str_cw)

    return textField_dic

def head_frame(setup_frame:str, str_cw:int):
    """
    Headの入力欄

    Parameters
    ----------
        string setup_frame : 親のレイアウト名
        int str_cw : 文字の横幅

    Returns
    -------
        dictionary : テキストフィールドの辞書
    """
    textField_dic={}

    head_tab = cmds.frameLayout(label="Head",parent=setup_frame,collapsable=True,p=setup_frame)
    _joint_field(head_tab,"Neck","c_neck",textField_dic,str_cw)
    _joint_field(head_tab,"Head","c_head",textField_dic,str_cw)
    _joint_field(head_tab,"Left Eye","l_eye",textField_dic,str_cw)
    _joint_field(head_tab,"Right Eye","r_eye",textField_dic,str_cw)
    _joint_field(head_tab,"Jaw","c_jaw",textField_dic,str_cw)

    return textField_dic

#指の並び(表示名, 関節ラベル)。joint_name.jsonのキーは f"{side}_{指名.lower()}{番号}" の形。
_FINGERS = ("Thumb","Index","Middle","Ring","Little")
_PHALANGES = (("1","Proximal"),("2","Intermediate"),("3","Distal"))
#Metacarpal(0番目の関節)はThumbには存在しない
_METACARPAL_FINGERS = ("index","middle","ring","little")

def hand_frame(setup_frame:str, str_cw:int, side:str, side_label:str):
    """
    片手ぶんの指の入力欄(旧lefthand_frame/righthand_frameの共通実装)

    Parameters
    ----------
        string setup_frame : 親のレイアウト名
        int str_cw : 文字の横幅
        string side : "l"または"r"(joint_name.jsonのキー接頭辞と対応)
        string side_label : 表示用ラベル("Left"/"Right")

    Returns
    -------
        dictionary : テキストフィールドの辞書
    """
    textField_dic={}

    hand_tab = cmds.frameLayout(label=f"{side_label} Hand",parent=setup_frame,collapsable=True,p=setup_frame)

    for finger in _FINGERS:
        for number,phalange_label in _PHALANGES:
            _joint_field(hand_tab,f"{finger} {phalange_label}",f"{side}_{finger.lower()}{number}",textField_dic,str_cw)

    for finger in _METACARPAL_FINGERS:
        _joint_field(hand_tab,f"{finger.capitalize()} Metacarpal",f"{side}_{finger}0",textField_dic,str_cw)

    return textField_dic

def auto_apply_frame(setup_frame:str,textField_dic:dict):
    """
    入力欄に自動入力

    Parameters
    ----------
        string setup_frame : 親のレイアウト名
        dictionary textfield : Joint名のテキストボックスが入った辞書

    Returns
    -------
        無し
    """
    cmds.rowLayout(nc=2,p=setup_frame)
    fullpath_checkBox = cmds.checkBox(label="フルパス",v=True)
    cmds.button(label="自動割り当て",command=lambda *_:auto_apply.auto(fullpath=cmds.checkBox(fullpath_checkBox,q=True,v=True), textfield=textField_dic))

def autorig_frame(parent_layout:str,textField_dic:dict,character_name:str):
    """
    リグ制作のGUI

    Parameters
    ----------
    string parent_layout : 親のレイアウト名
        dictionary textfield : Joint名のテキストボックスが入った辞書
        string character_name : 名前を入れるテキストボックス

    Returns
    -------
        無し
    """
    #フレーム
    setup_frame = cmds.frameLayout(label="リグ制作",parent=parent_layout,collapsable=True)

    cmds.rowLayout(nc=2,p=setup_frame)
    primary_option = cmds.optionMenu(label="主軸")
    cmds.menuItem( label="X", )
    cmds.menuItem( label="Y", )
    cmds.menuItem( label="Z")
    cmds.button(label="ガイド作成",command=lambda *_:autorig_preparation.do(textField_dic=textField_dic,character_name=character_name,primary_axis=cmds.optionMenu(primary_option,q=True,sl=True)))

    cmds.rowLayout(nc=4,p=setup_frame)
    cmds.text(l="90°回転")
    rotate_w = 30
    cmds.button(label="X",command=lambda *_:autorig_preparation.rotate_90("X"),w=rotate_w)
    cmds.button(label="Y",command=lambda *_:autorig_preparation.rotate_90("Y"),w=rotate_w)
    cmds.button(label="Z",command=lambda *_:autorig_preparation.rotate_90("Z"),w=rotate_w)

    cmds.button(label="リグ作成",command=lambda *_:autorig_createBase.create_rig(textField_dic=textField_dic,character_name=character_name),p=setup_frame)

def control_shape_frame(parent_layout:str):
    """
    コントローラーのカーブ形状(CV座標)をjsonへ書き出し/読み込みするGUI。
    シェイプをCV単位で手直しした後にリグを作り直す必要があっても、このjsonを経由すれば
    手直ししたシェイプを作り直さずに済む(control_shape.py参照)。

    対象は選択中のコントローラー(またはリグのトップグループ等、選択したものの子孫のCon_*)。
    何も選択していなければシーン内の全Con_*が対象になる。

    Parameters
    ----------
        string parent_layout : 親のレイアウト名

    Returns
    -------
        無し
    """
    #フレーム
    shape_frame = cmds.frameLayout(label="コントロールシェイプ",parent=parent_layout,collapsable=True)

    cmds.rowLayout(nc=3,adjustableColumn=2,p=shape_frame)
    cmds.text(label="Export Shape Path: ")
    export_path_field = cmds.textField()
    cmds.button(label="参照",command=lambda *_:control_shape.browse_export_path(export_path_field))

    cmds.rowLayout(nc=1,adjustableColumn=1,p=shape_frame)
    cmds.button(label="Export Shape",command=lambda *_:control_shape.export_shapes(cmds.textField(export_path_field,q=True,tx=True)))

    cmds.rowLayout(nc=3,adjustableColumn=2,p=shape_frame)
    cmds.text(label="Import Shape Path : ")
    import_path_field = cmds.textField()
    cmds.button(label="参照",command=lambda *_:control_shape.browse_import_path(import_path_field))

    cmds.rowLayout(nc=1,adjustableColumn=1,p=shape_frame)
    cmds.button(label="Import Shape",command=lambda *_:control_shape.import_shapes(cmds.textField(import_path_field,q=True,tx=True)))

def rig_import_frame(parent_layout:str):
    """
    別ファイルで作成したrigを現在のシーンへ読み込むGUI。

    Picker(picker.py)はコントローラー等をUUIDで管理しているため、単純な
    インポートでは(Mayaのインポートは名前の衝突が無くてもUUIDを再割り当てして
    しまうため)読み込み後にPickerが対象を見つけられなくなる。ここから読み込むと、
    リグ作成時に記録されている元のUUIDへ復元してから読み込みを完了する
    (詳細はrig_import.py参照)。

    Parameters
    ----------
        string parent_layout : 親のレイアウト名

    Returns
    -------
        無し
    """
    #フレーム
    import_frame = cmds.frameLayout(label="リグ読み込み",parent=parent_layout,collapsable=True)

    cmds.rowLayout(nc=3,adjustableColumn=2,p=import_frame)
    cmds.text(label="Maya Scene : ")
    import_rig_path_field = cmds.textField()
    cmds.button(label="参照",command=lambda *_:rig_import.browse_import_rig_path(import_rig_path_field))

    cmds.rowLayout(nc=1,adjustableColumn=1,p=import_frame)
    cmds.button(label="Import Rig",command=lambda *_:rig_import.import_rig(cmds.textField(import_rig_path_field,q=True,tx=True)))

def blendshape_frame(parent_layout:str,character_name:str):
    """
    リグ制作のGUI

    Parameters
    ----------
    string parent_layout : 親のレイアウト名
        string character_name : 名前を入れるテキストボックス

    Returns
    -------
        無し
    """
    #フレーム
    blendshape_frame = cmds.frameLayout(label="ブレンドシェイプコントローラー",parent=parent_layout,collapsable=True)

    width=360

    #メッシュ
    cmds.rowLayout(nc=4,adjustableColumn=2,p=blendshape_frame)
    cmds.text(label="オブジェクト : ")
    obj = cmds.textField()
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(obj,"transform"))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(obj))

    cmds.rowLayout(nc=4,adjustableColumn=2,p=blendshape_frame)
    cmds.text(label="シェイプ : ")
    shape = cmds.textField()
    cmds.button(label="自動割り当て",command=lambda *_:blendshape.meshattach(shape,obj))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(shape))

    cmds.rowLayout(nc=4,adjustableColumn=2,p=blendshape_frame)
    cmds.text(label="スキンクラスター : ")
    skinCluster = cmds.textField()
    cmds.button(label="自動割り当て",command=lambda *_:blendshape.sourcenodeattach(skinCluster,shape,"skinCluster"))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(skinCluster))

    cmds.rowLayout(nc=4,adjustableColumn=2,p=blendshape_frame)
    cmds.text(label="ブレンドシェイプ : ")
    blendShape = cmds.textField()
    cmds.button(label="自動割り当て",command=lambda *_:blendshape.sourcenodeattach(blendShape,skinCluster,"blendShape"))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(blendShape))

    cmds.rowLayout(nc=1,adjustableColumn=2,p=blendshape_frame)
    optionMenus = []
    cmds.button(label="適用",command=lambda *_:blendshape.setOptionMenu(optionMenus,blendShape))

    #1*1コントローラー
    frame1x1 = cmds.frameLayout(label="1*1コントローラー",parent=blendshape_frame,collapsable=True)
    cmds.rowLayout(nc=2,adjustableColumn=2,p=frame1x1)
    cmds.text(label="名前 : ")
    name1x1 = cmds.textField()
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame1x1)
    color1x1 = cmds.colorSliderGrp(label="カラー",rgbValue=[1,0.5,0])
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame1x1)
    blendshape1_1x1 = cmds.optionMenu(label="ブレンドシェイプ", w=width)
    optionMenus.append(blendshape1_1x1)
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame1x1)
    cmds.button(label="作成",command=lambda *_:blendshape.create1x1con(blendShape,name1x1,color1x1,blendshape1_1x1))

    #2*1コントローラー
    frame2x1 = cmds.frameLayout(label="2*1コントローラー",parent=blendshape_frame,collapsable=True)
    cmds.rowLayout(nc=2,adjustableColumn=2,p=frame2x1)
    cmds.text(label="名前 : ")
    name2x1 = cmds.textField()
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame2x1)
    color2x1 = cmds.colorSliderGrp(label="カラー",rgbValue=[1,0.5,0])
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame2x1)
    blendshape1_2x1 = cmds.optionMenu(label="ブレンドシェイプ プラス", w=width)
    optionMenus.append(blendshape1_2x1)
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame2x1)
    blendshape2_2x1 = cmds.optionMenu(label="ブレンドシェイプ マイナス", w=width)
    optionMenus.append(blendshape2_2x1)
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame2x1)
    cmds.button(label="作成",command=lambda *_:blendshape.create2x1con(blendShape,name2x1,color2x1,blendshape1_2x1,blendshape2_2x1))

    #1*2コントローラー
    frame1x2 = cmds.frameLayout(label="1*2コントローラー",parent=blendshape_frame,collapsable=True)
    cmds.rowLayout(nc=2,adjustableColumn=2,p=frame1x2)
    cmds.text(label="名前 : ")
    name1x2 = cmds.textField()
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame1x2)
    color1x2 = cmds.colorSliderGrp(label="カラー",rgbValue=[1,0.5,0])
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame1x2)
    blendshape1_1x2 = cmds.optionMenu(label="ブレンドシェイプ1", w=width)
    optionMenus.append(blendshape1_1x2)
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame1x2)
    blendshape2_1x2 = cmds.optionMenu(label="ブレンドシェイプ2", w=width)
    optionMenus.append(blendshape2_1x2)
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame1x2)
    cmds.button(label="作成",command=lambda *_:blendshape.create1x2con(blendShape,name1x2,color1x2,blendshape1_1x2,blendshape2_1x2))

    #2*2コントローラー
    frame2x2 = cmds.frameLayout(label="2*2コントローラー",parent=blendshape_frame,collapsable=True)
    cmds.rowLayout(nc=2,adjustableColumn=2,p=frame2x2)
    cmds.text(label="名前 : ")
    name2x2 = cmds.textField()
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame2x2)
    color2x2 = cmds.colorSliderGrp(label="カラー",rgbValue=[1,0.5,0])
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame2x2)
    blendshape1_2x2 = cmds.optionMenu(label="ブレンドシェイプ1 プラス", w=width)
    optionMenus.append(blendshape1_2x2)
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame2x2)
    blendshape2_2x2 = cmds.optionMenu(label="ブレンドシェイプ1 マイナス", w=width)
    optionMenus.append(blendshape2_2x2)
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame2x2)
    blendshape3_2x2 = cmds.optionMenu(label="ブレンドシェイプ2 プラス", w=width)
    optionMenus.append(blendshape3_2x2)
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame2x2)
    blendshape4_2x2 = cmds.optionMenu(label="ブレンドシェイプ2 マイナス", w=width)
    optionMenus.append(blendshape4_2x2)
    cmds.rowLayout(nc=1,adjustableColumn=2,p=frame2x2)
    cmds.button(label="作成",command=lambda *_:blendshape.create2x2con(blendShape,name2x2,color2x2,blendshape1_2x2,blendshape2_2x2,blendshape3_2x2,blendshape4_2x2))
