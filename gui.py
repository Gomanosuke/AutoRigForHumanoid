from maya import cmds
from maya import OpenMaya
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
    fbx_frame(main_layout)
    create_frame = cmds.frameLayout(label="リギング",parent=main_layout,collapsable=True)
    setup_list = humanoid_setup(create_frame)
    autorig_frame(create_frame,setup_list[1],setup_list[0])
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
    fbx_frame = cmds.frameLayout(label="FBX Shapeリネーム",parent=parent_layout,collapsable=True)

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

    textField_dic:dict
    textField_dic = body_frame(setup_frame,str_cw)
    textField_dic |= head_frame(setup_frame,str_cw)
    textField_dic |= lefthand_frame(setup_frame,str_cw)
    textField_dic |= righthand_frame(setup_frame,str_cw)

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

    #body
    body_tab = cmds.frameLayout(label="Body",parent=setup_frame,collapsable=True,p=setup_frame)
    #Body
    body_frame = cmds.frameLayout(label="Body",parent=body_tab,collapsable=True,p=setup_frame)
    #hips
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=body_frame)
    cmds.text(label="Hips : ")
    hips = cmds.textField()
    textField_dic["c_hips"]=hips
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(hips))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(hips))
    #spine
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=body_frame)
    cmds.text(label="Spine : ")
    spine = cmds.textField()
    textField_dic["c_spine"]=spine
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(spine))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(spine))
    #chest
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=body_frame)
    cmds.text(label="Chest : ")
    chest = cmds.textField()
    textField_dic["c_chest"]=chest
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(chest))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(chest))
    #upper_chest
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=body_frame)
    cmds.text(label="Upper Chest : ")
    upper_chest = cmds.textField()
    textField_dic["c_upperChest"]=upper_chest
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(upper_chest))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(upper_chest))

    #LeftArm
    LeftArm_frame = cmds.frameLayout(label="Left Arm",parent=body_tab,collapsable=True,p=setup_frame)
    #shoulder
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=LeftArm_frame)
    cmds.text(label="Shoulder : ")
    left_shoulder = cmds.textField()
    textField_dic["l_shoulder"]=left_shoulder
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(left_shoulder))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(left_shoulder))
    #upper_arm
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=LeftArm_frame)
    cmds.text(label="Upper Arm : ")
    left_upper_arm = cmds.textField()
    textField_dic["l_upperArm"]=left_upper_arm
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(left_upper_arm))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(left_upper_arm))
    #lower_arm
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=LeftArm_frame)
    cmds.text(label="Lower Arm : ")
    left_lower_arm = cmds.textField()
    textField_dic["l_lowerArm"]=left_lower_arm
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(left_lower_arm))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(left_lower_arm))
    #hand
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=LeftArm_frame)
    cmds.text(label="Hand : ")
    left_hand = cmds.textField()
    textField_dic["l_hand"]=left_hand
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(left_hand))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(left_hand))

    #RightArm
    RightArm_frame = cmds.frameLayout(label="Right Arm",parent=body_tab,collapsable=True,p=setup_frame)
    #shoulder
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=RightArm_frame)
    cmds.text(label="Shoulder : ")
    right_shoulder = cmds.textField()
    textField_dic["r_shoulder"]=right_shoulder
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(right_shoulder))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(right_shoulder))
    #upper_arm
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=RightArm_frame)
    cmds.text(label="Upper Arm : ")
    right_upper_arm = cmds.textField()
    textField_dic["r_upperArm"]=right_upper_arm
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(right_upper_arm))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(right_upper_arm))
    #lower_arm
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=RightArm_frame)
    cmds.text(label="Lower Arm : ")
    right_lower_arm = cmds.textField()
    textField_dic["r_lowerArm"]=right_lower_arm
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(right_lower_arm))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(right_lower_arm))
    #hand
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=RightArm_frame)
    cmds.text(label="Hand : ")
    right_hand = cmds.textField()
    textField_dic["r_hand"]=right_hand
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(right_hand))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(right_hand))

    #LeftLeg
    LeftLeg_frame = cmds.frameLayout(label="Left Leg",parent=body_tab,collapsable=True,p=setup_frame)
    #upper_leg
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=LeftLeg_frame)
    cmds.text(label="Upper Leg : ")
    left_upper_leg = cmds.textField()
    textField_dic["l_upperLeg"]=left_upper_leg
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(left_upper_leg))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(left_upper_leg))
    #lower_leg
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=LeftLeg_frame)
    cmds.text(label="Lower Leg : ")
    left_lower_leg = cmds.textField()
    textField_dic["l_lowerLeg"]=left_lower_leg
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(left_lower_leg))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(left_lower_leg))
    #Foot
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=LeftLeg_frame)
    cmds.text(label="Foot : ")
    left_foot = cmds.textField()
    textField_dic["l_foot"]=left_foot
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(left_foot))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(left_foot))
    #Toes
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=LeftLeg_frame)
    cmds.text(label="Toes : ")
    left_toes = cmds.textField()
    textField_dic["l_toes"]=left_toes
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(left_toes))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(left_toes))

    #RightLeg
    RightLeg_frame = cmds.frameLayout(label="Right Leg",parent=body_tab,collapsable=True,p=setup_frame)
    #upper_leg
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=RightLeg_frame)
    cmds.text(label="Upper Leg : ")
    right_upper_leg = cmds.textField()
    textField_dic["r_upperLeg"]=right_upper_leg
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(right_upper_leg))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(right_upper_leg))
    #lower_leg
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=RightLeg_frame)
    cmds.text(label="Lower Leg : ")
    right_lower_leg = cmds.textField()
    textField_dic["r_lowerLeg"]=right_lower_leg
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(right_lower_leg))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(right_lower_leg))
    #Foot
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=RightLeg_frame)
    cmds.text(label="Foot : ")
    right_foot = cmds.textField()
    textField_dic["r_foot"]=right_foot
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(right_foot))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(right_foot))
    #Toes
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=RightLeg_frame)
    cmds.text(label="Toes : ")
    right_toes = cmds.textField()
    textField_dic["r_toes"]=right_toes
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(right_toes))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(right_toes))

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

    #head
    head_tab = cmds.frameLayout(label="Head",parent=setup_frame,collapsable=True,p=setup_frame)
    #neck
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Neck : ")
    neck = cmds.textField()
    textField_dic["c_neck"]=neck
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(neck))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(neck))
    #head
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Head : ")
    head = cmds.textField()
    textField_dic["c_head"]=head
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(head))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(head))
    #left eye
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Left Eye : ")
    left_eye = cmds.textField()
    textField_dic["l_eye"]=left_eye
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(left_eye))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(left_eye))
    #right eye
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Right Eye : ")
    right_eye = cmds.textField()
    textField_dic["r_eye"]=right_eye
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(right_eye))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(right_eye))
    #jaw
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Jaw : ")
    jaw = cmds.textField()
    textField_dic["c_jaw"]=jaw
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(jaw))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(jaw))

    return textField_dic

def lefthand_frame(setup_frame:str, str_cw:int):
    """
    Lefthandの入力欄

    Parameters
    ----------
        string setup_frame : 親のレイアウト名
        int str_cw : 文字の横幅

    Returns
    -------
        dictionary : テキストフィールドの辞書
    """
    textField_dic={}

    #hand
    head_tab = cmds.frameLayout(label="Left Hand",parent=setup_frame,collapsable=True,p=setup_frame)
    #thumb1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Thumb Proximal : ")
    thumb1 = cmds.textField()
    textField_dic["l_thumb1"]=thumb1
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(thumb1))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(thumb1))
    #thumb2
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Thumb Intermediate : ")
    thumb2 = cmds.textField()
    textField_dic["l_thumb2"]=thumb2
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(thumb2))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(thumb2))
    #thumb1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Thumb Distal : ")
    thumb3 = cmds.textField()
    textField_dic["l_thumb3"]=thumb3
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(thumb3))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(thumb3))

    #index1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Index Proximal : ")
    index1 = cmds.textField()
    textField_dic["l_index1"]=index1
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(index1))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(index1))
    #index2
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Index Intermediate : ")
    index2 = cmds.textField()
    textField_dic["l_index2"]=index2
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(index2))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(index2))
    #index1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Index Distal : ")
    index3 = cmds.textField()
    textField_dic["l_index3"]=index3
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(index3))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(index3))

    #middle1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Middle Proximal : ")
    middle1 = cmds.textField()
    textField_dic["l_middle1"]=middle1
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(middle1))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(middle1))
    #middle2
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Middle Intermediate : ")
    middle2 = cmds.textField()
    textField_dic["l_middle2"]=middle2
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(middle2))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(middle2))
    #middle1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Middle Distal : ")
    middle3 = cmds.textField()
    textField_dic["l_middle3"]=middle3
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(middle3))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(middle3))

    #ring1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Ring Proximal : ")
    ring1 = cmds.textField()
    textField_dic["l_ring1"]=ring1
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(ring1))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(ring1))
    #ring2
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Ring Intermediate : ")
    ring2 = cmds.textField()
    textField_dic["l_ring2"]=ring2
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(ring2))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(ring2))
    #ring1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Ring Distal : ")
    ring3 = cmds.textField()
    textField_dic["l_ring3"]=ring3
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(ring3))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(ring3))

    #little1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Little Proximal : ")
    little1 = cmds.textField()
    textField_dic["l_little1"]=little1
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(little1))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(little1))
    #little2
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Little Intermediate : ")
    little2 = cmds.textField()
    textField_dic["l_little2"]=little2
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(little2))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(little2))
    #little1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Little Distal : ")
    little3 = cmds.textField()
    textField_dic["l_little3"]=little3
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(little3))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(little3))

    return textField_dic

def righthand_frame(setup_frame:str, str_cw:int):
    """
    Lefthandの入力欄

    Parameters
    ----------
        string setup_frame : 親のレイアウト名
        int str_cw : 文字の横幅

    Returns
    -------
        dictionary : テキストフィールドの辞書
    """
    textField_dic={}

    #hand
    head_tab = cmds.frameLayout(label="Right Hand",parent=setup_frame,collapsable=True,p=setup_frame)
    #thumb1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Thumb Proximal : ")
    thumb1 = cmds.textField()
    textField_dic["r_thumb1"]=thumb1
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(thumb1))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(thumb1))
    #thumb2
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Thumb Intermediate : ")
    thumb2 = cmds.textField()
    textField_dic["r_thumb2"]=thumb2
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(thumb2))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(thumb2))
    #thumb1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Thumb Distal : ")
    thumb3 = cmds.textField()
    textField_dic["r_thumb3"]=thumb3
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(thumb3))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(thumb3))

    #index1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Index Proximal : ")
    index1 = cmds.textField()
    textField_dic["r_index1"]=index1
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(index1))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(index1))
    #index2
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Index Intermediate : ")
    index2 = cmds.textField()
    textField_dic["r_index2"]=index2
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(index2))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(index2))
    #index1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Index Distal : ")
    index3 = cmds.textField()
    textField_dic["r_index3"]=index3
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(index3))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(index3))

    #middle1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Middle Proximal : ")
    middle1 = cmds.textField()
    textField_dic["r_middle1"]=middle1
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(middle1))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(middle1))
    #middle2
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Middle Intermediate : ")
    middle2 = cmds.textField()
    textField_dic["r_middle2"]=middle2
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(middle2))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(middle2))
    #middle1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Middle Distal : ")
    middle3 = cmds.textField()
    textField_dic["r_middle3"]=middle3
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(middle3))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(middle3))

    #ring1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Ring Proximal : ")
    ring1 = cmds.textField()
    textField_dic["r_ring1"]=ring1
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(ring1))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(ring1))
    #ring2
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Ring Intermediate : ")
    ring2 = cmds.textField()
    textField_dic["r_ring2"]=ring2
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(ring2))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(ring2))
    #ring1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Ring Distal : ")
    ring3 = cmds.textField()
    textField_dic["r_ring3"]=ring3
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(ring3))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(ring3))

    #little1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Little Proximal : ")
    little1 = cmds.textField()
    textField_dic["r_little1"]=little1
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(little1))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(little1))
    #little2
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Little Intermediate : ")
    little2 = cmds.textField()
    textField_dic["r_little2"]=little2
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(little2))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(little2))
    #little1
    cmds.rowLayout(nc=4,adjustableColumn=2,cw=[1,str_cw],p=head_tab)
    cmds.text(label="Little Distal : ")
    little3 = cmds.textField()
    textField_dic["r_little3"]=little3
    cmds.button(label="割り当て",command=lambda *_:auto_apply.attach(little3))
    cmds.button(label="選択",command=lambda *_:auto_apply.select(little3))

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
    cmds.button(label="基準作成",command=lambda *_:autorig_preparation.do(textField_dic=textField_dic,character_name=character_name,primary_axis=cmds.optionMenu(primary_option,q=True,sl=True)))

    cmds.rowLayout(nc=4,p=setup_frame)
    cmds.text(l="90°回転")
    rotate_w = 30
    cmds.button(label="X",command=lambda *_:autorig_preparation.rotate_90("X"),w=rotate_w)
    cmds.button(label="Y",command=lambda *_:autorig_preparation.rotate_90("Y"),w=rotate_w)
    cmds.button(label="Z",command=lambda *_:autorig_preparation.rotate_90("Z"),w=rotate_w)

    cmds.button(label="リグ作成",command=lambda *_:autorig_createBase.create_rig(textField_dic=textField_dic,character_name=character_name),p=setup_frame)

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

