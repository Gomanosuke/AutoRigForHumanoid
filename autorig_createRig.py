from maya import cmds
from maya.api import OpenMaya
from pathlib import Path
import json
import importlib
import math

from . import autorig_utility
importlib.reload(autorig_utility)

#json読み込み
with open(f"{Path(__file__).resolve().parent}/joint_name.json", mode="rt", encoding="utf-8") as f:
    joint_name = json.load(f)

def init_createRig(joint_dic:dict, character_name:str, parent:str, orientation_dic:dict , pos_dic:dict):
    """
    リグ作成

    Parameters
    ----------
        dictionary joint_dic : HumanoidJointが入った辞書
        string character_name : 名前
        string parent : 親になるオブジェクト
        dictionary orientation_dic : 回転の基準
        dictionary pos_dic : 位置の基準

    Returns
    -------
        無し
    """
    obj_dic={}


    #すべての親作成
    rig_grp = cmds.group(em=True,n=f"Grp_C_{character_name}Rig",p=parent)
    cmds.setAttr(f"{rig_grp}.t",lock=True)
    cmds.setAttr(f"{rig_grp}.r",lock=True)
    cmds.setAttr(f"{rig_grp}.s",lock=True)
    obj_dic[("Grp","C",f"{character_name}Rig")]=rig_grp

    #コントローラ作成
    obj_dic |= create_root(character_name,rig_grp)
    obj_dic |= create_body(character_name,rig_grp,obj_dic,joint_dic,orientation_dic)
    obj_dic |= create_head(character_name,rig_grp,obj_dic,joint_dic,orientation_dic)
    obj_dic |= create_leg(character_name,rig_grp,obj_dic,joint_dic,orientation_dic,pos_dic)
    obj_dic |= create_arm(character_name,rig_grp,obj_dic,joint_dic,orientation_dic)
    obj_dic |= create_hand(character_name,rig_grp,obj_dic,joint_dic,orientation_dic)
    clean_obj(character_name,obj_dic)

def create_root(character_name:str, parent:str):
    """
    リグ作成

    Parameters
    ----------
        string character_name : 名前
        string parent : 親になるオブジェクト

    Returns
    -------
        作成したオブジェ入った辞書
    """
    #親作成
    root_obj = cmds.group(em=True,n=f"Grp_C_Root",p=parent)
    cmds.setAttr( f"{root_obj}.t", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{root_obj}.r", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{root_obj}.s", lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f"{root_obj}.v",keyable=False,channelBox=True)
    #SettingObj
    create_obj_dic = autorig_utility.create_controller("Setting",root_obj,pos_CLR="C",con_shape="unity",con_color=[0.9,0.9,0.9],pos=(0,0,20),
                                                        con_pos_lock=(True,True,True),con_rot_lock=(True,True,True),con_scl_lock=(True,True,True))
    cmds.addAttr(create_obj_dic[("Con","C","Setting")],ln="advance",at="float",max=1,min=0)
    cmds.setAttr(f"{create_obj_dic[('Con','C','Setting')]}.advance",0,k=True)

    create_obj_dic |= autorig_utility.create_controller("Root1",root_obj,pos_CLR="C",con_shape="scuare",con_color=[0.8,0.2,0.2],con_scl=(40,40,40),uniform_scale=True,
                                                        con_advance_scl=(True,True,True),setting=create_obj_dic[("Con","C","Setting")])
    create_obj_dic |= autorig_utility.create_controller("Root2",root_obj,pos_CLR="C",con_shape="scuare",con_color=[0.2,0.8,0.2],con_scl=(36,36,36),uniform_scale=True,
                                                        con_advance_scl=(True,True,True),setting=create_obj_dic[("Con","C","Setting")])
    create_obj_dic |= autorig_utility.create_controller("Root3",root_obj,pos_CLR="C",con_shape="scuare",con_color=[0.2,0.2,0.8],con_scl=(32,32,32),uniform_scale=True,
                                                        con_advance_scl=(True,True,True),setting=create_obj_dic[("Con","C","Setting")])
    
    #接続
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Root1')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','Root2')]}.offsetParentMatrix")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Root2')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','Root3')]}.offsetParentMatrix")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Root3')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','Setting')]}.offsetParentMatrix")

    return create_obj_dic

def create_body(character_name:str, parent:str, obj_dic:dict, joint_dic:dict ,orientation_dic:dict):
    """
    リグ作成

    Parameters
    ----------
        string character_name : 名前
        string parent : 親になるオブジェクト
        dictionary obj_dic : 作成済みのオブジェクト
        dictionary joint_dic : ダミーのHUmanoidジョイント
        dictionary orientation_dic : 回転オブジェ

    Returns
    -------
        作成したオブジェ入った辞書
    """
    create_obj_dic={}
    setting = obj_dic[('Con','C','Setting')]

    #親作成
    root_obj = cmds.group(em=True,n=f"Grp_C_Body",p=parent)
    create_obj_dic[('Grp','C','Body')]=root_obj

    #matrix取得
    hips_matrix = cmds.xform(orientation_dic["c_hips"],m=True,ws=True,q=True)
    spine_matrix = cmds.xform(orientation_dic["c_spine"],m=True,ws=True,q=True)
    chest_matrix = cmds.xform(orientation_dic["c_chest"],m=True,ws=True,q=True)

    #腰親作成
    create_obj_dic |= autorig_utility.create_controller("Waist",root_obj,pos_CLR="C",con_color=(0.8,0.8,0.2),con_shape="arrorFour",con_scl=(10,10,10),con_rot=(0,0,90),
                                                        uniform_scale=True,setting=setting,con_advance_scl=(True,True,True))
    cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','Waist')]}.offsetParentMatrix")
    cmds.xform(create_obj_dic[('Grp','C','Waist')],m=spine_matrix,ws=True)

    #尻コントローラー
    create_obj_dic |= autorig_utility.create_controller("Hips",root_obj,pos_CLR="C",con_color=(0.2,0.8,0.2),con_shape="cube",con_scl=(7,13,13),con_pos=(-4,0,0),
                                                        setting=setting,con_advance_scl=(True,True,True),con_advance_pos=(True,True,True))
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Waist')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','Hips')]}.offsetParentMatrix")

    #胴体FK
    #Spine
    create_obj_dic |= autorig_utility.create_controller("SpineFK",root_obj,pos_CLR="C",con_color=(0.2,0.8,0.8),con_shape="circle",con_scl=(9,9,9),con_rot=(0,0,90),
                                                        setting=setting,con_advance_scl=(True,True,True),con_advance_pos=(True,True,True))
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Waist')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','SpineFK')]}.offsetParentMatrix")
    cmds.xform(create_obj_dic[('Grp','C','SpineFK')],m=spine_matrix,ws=True)
    #ChestFK
    create_obj_dic |= autorig_utility.create_controller("ChestFK",root_obj,pos_CLR="C",con_color=(0.2,0.8,0.8),con_shape="circle",con_scl=(9,9,9),con_rot=(0,0,90),
                                                        setting=setting,con_advance_scl=(True,True,True),con_advance_pos=(True,True,True))
    cmds.xform(create_obj_dic[('Grp','C','ChestFK')],m=chest_matrix,ws=True)
    autorig_utility.switch_parent(posA=create_obj_dic[('Drv','C','SpineFK')],
                                  rotB=create_obj_dic[('Drv','C','SpineFK')],rotA=create_obj_dic[('Drv','C','Waist')],
                                  sclB=create_obj_dic[('Drv','C','SpineFK')],sclA=create_obj_dic[('Drv','C','Waist')],
                                  dvn_con=create_obj_dic[('Con','C','ChestFK')],dvn_grp=create_obj_dic[('Grp','C','ChestFK')],postScl=True)
    
    #IK
    create_obj_dic |= autorig_utility.create_controller("ChestIK",root_obj,pos_CLR="C",con_shape="cube",con_color=(0.2,0.8,0.2),con_scl=(13,13,13),con_pos=(8,0,0),
                                                            setting=setting,con_advance_scl=(True,True,True))
    autorig_utility.postScale_parent(dvn_con=create_obj_dic[('Con','C','ChestIK')],dvn_grp=create_obj_dic[('Grp','C','ChestIK')]
                                     ,drv_drv=create_obj_dic[('Drv','C','ChestFK')])
    cmds.xform(create_obj_dic[('Grp','C','ChestIK')],m=chest_matrix,ws=True)

    create_obj_dic |= autorig_utility.create_controller("SpineIK",root_obj,pos_CLR="C",con_shape="fatCross",con_color=(0.2,0.8,0.2),con_scl=(4,4,4),con_rot=(0,0,90),
                                                            setting=setting,con_advance_scl=(True,True,True),con_advance_pos=(True,True,True),con_advance_rot=(False,True,True))
    aimMatrix = cmds.createNode("aimMatrix")
    multMatrix1 = cmds.createNode("multMatrix")
    multMatrix2 = cmds.createNode("multMatrix")
    multMatrix3 = cmds.createNode("multMatrix")
    decomposeMatrix1 = cmds.createNode("decomposeMatrix")
    decomposeMatrix2 = cmds.createNode("decomposeMatrix")
    dotProduct1 = cmds.createNode("dotProduct")
    dotProduct2 = cmds.createNode("dotProduct")
    composeMatrix1 = cmds.createNode("composeMatrix")
    composeMatrix2 = cmds.createNode("composeMatrix")
    quatToEuler1 = cmds.createNode("quatToEuler")
    quatToEuler2 = cmds.createNode("quatToEuler")
    floatMath1 = cmds.createNode("floatMath")
    floatMath2 = cmds.createNode("floatMath")
    floatMath3 = cmds.createNode("floatMath")
    
    cmds.setAttr(F"{aimMatrix}.secondaryInputAxisZ",1)
    cmds.setAttr(F"{aimMatrix}.secondaryInputAxisY",0)
    cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix2}.matrixIn[0]")
    cmds.connectAttr(f"{aimMatrix}.outputMatrix",f"{multMatrix2}.matrixIn[1]")
    cmds.setAttr(f"{aimMatrix}.secondaryMode",1)
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','SpineFK')]}.worldMatrix[0]",f"{aimMatrix}.inputMatrix")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','ChestIK')]}.worldMatrix[0]",f"{aimMatrix}.primaryTargetMatrix")
    cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{aimMatrix}.secondaryTargetMatrix")
    cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix1}.matrixIn[0]")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','SpineFK')]}.worldMatrix[0]",f"{multMatrix1}.matrixIn[1]")
    cmds.setAttr(f"{composeMatrix1}.inputTranslateZ",1)
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','ChestIK')]}.matrix",f"{multMatrix3}.matrixIn[0]")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','ChestFK')]}.matrix",f"{multMatrix3}.matrixIn[1]")
    cmds.connectAttr(f"{multMatrix3}.matrixSum",f"{decomposeMatrix1}.inputMatrix")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Hips')]}.matrix",f"{decomposeMatrix2}.inputMatrix")
    cmds.setAttr(f"{dotProduct1}.input2X",1)
    cmds.setAttr(f"{dotProduct2}.input2X",1)
    cmds.connectAttr(f"{decomposeMatrix1}.outputQuatX",f"{dotProduct1}.input1X")
    cmds.connectAttr(f"{decomposeMatrix1}.outputQuatY",f"{dotProduct1}.input1Y")
    cmds.connectAttr(f"{decomposeMatrix1}.outputQuatZ",f"{dotProduct1}.input1Z")
    cmds.connectAttr(f"{decomposeMatrix2}.outputQuatX",f"{dotProduct2}.input1X")
    cmds.connectAttr(f"{decomposeMatrix2}.outputQuatY",f"{dotProduct2}.input1Y")
    cmds.connectAttr(f"{decomposeMatrix2}.outputQuatZ",f"{dotProduct2}.input1Z")
    cmds.connectAttr(f"{dotProduct1}.output",f"{quatToEuler1}.inputQuatX")
    cmds.connectAttr(f"{dotProduct2}.output",f"{quatToEuler2}.inputQuatX")
    cmds.connectAttr(f"{decomposeMatrix1}.outputQuatW",f"{quatToEuler1}.inputQuatW")
    cmds.connectAttr(f"{decomposeMatrix2}.outputQuatW",f"{quatToEuler2}.inputQuatW")
    cmds.connectAttr(F"{quatToEuler1}.outputRotateX",f"{floatMath1}.floatA")
    cmds.connectAttr(F"{quatToEuler2}.outputRotateX",f"{floatMath2}.floatA")
    cmds.setAttr(F"{floatMath1}.operation",2)
    cmds.setAttr(F"{floatMath2}.operation",2)
    cmds.setAttr(F"{floatMath3}.operation",0)
    cmds.connectAttr(F"{floatMath1}.outFloat",f"{floatMath3}.floatA")
    cmds.connectAttr(F"{floatMath2}.outFloat",f"{floatMath3}.floatB")
    cmds.connectAttr(f"{floatMath3}.outFloat",f"{composeMatrix2}.inputRotateX")
    cmds.addAttr(create_obj_dic[('Con','C','SpineIK')],ln="followChest",at="float",max=1,min=0,k=True)
    cmds.addAttr(create_obj_dic[('Con','C','SpineIK')],ln="followHips",at="float",max=1,min=0,k=True)
    cmds.connectAttr(F"{create_obj_dic[('Con','C','SpineIK')]}.followChest",f"{floatMath1}.floatB")
    cmds.connectAttr(F"{create_obj_dic[('Con','C','SpineIK')]}.followHips",f"{floatMath2}.floatB")

    decomposeMatrix1 = cmds.createNode("decomposeMatrix")
    decomposeMatrix2 = cmds.createNode("decomposeMatrix")
    composeMatrix1 = cmds.createNode("composeMatrix")
    composeMatrix2 = cmds.createNode("composeMatrix")
    multMatrix1 = cmds.createNode("multMatrix")
    distanceBetween1 = cmds.createNode("distanceBetween")
    distanceBetween2 = cmds.createNode("distanceBetween")
    floatComposite = cmds.createNode("floatComposite")
    floatMath1 = cmds.createNode("floatMath")
    floatMath2 = cmds.createNode("floatMath")
    floatMath3 = cmds.createNode("floatMath")
    cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{decomposeMatrix1}.inputMatrix")
    cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{composeMatrix1}.inputTranslate")
    cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{composeMatrix1}.inputQuat")
    cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
    cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{create_obj_dic[('Grp','C','SpineIK')]}.offsetParentMatrix")
    cmds.connectAttr(F"{create_obj_dic[('Con','C','SpineIK')]}.inverseMatrix",f"{multMatrix1}.matrixIn[0]")
    cmds.connectAttr(F"{composeMatrix2}.outputMatrix",f"{multMatrix1}.matrixIn[1]")
    cmds.connectAttr(F"{create_obj_dic[('Con','C','SpineIK')]}.matrix",f"{multMatrix1}.matrixIn[2]")
    cmds.connectAttr(F"{composeMatrix1}.outputMatrix",f"{multMatrix1}.matrixIn[3]")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','SpineFK')]}.worldMatrix[0]",f"{decomposeMatrix2}.inputMatrix")
    cmds.connectAttr(f"{decomposeMatrix2}.outputScaleY",f"{composeMatrix2}.inputScaleY")
    cmds.connectAttr(f"{decomposeMatrix2}.outputScaleZ",f"{composeMatrix2}.inputScaleZ")
    cmds.setAttr(F"{floatMath1}.operation",2)
    cmds.connectAttr(f"{floatMath1}.outFloat",f"{composeMatrix2}.inputScaleX")
    cmds.connectAttr(F"{decomposeMatrix2}.outputScaleX",f"{floatMath1}.floatA")
    cmds.connectAttr(F"{floatComposite}.outFloat",f"{floatMath1}.floatB")
    cmds.setAttr(f"{floatComposite}.operation",2)
    cmds.setAttr(f"{floatComposite}.floatA",1)
    cmds.setAttr(F"{floatMath2}.operation",3)
    cmds.connectAttr(f"{floatMath2}.outFloat",f"{floatComposite}.floatB")
    cmds.connectAttr(F"{distanceBetween2}.distance",f"{floatMath2}.floatA")
    cmds.connectAttr(F"{distanceBetween1}.distance",f"{floatMath2}.floatB")
    cmds.connectAttr(F"{create_obj_dic[('Drv','C','SpineFK')]}.worldMatrix[0]",f"{distanceBetween1}.inMatrix1")
    cmds.connectAttr(F"{create_obj_dic[('Drv','C','SpineFK')]}.worldMatrix[0]",f"{distanceBetween2}.inMatrix1")
    cmds.connectAttr(F"{create_obj_dic[('Drv','C','ChestFK')]}.worldMatrix[0]",f"{distanceBetween1}.inMatrix2")
    cmds.connectAttr(F"{create_obj_dic[('Drv','C','ChestIK')]}.worldMatrix[0]",f"{distanceBetween2}.inMatrix2")
    cmds.setAttr(F"{floatMath3}.operation",2)
    cmds.connectAttr(f"{floatMath3}.outFloat",f"{floatComposite}.factor")
    cmds.connectAttr(f"{obj_dic[('Con','C','Setting')]}.advance",f"{floatMath3}.floatA")
    cmds.addAttr(create_obj_dic[('Con','C','SpineIK')],ln="stretch",at="float",max=1,min=0,k=True)
    cmds.connectAttr(f"{create_obj_dic[('Con','C','SpineIK')]}.stretch",f"{floatMath3}.floatB")

    min = cmds.createNode("min")
    colorComposite1 = cmds.createNode("colorComposite")
    colorMath1 = cmds.createNode("colorMath")
    distanceBetween1 = cmds.createNode("distanceBetween")
    distanceBetween2 = cmds.createNode("distanceBetween")
    multMatrix1 = cmds.createNode("multMatrix")
    multMatrix2 = cmds.createNode("multMatrix")
    decomposeMatrix1 = cmds.createNode("decomposeMatrix")
    decomposeMatrix2 = cmds.createNode("decomposeMatrix")
    composeMatrix1 = cmds.createNode("composeMatrix")
    floatMath1 = cmds.createNode("floatMath")
    #ChestIKはcon_advance_pos未指定(=(False,False,False)一律)のため、Con.translate→Drv.translateが
    #複合アトリビュートのまま1本で繋がっている(autorig_utility._connect_advance_vector参照)。
    #ここでDrv.tを別系統(colorComposite1経由)へ繋ぎ変えるので、複合単位でdisconnectする。
    cmds.disconnectAttr(f"{create_obj_dic[('Con','C','ChestIK')]}.translate",f"{create_obj_dic[('Drv','C','ChestIK')]}.translate")
    cmds.addAttr(create_obj_dic[('Con','C','ChestIK')],ln="stretch",at="float",max=1,min=0,k=True)
    cmds.setAttr(f"{floatMath1}.operation",3)
    cmds.setAttr(f"{colorMath1}.operation",3)
    cmds.setAttr(f"{colorComposite1}.operation",2)
    cmds.connectAttr(F"{colorComposite1}.outColor",f"{create_obj_dic[('Drv','C','ChestIK')]}.t")
    cmds.connectAttr(f"{min}.output",F"{colorComposite1}.factor")
    cmds.connectAttr(f"{obj_dic[('Con','C','Setting')]}.advance",f"{min}.input[0]")
    cmds.connectAttr(f"{create_obj_dic[('Con','C','ChestIK')]}.stretch",f"{min}.input[1]")
    cmds.connectAttr(f"{create_obj_dic[('Con','C','ChestIK')]}.t",F"{colorComposite1}.colorB")
    cmds.connectAttr(f"{decomposeMatrix2}.outputTranslate",F"{colorComposite1}.colorA")
    cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{decomposeMatrix2}.inputMatrix")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','SpineFK')]}.worldMatrix[0]",f"{distanceBetween1}.inMatrix1")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','SpineFK')]}.worldMatrix[0]",f"{distanceBetween2}.inMatrix1")
    cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix2}.matrixIn[0]")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','SpineFK')]}.worldMatrix[0]",f"{multMatrix2}.matrixIn[1]")
    cmds.connectAttr(f"{create_obj_dic[('Grp','C','ChestIK')]}.worldInverseMatrix[0]",f"{multMatrix2}.matrixIn[2]")
    cmds.connectAttr(f"{create_obj_dic[('Con','C','ChestIK')]}.worldMatrix[0]",f"{multMatrix1}.matrixIn[0]")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','SpineFK')]}.worldInverseMatrix[0]",f"{multMatrix1}.matrixIn[1]")
    cmds.connectAttr(f"{create_obj_dic[('Con','C','ChestIK')]}.worldMatrix[0]",f"{distanceBetween1}.inMatrix2")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','ChestFK')]}.worldMatrix[0]",f"{distanceBetween2}.inMatrix2")
    cmds.connectAttr(F"{distanceBetween1}.distance",f"{floatMath1}.floatA")
    cmds.connectAttr(F"{distanceBetween2}.distance",f"{floatMath1}.floatB")
    cmds.connectAttr(F"{floatMath1}.outFloat",f"{colorMath1}.colorBR")
    cmds.connectAttr(F"{floatMath1}.outFloat",f"{colorMath1}.colorBG")
    cmds.connectAttr(F"{floatMath1}.outFloat",f"{colorMath1}.colorBB")
    cmds.connectAttr(F"{multMatrix1}.matrixSum",f"{decomposeMatrix1}.inputMatrix")
    cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",F"{colorMath1}.colorA")
    cmds.connectAttr(f"{colorMath1}.outColor",f"{composeMatrix1}.inputTranslate")

    #接続
    autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','Hips')]}",joint_dic["c_hips"])
    autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','ChestIK')]}",joint_dic["c_chest"])
    autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','SpineIK')]}",joint_dic["c_spine"])

    # UpperChest作成
    if(f'c_upperChest' in joint_dic):
        upperChest_matrix = cmds.xform(orientation_dic["c_upperChest"],m=True,ws=True,q=True)
        create_obj_dic |= autorig_utility.create_controller("UpperChest",root_obj,pos_CLR="C",con_color=(0.2,0.8,0.8),con_shape="circle",con_scl=(9,9,9),con_rot=(0,0,90),
                                                            setting=setting,con_advance_scl=(True,True,True),con_advance_pos=(True,True,True))
        cmds.xform(create_obj_dic[('Grp','C','UpperChest')],m=upperChest_matrix,ws=True)
        autorig_utility.switch_parent(posA=create_obj_dic[('Drv','C','ChestIK')],
                                  rotB=create_obj_dic[('Drv','C','ChestIK')],rotA=create_obj_dic[('Drv','C','Waist')],
                                  sclB=create_obj_dic[('Drv','C','ChestIK')],sclA=create_obj_dic[('Drv','C','Waist')],
                                  dvn_con=create_obj_dic[('Con','C','UpperChest')],dvn_grp=create_obj_dic[('Grp','C','UpperChest')],postScl=True)
        autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','UpperChest')]}",joint_dic["c_upperChest"])

    return create_obj_dic

def create_head(character_name:str, parent:str, obj_dic:dict, joint_dic:dict ,orientation_dic:dict):
    """
    リグ作成

    Parameters
    ----------
        string character_name : 名前
        string parent : 親になるオブジェクト
        dictionary obj_dic : 作成済みのオブジェクト
        dictionary joint_dic : ダミーのHUmanoidジョイント
        dictionary orientation_dic : 回転オブジェ

    Returns
    -------
        作成したオブジェ入った辞書
    """
    create_obj_dic={}
    setting = obj_dic[('Con','C','Setting')]

    #親作成
    root_obj = cmds.group(em=True,n=f"Grp_C_Heads",p=parent)
    create_obj_dic[('Grp','C','Heads')]=root_obj

    #matrix取得
    neck_matrix = cmds.xform(orientation_dic["c_neck"],m=True,ws=True,q=True)
    head_matrix = cmds.xform(orientation_dic["c_head"],m=True,ws=True,q=True)
    chest_matrix = cmds.xform(orientation_dic["c_chest"],m=True,ws=True,q=True)
    eye_l_matrix = cmds.xform(orientation_dic["l_eye"],m=True,ws=True,q=True)
    eye_r_matrix = cmds.xform(orientation_dic["r_eye"],m=True,ws=True,q=True)

    #Neck
    create_obj_dic |= autorig_utility.create_controller("Neck",root_obj,pos_CLR="C",con_color=(0.2,0.8,0.8),con_shape="circle",con_scl=(3,3,3),con_rot=(0,0,90),
                                                        setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True))
    cmds.xform(create_obj_dic[('Grp','C','Neck')],m=neck_matrix,ws=True)
    
    if(f'c_upperChest' not in joint_dic):
        autorig_utility.switch_parent(posA=obj_dic[('Drv','C','ChestIK')],sclA=obj_dic[('Drv','C','ChestIK')],
                                    rotA=obj_dic[('Drv','C','Root3')],rotB=obj_dic[('Drv','C','ChestIK')],
                                    dvn_con=create_obj_dic[('Con','C','Neck')],dvn_grp=create_obj_dic[('Grp','C','Neck')])
    else:
        autorig_utility.switch_parent(posA=obj_dic[('Drv','C','UpperChest')],sclA=obj_dic[('Drv','C','UpperChest')],
                                    rotA=obj_dic[('Drv','C','Root3')],rotB=obj_dic[('Drv','C','UpperChest')],
                                    dvn_con=create_obj_dic[('Con','C','Neck')],dvn_grp=create_obj_dic[('Grp','C','Neck')])

    cmds.setAttr(f"{create_obj_dic[('Con','C','Neck')]}.rotParent",1)


    #Head
    create_obj_dic |= autorig_utility.create_controller("Head",root_obj,pos_CLR="C",con_color=(0.2,0.8,0.8),con_shape="circle",con_scl=(8,8,8),con_pos=(15,0,0),con_rot=(0,0,90),
                                                        setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),uniform_scale=True)
    
    outputComposeMatrix = cmds.createNode("composeMatrix")
    cmds.setAttr(f"{outputComposeMatrix}.useEulerRotation",0)
    cmds.connectAttr(f"{outputComposeMatrix}.outputMatrix",f"{create_obj_dic[('Grp','C','Head')]}.offsetParentMatrix",f=True)

    cmds.addAttr(create_obj_dic[('Con','C','Head')],ln="neckMatrix",at="matrix")
    matrix = OpenMaya.MMatrix(head_matrix)*OpenMaya.MMatrix(neck_matrix).inverse()
    matrix = list(matrix)
    cmds.setAttr(f"{create_obj_dic[('Con','C','Head')]}.neckMatrix",matrix,typ="matrix",l=True)
    multMatrix = cmds.createNode("multMatrix")
    neckDecomposeMatrix = cmds.createNode("decomposeMatrix")
    cmds.connectAttr(f"{create_obj_dic[('Con','C','Head')]}.neckMatrix",f"{multMatrix}.matrixIn[0]")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Neck')]}.worldMatrix[0]",f"{multMatrix}.matrixIn[1]")
    cmds.connectAttr(f"{multMatrix}.matrixSum",f"{neckDecomposeMatrix}.inputMatrix")
    cmds.connectAttr(f"{neckDecomposeMatrix}.outputTranslate",f"{outputComposeMatrix}.inputTranslate")

    cmds.addAttr(create_obj_dic[('Con','C','Head')],ln="chestMatrix",at="matrix")
    matrix = OpenMaya.MMatrix(head_matrix)*OpenMaya.MMatrix(chest_matrix).inverse()
    matrix = list(matrix)
    cmds.setAttr(f"{create_obj_dic[('Con','C','Head')]}.chestMatrix",matrix,typ="matrix",l=True)
    multMatrix = cmds.createNode("multMatrix")
    chestDecomposeMatrix = cmds.createNode("decomposeMatrix")
    cmds.connectAttr(f"{create_obj_dic[('Con','C','Head')]}.chestMatrix",f"{multMatrix}.matrixIn[0]")
    cmds.connectAttr(f"{obj_dic[('Drv','C','ChestIK')]}.worldMatrix[0]",f"{multMatrix}.matrixIn[1]")
    cmds.connectAttr(f"{multMatrix}.matrixSum",f"{chestDecomposeMatrix}.inputMatrix")

    cmds.addAttr(create_obj_dic[('Con','C','Head')],ln="rootMatrix",at="matrix")
    matrix = head_matrix
    cmds.setAttr(f"{create_obj_dic[('Con','C','Head')]}.rootMatrix",matrix,typ="matrix",l=True)
    multMatrix = cmds.createNode("multMatrix")
    rootDecomposeMatrix = cmds.createNode("decomposeMatrix")
    cmds.connectAttr(f"{create_obj_dic[('Con','C','Head')]}.rootMatrix",f"{multMatrix}.matrixIn[0]")
    cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix[0]",f"{multMatrix}.matrixIn[1]")
    cmds.connectAttr(f"{multMatrix}.matrixSum",f"{rootDecomposeMatrix}.inputMatrix")
    cmds.connectAttr(f"{rootDecomposeMatrix}.outputScale",f"{outputComposeMatrix}.inputScale")

    cmds.addAttr(F"{create_obj_dic[('Con','C','Head')]}",ln="rotParent",at="enum",en="root:chest:neck:",k=True)
    cmds.setAttr(f"{create_obj_dic[('Con','C','Head')]}.rotParent",1)

    rootCondition = cmds.createNode("condition")
    cmds.connectAttr(f"{create_obj_dic[('Con','C','Head')]}.rotParent",f"{rootCondition}.firstTerm")
    cmds.setAttr(f"{rootCondition}.secondTerm",0)
    cmds.setAttr(f"{rootCondition}.colorIfTrueR",1)
    cmds.setAttr(f"{rootCondition}.colorIfFalseR",0)

    chestCondition = cmds.createNode("condition")
    cmds.connectAttr(f"{create_obj_dic[('Con','C','Head')]}.rotParent",f"{chestCondition}.firstTerm")
    cmds.setAttr(f"{chestCondition}.secondTerm",1)
    cmds.setAttr(f"{chestCondition}.colorIfTrueR",1)
    cmds.setAttr(f"{chestCondition}.colorIfFalseR",0)

    neckCondition = cmds.createNode("condition")
    cmds.connectAttr(f"{create_obj_dic[('Con','C','Head')]}.rotParent",f"{neckCondition}.firstTerm")
    cmds.setAttr(f"{neckCondition}.secondTerm",2)
    cmds.setAttr(f"{neckCondition}.colorIfTrueR",1)
    cmds.setAttr(f"{neckCondition}.colorIfFalseR",0)

    for i in {"X","Y","Z","W"}:
        rootFloatMath = cmds.createNode("floatMath")
        chestFloatMath = cmds.createNode("floatMath")
        neckFloatMath = cmds.createNode("floatMath")
        cmds.setAttr(F"{rootFloatMath}.operation",2)
        cmds.setAttr(F"{chestFloatMath}.operation",2)
        cmds.setAttr(F"{neckFloatMath}.operation",2)
        cmds.connectAttr(f"{rootDecomposeMatrix}.outputQuat{i}",f"{rootFloatMath}.floatA")
        cmds.connectAttr(f"{chestDecomposeMatrix}.outputQuat{i}",f"{chestFloatMath}.floatA")
        cmds.connectAttr(f"{neckDecomposeMatrix}.outputQuat{i}",f"{neckFloatMath}.floatA")
        cmds.connectAttr(f"{rootCondition}.outColorR",f"{rootFloatMath}.floatB")
        cmds.connectAttr(f"{chestCondition}.outColorR",f"{chestFloatMath}.floatB")
        cmds.connectAttr(f"{neckCondition}.outColorR",f"{neckFloatMath}.floatB")
        addFloatMath1 = cmds.createNode("floatMath")
        addFloatMath2 = cmds.createNode("floatMath")
        cmds.setAttr(F"{addFloatMath1}.operation",0)
        cmds.setAttr(F"{addFloatMath2}.operation",0)
        cmds.connectAttr(f"{rootFloatMath}.outFloat",f"{addFloatMath1}.floatA")
        cmds.connectAttr(f"{chestFloatMath}.outFloat",f"{addFloatMath1}.floatB")
        cmds.connectAttr(f"{neckFloatMath}.outFloat",f"{addFloatMath2}.floatA")
        cmds.connectAttr(f"{addFloatMath1}.outFloat",f"{addFloatMath2}.floatB")
        cmds.connectAttr(f"{addFloatMath2}.outFloat",f"{outputComposeMatrix}.inputQuat{i}")

    #接続
    autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','Neck')]}",joint_dic["c_neck"])
    autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','Head')]}",joint_dic["c_head"])

    #目
    eye_c_pos = [(v*0.5) + (cmds.xform(orientation_dic["r_eye"],t=True,ws=True,q=True)[n] * 0.5) for n,v in enumerate(cmds.xform(orientation_dic["l_eye"],t=True,ws=True,q=True))]
    eye_c_pos[2]+=eye_c_pos[1]/2
    create_obj_dic |= autorig_utility.create_controller("EyeAim",root_obj,pos_CLR="C",con_color=(0.6,0.6,0),con_shape="scuare",con_scl=(3,3,6),con_pos=(0,0,0),con_rot=(90,0,90),
                                                        setting=setting,uniform_scale=True)
    cmds.xform(create_obj_dic[('Grp','C','EyeAim')],t=eye_c_pos,ws=True)
    autorig_utility.switch_parent(dvn_grp=create_obj_dic[('Grp','C','EyeAim')],dvn_con=create_obj_dic[('Con','C','EyeAim')],
                                  posA=obj_dic[('Drv','C','Root3')],posB=create_obj_dic[('Drv','C','Head')],
                                  rotA=obj_dic[('Drv','C','Root3')],rotB=create_obj_dic[('Drv','C','Head')],
                                  sclA=obj_dic[('Drv','C','Root3')],sclB=create_obj_dic[('Drv','C','Head')])
    
    lr = {}
    lr["L"] = eye_l_matrix
    lr["R"] = eye_r_matrix
    move_matrix = [1,0,0,0,0,1,0,0,0,0,1,0,eye_c_pos[1]/2,0,0,1]
    composeMatrix1 = cmds.createNode("composeMatrix")
    cmds.setAttr(F"{composeMatrix1}.inputTranslateY",1)
    for i in lr:
        if(i == "L"):
            scl = 1
        else:
            scl = -1
        create_obj_dic |= autorig_utility.create_controller("EyeAim",root_obj,pos_CLR=i,con_color=(0.6,0.6,0),con_shape="circle",con_scl=(2,2,2),con_rot=(90,0,90),
                                                            setting=setting,con_scl_lock=(True,True,True),con_rot_lock=(True,True,True),drv_scale_offset=(1,-1,1))
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','EyeAim')]}.worldMatrix",f"{create_obj_dic[('Grp',i,'EyeAim')]}.offsetParentMatrix")
        matrix = OpenMaya.MMatrix(move_matrix)*OpenMaya.MMatrix(lr[i])
        cmds.xform(create_obj_dic[('Grp',i,'EyeAim')],m=list(matrix),ws=True)
        cmds.setAttr(f"{create_obj_dic[('Grp',i,'EyeAim')]}.r",*(0,0,0),typ="double3")
        cmds.setAttr(f"{create_obj_dic[('Grp',i,'EyeAim')]}.s",*(scl,1,1),typ="double3")

        aim_target = cmds.group(em=True, name=f"Grp_{i}_EyeAimTarget", parent=root_obj)
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','Head')]}.worldMatrix",f"{aim_target}.offsetParentMatrix")
        cmds.xform(aim_target,m=lr[i],ws=True)

        create_obj_dic |= autorig_utility.create_controller("Eye",root_obj,pos_CLR=i,con_color=(0.2,0.8,0.8),con_shape="circle",con_scl=(2,2,2),con_rot=(90,90,0),
                                                            setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),drv_scale_offset=(1,-1,1),uniform_scale=True)
        
        aimMatrix = cmds.createNode("aimMatrix")
        multMatrix1 = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{aim_target}.worldMatrix[0]",f"{aimMatrix}.inputMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Drv',i,'EyeAim')]}.worldMatrix[0]",f"{aimMatrix}.primaryTargetMatrix")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(f"{aim_target}.worldMatrix[0]",f"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{aimMatrix}.secondaryTargetMatrix")
        cmds.setAttr(f"{aimMatrix}.secondaryMode",1)
        cmds.connectAttr(f"{aimMatrix}.outputMatrix",f"{create_obj_dic[('Grp',i,'Eye')]}.offsetParentMatrix")

        cmds.setAttr(f"{create_obj_dic[('Grp',i,'Eye')]}.sy",scl)
        
        autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv',i,'Eye')]}",joint_dic[f"{i.lower()}_eye"])

    return create_obj_dic

def create_leg(character_name:str, parent:str, obj_dic:dict, joint_dic:dict ,orientation_dic:dict, pos_dic:dict):
    """
    リグ作成

    Parameters
    ----------
        string character_name : 名前
        string parent : 親になるオブジェクト
        dictionary obj_dic : 作成済みのオブジェクト
        dictionary joint_dic : ダミーのHUmanoidジョイント
        dictionary orientation_dic : 回転オブジェ
        dictionary pos_dic : 位置の基準

    Returns
    -------
        作成したオブジェ入った辞書
    """
    create_obj_dic={}
    setting = obj_dic[('Con','C','Setting')]

    #親作成
    root_center_obj = cmds.group(em=True,n=f"Grp_C_Leg",p=parent)
    create_obj_dic[('Grp','C','Leg')]=root_center_obj

    hips_joint_matrix = cmds.xform(joint_dic["c_hips"],m=True,ws=True,q=True)

    #左右繰り返し
    for clr in ("L","R"):
        if(clr == "L"):
            scl = 1
        else:
            scl = -1
        clr_lower = clr.lower()
        root_obj = cmds.group(em=True,n=f"Grp_{clr}_Leg",p=root_center_obj)
        create_obj_dic[('Grp',clr,'Leg')]=root_obj

        #matrix取得
        upperLeg_matrix = cmds.xform(orientation_dic[f"{clr_lower}_upperLeg"],m=True,ws=True,q=True)
        lowerLeg_matrix = cmds.xform(orientation_dic[f"{clr_lower}_lowerLeg"],m=True,ws=True,q=True)
        foot_matrix = cmds.xform(orientation_dic[f"{clr_lower}_foot"],m=True,ws=True,q=True)
        toes_matrix = cmds.xform(orientation_dic[f"{clr_lower}_toes"],m=True,ws=True,q=True)

        #LegRoot
        create_obj_dic |= autorig_utility.create_controller("LegRoot",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0.2),con_shape="fatCross",con_scl=(0.8,0.8,0.8),con_rot=(90,0,0),con_pos=(0,-4,0),
                                                            setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),uniform_scale=True,drv_scale_offset=(1,scl,1))
        cmds.xform(create_obj_dic[('Grp',clr,'LegRoot')],m=upperLeg_matrix,ws=True)
        autorig_utility.switch_parent(posA=obj_dic[('Drv','C','Hips')],sclA=obj_dic[('Drv','C','Root3')],
                                      rotB=obj_dic[('Drv','C','Hips')],rotA=obj_dic[('Drv','C','Root3')],
                                      dvn_con=create_obj_dic[('Con',clr,'LegRoot')],dvn_grp=create_obj_dic[('Grp',clr,'LegRoot')])
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'LegRoot')]}.sy",scl)

        cmds.addAttr(create_obj_dic[('Drv',clr,'LegRoot')],ln="WorldBindMatrix",at="matrix")
        matrix = cmds.xform(create_obj_dic[('Drv',clr,'LegRoot')],q=True,ws=True,m=True)
        cmds.setAttr(f"{create_obj_dic[('Drv',clr,'LegRoot')]}.WorldBindMatrix",*matrix,typ="matrix")

        #ダミージョイント複製
        upperLeg_fk = cmds.duplicate(joint_dic[f"{clr_lower}_upperLeg"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_upperLeg"],l=False)[0]+"_fk")[0]
        lowerLeg_fk = cmds.duplicate(joint_dic[f"{clr_lower}_lowerLeg"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_lowerLeg"],l=False)[0]+"_fk")[0]
        foot_fk = cmds.duplicate(joint_dic[f"{clr_lower}_foot"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_foot"],l=False)[0]+"_fk")[0]
        toes_fk = cmds.duplicate(joint_dic[f"{clr_lower}_toes"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_toes"],l=False)[0]+"_fk")[0]
        lowerLeg_fk = cmds.parent(lowerLeg_fk,upperLeg_fk)[0]
        foot_fk = cmds.parent(foot_fk,lowerLeg_fk)[0]
        toes_fk = cmds.parent(toes_fk,foot_fk)[0]
        upperLeg_ik = cmds.duplicate(joint_dic[f"{clr_lower}_upperLeg"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_upperLeg"],l=False)[0]+"_ik")[0]
        lowerLeg_ik = cmds.duplicate(joint_dic[f"{clr_lower}_lowerLeg"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_lowerLeg"],l=False)[0]+"_ik")[0]
        foot_ik = cmds.duplicate(joint_dic[f"{clr_lower}_foot"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_foot"],l=False)[0]+"_ik")[0]
        toes_ik = cmds.duplicate(joint_dic[f"{clr_lower}_toes"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_toes"],l=False)[0]+"_ik")[0]
        lowerLeg_ik = cmds.parent(lowerLeg_ik,upperLeg_ik)[0]
        foot_ik = cmds.parent(foot_ik,lowerLeg_ik)[0]
        toes_ik = cmds.parent(toes_ik,foot_ik)[0]

        create_obj_dic[('Joint',clr,'UpperLegFK')]=upperLeg_fk
        create_obj_dic[('Joint',clr,'UpperLegIK')]=upperLeg_ik
        create_obj_dic[('Joint',clr,'LowerLegFK')]=lowerLeg_fk
        create_obj_dic[('Joint',clr,'LowerLegIK')]=lowerLeg_ik
        create_obj_dic[('Joint',clr,'FootIK')]=foot_ik
        create_obj_dic[('Joint',clr,'FootFK')]=foot_fk
        create_obj_dic[('Joint',clr,'ToesIK')]=toes_ik
        create_obj_dic[('Joint',clr,'ToesFK')]=toes_fk

        for i in (upperLeg_fk,lowerLeg_fk,foot_fk,toes_fk,upperLeg_ik,lowerLeg_ik,foot_ik,toes_ik):
            jointOrient = cmds.getAttr(f"{i}.jointOrient")[0]
            cmds.setAttr(f"{i}.preferredAngleX",jointOrient[0])
            cmds.setAttr(f"{i}.preferredAngleY",jointOrient[1])
            cmds.setAttr(f"{i}.preferredAngleZ",jointOrient[2])
            cmds.setAttr(f"{i}.jointOrient",*(0,0,0),typ="double3")
            rot = cmds.getAttr(f"{i}.r")[0]#追加
            cmds.setAttr(f"{i}.r",*jointOrient,typ="double3")
            cmds.xform(i,eu=True,ro=rot,r=True)#追加

        #IKFK選択
        cmds.addAttr(create_obj_dic[('Con',clr,'LegRoot')],ln="IKFK",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK",0,k=True)
        for i in [(upperLeg_fk,upperLeg_ik,joint_dic[f"{clr_lower}_upperLeg"]),(lowerLeg_fk,lowerLeg_ik,joint_dic[f"{clr_lower}_lowerLeg"]),
                (foot_fk,foot_ik,joint_dic[f"{clr_lower}_foot"]),(toes_fk,toes_ik,joint_dic[f"{clr_lower}_toes"])]:
            decomposeMatrix1 = cmds.createNode("decomposeMatrix")
            decomposeMatrix2 = cmds.createNode("decomposeMatrix")
            quatSlerp = cmds.createNode("quatSlerp")
            quatToEuler = cmds.createNode("quatToEuler")
            pairBlend = cmds.createNode("pairBlend")
            blendColors = cmds.createNode("blendColors")
            cmds.connectAttr(f"{i[0]}.jointOrient",f"{i[2]}.jointOrient")
            cmds.connectAttr(f"{i[1]}.matrix", f"{decomposeMatrix2}.inputMatrix")
            cmds.connectAttr(f"{i[0]}.matrix", f"{decomposeMatrix1}.inputMatrix")
            cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{quatSlerp}.input2Quat")
            cmds.connectAttr(f"{decomposeMatrix2}.outputQuat",f"{quatSlerp}.input1Quat")
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK", f"{quatSlerp}.inputT")
            cmds.connectAttr(f"{decomposeMatrix2}.outputTranslate",f"{pairBlend}.inTranslate1")
            cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{pairBlend}.inTranslate2")
            cmds.connectAttr(f"{decomposeMatrix2}.outputScale",f"{pairBlend}.inRotate1")
            cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{pairBlend}.inRotate2")
            cmds.connectAttr(f"{decomposeMatrix2}.outputShear",f"{blendColors}.color2")
            cmds.connectAttr(f"{decomposeMatrix1}.outputShear",f"{blendColors}.color1")
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK", f"{pairBlend}.weight")
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK", f"{blendColors}.blender")
            cmds.connectAttr(f"{quatSlerp}.outputQuat",f"{quatToEuler}.inputQuat")
            cmds.connectAttr(f"{i[2]}.rotateOrder",f"{quatToEuler}.inputRotateOrder")
            cmds.connectAttr(f"{quatToEuler}.outputRotate",f"{i[2]}.rotate")
            cmds.connectAttr(f"{pairBlend}.outTranslate",f"{i[2]}.translate")
            cmds.connectAttr(f"{pairBlend}.outRotate",f"{i[2]}.scale")
            cmds.connectAttr(f"{blendColors}.output",f"{i[2]}.shear")

        #FK作成
        #UpperLeg
        create_obj_dic |= autorig_utility.create_controller("UpperLegFK",root_obj,pos_CLR=clr,con_color=(0.2,0.8,0.8),con_shape="circle",con_scl=(3,3,3),con_rot=(90,90,0),con_pos=(9,0,0),
                                                                setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),drv_scale_offset=(1,scl,1))
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'LegRoot')]}.worldMatrix[0]",f"{create_obj_dic[('Grp',clr,'UpperLegFK')]}.offsetParentMatrix")
        cmds.xform(create_obj_dic[('Grp',clr,'UpperLegFK')],m=upperLeg_matrix,ws=True)
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'UpperLegFK')]}.sy",scl)
        #lowerleg
        create_obj_dic |= autorig_utility.create_controller("LowerLegFK",root_obj,pos_CLR=clr,con_color=(0.2,0.8,0.8),con_shape="circle",con_scl=(3,3,3),con_rot=(90,90,0),con_pos=(9,0,0),
                                                                setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),drv_scale_offset=(1,scl,1))
        cmds.xform(create_obj_dic[('Grp',clr,'LowerLegFK')],m=lowerLeg_matrix,ws=True)
        autorig_utility.switch_parent(posA=create_obj_dic[('Drv',clr,'UpperLegFK')],
                                      sclA=create_obj_dic[('Drv',clr,'LegRoot')],sclB=create_obj_dic[('Drv',clr,'UpperLegFK')],
                                      rotA=create_obj_dic[('Drv',clr,'LegRoot')],rotB=create_obj_dic[('Drv',clr,'UpperLegFK')],
                                      dvn_con=create_obj_dic[('Con',clr,'LowerLegFK')],dvn_grp=create_obj_dic[('Grp',clr,'LowerLegFK')],postScl=True)
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'LowerLegFK')]}.sy",scl)
        #foot
        create_obj_dic |= autorig_utility.create_controller("FootFK",root_obj,pos_CLR=clr,con_color=(0.2,0.8,0.8),con_shape="circle",con_scl=(3,3,3),con_rot=(90,90,0),con_pos=(9,0,0),
                                                                setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),drv_scale_offset=(1,scl,1))
        cmds.xform(create_obj_dic[('Grp',clr,'FootFK')],m=foot_matrix,ws=True)
        autorig_utility.switch_parent(posA=create_obj_dic[('Drv',clr,'LowerLegFK')],
                                      sclA=create_obj_dic[('Drv',clr,'LegRoot')],sclB=create_obj_dic[('Drv',clr,'LowerLegFK')],
                                      rotA=create_obj_dic[('Drv',clr,'LegRoot')],rotB=create_obj_dic[('Drv',clr,'LowerLegFK')],
                                      dvn_con=create_obj_dic[('Con',clr,'FootFK')],dvn_grp=create_obj_dic[('Grp',clr,'FootFK')],postScl=True)
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'FootFK')]}.sy",scl)
        #toes
        create_obj_dic |= autorig_utility.create_controller("ToesFK",root_obj,pos_CLR=clr,con_color=(0.2,0.8,0.8),con_shape="circle",con_scl=(3,3,3),con_rot=(90,90,0),con_pos=(9,0,0),
                                                                setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),drv_scale_offset=(1,scl,1))
        cmds.xform(create_obj_dic[('Grp',clr,'ToesFK')],m=toes_matrix,ws=True)
        autorig_utility.switch_parent(posA=create_obj_dic[('Drv',clr,'FootFK')],
                                      sclA=create_obj_dic[('Drv',clr,'LegRoot')],sclB=create_obj_dic[('Drv',clr,'FootFK')],
                                      rotA=create_obj_dic[('Drv',clr,'LegRoot')],rotB=create_obj_dic[('Drv',clr,'FootFK')],
                                      dvn_con=create_obj_dic[('Con',clr,'ToesFK')],dvn_grp=create_obj_dic[('Grp',clr,'ToesFK')],postScl=True)
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'ToesFK')]}.sy",scl)

        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LowerLegFK')]}.rotParent",1)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FootFK')]}.rotParent",1)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'ToesFK')]}.rotParent",1)
        autorig_utility.matrix_constraint(create_obj_dic[('Drv',clr,"UpperLegFK")],upperLeg_fk)
        autorig_utility.matrix_constraint(create_obj_dic[('Drv',clr,"LowerLegFK")],lowerLeg_fk)
        autorig_utility.matrix_constraint(create_obj_dic[('Drv',clr,"FootFK")],foot_fk)
        autorig_utility.matrix_constraint(create_obj_dic[('Drv',clr,"ToesFK")],toes_fk)

        #IK作成
        #IKdummy
        matrix = cmds.xform(upperLeg_fk,q=True,ws=True,m=True)
        ik_parent = cmds.group(em=True,n=f"Grp_{clr}_LegIKJoint",p=root_obj)
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegRoot')]}.worldMatrix",f"{ik_parent}.offsetParentMatrix")
        cmds.xform(ik_parent,m=matrix,ws=True)

        upperLeg_ik_dummy = cmds.duplicate(upperLeg_ik,f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_upperLeg"],l=False)[0]+"_ik_dummy")[0]
        lowerLeg_ik_dummy = cmds.duplicate(lowerLeg_ik,f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_lowerLeg"],l=False)[0]+"_ik_dummy")[0]
        foot_ik_dummy = cmds.duplicate(foot_ik,f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_foot"],l=False)[0]+"_ik_dummy")[0]
        upperLeg_ik_dummy = cmds.parent(upperLeg_ik_dummy,ik_parent)[0]
        lowerLeg_ik_dummy = cmds.parent(lowerLeg_ik_dummy,upperLeg_ik_dummy)[0]
        foot_ik_dummy = cmds.parent(foot_ik_dummy,lowerLeg_ik_dummy)[0]
        cmds.makeIdentity(upperLeg_ik_dummy,a=True,t=False,r=True,s=False,n=False,pn=True)
        cmds.makeIdentity(lowerLeg_ik_dummy,a=True,t=False,r=True,s=False,n=False,pn=True)

        autorig_utility.matrix_constraint(upperLeg_ik_dummy,upperLeg_ik)
        autorig_utility.matrix_constraint(lowerLeg_ik_dummy,lowerLeg_ik)
        autorig_utility.matrix_constraint(foot_ik_dummy,foot_ik)

        #メインコントローラー
        create_obj_dic |= autorig_utility.create_controller("LegIK",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0),con_shape="cube",con_scl=(5,5,5),con_rot=(90,90,0),
                                                            setting=setting,uniform_scale=True,connect_drv=False,con_advance_scl=(True,True,True))
        cmds.xform(create_obj_dic[('Grp',clr,'LegIK')],ws=True,t=[foot_matrix[12],foot_matrix[13],foot_matrix[14]])
        autorig_utility.switch_parent(posA=obj_dic[('Drv','C','Root3')],posB=create_obj_dic[('Drv',clr,'LegRoot')],
                                      rotA=obj_dic[('Drv','C','Root3')],rotB=create_obj_dic[('Drv',clr,'LegRoot')],
                                      sclA=create_obj_dic[('Drv',clr,'LegRoot')],
                                      dvn_con=create_obj_dic[('Con',clr,'LegIK')],dvn_grp=create_obj_dic[('Grp',clr,'LegIK')])
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'LegIK')]}.sx",scl)
        legIK_matrix=cmds.xform(create_obj_dic[('Grp',clr,'LegIK')],q=True,ws=True,m=True)

        #先端回転
        toestip_matrix = cmds.xform(pos_dic[f"{clr_lower}_toestip"],m=True,ws=True,q=True)
        heel_matrix = cmds.xform(pos_dic[f"{clr_lower}_heel"],m=True,ws=True,q=True)
        footinside_matrix = cmds.xform(pos_dic[f"{clr_lower}_footinside"],m=True,ws=True,q=True)
        footoutside_matrix = cmds.xform(pos_dic[f"{clr_lower}_footoutside"],m=True,ws=True,q=True)
        sole_matrix = cmds.xform(pos_dic[f"{clr_lower}_sole"],m=True,ws=True,q=True)
        #matrix
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="ToesMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(toestip_matrix)*OpenMaya.MMatrix(legIK_matrix).inverse()
        cmds.setAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.ToesMatrix",*matrix,typ="matrix",k=False,l=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="HeelMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(heel_matrix)*OpenMaya.MMatrix(legIK_matrix).inverse()
        cmds.setAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.HeelMatrix",*matrix,typ="matrix",k=False,l=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="FootInsideMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(footinside_matrix)*OpenMaya.MMatrix(legIK_matrix).inverse()
        cmds.setAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.FootInsideMatrix",*matrix,typ="matrix",k=False,l=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="FootOutsideMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(footoutside_matrix)*OpenMaya.MMatrix(legIK_matrix).inverse()
        cmds.setAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.FootOutsideMatrix",*matrix,typ="matrix",k=False,l=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="SoleMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(sole_matrix)*OpenMaya.MMatrix(legIK_matrix).inverse()
        cmds.setAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.SoleMatrix",*matrix,typ="matrix",k=False,l=True)
        #アトリビュート作成
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="ToesRoll",at="double",dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.ToesRoll",0,k=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="ToesRotate",at="double",dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.ToesRotate",0,k=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="HeelRoll",at="double",dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.HeelRoll",0,k=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="HeelRotate",at="double",dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.HeelRotate",0,k=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="SoleRotate",at="double",dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.SoleRotate",0,k=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="Tilt",at="double",dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.Tilt",0,k=True)
        #計算
        toesComposeMatrix = cmds.createNode("composeMatrix")
        heelComposeMatrix = cmds.createNode("composeMatrix")
        soleComposeMatrix = cmds.createNode("composeMatrix")
        insideComposeMatrix = cmds.createNode("composeMatrix")
        outsideComposeMatrix = cmds.createNode("composeMatrix")
        toesInverseMatrix = cmds.createNode("inverseMatrix")
        heelInverseMatrix = cmds.createNode("inverseMatrix")
        soleInverseMatrix = cmds.createNode("inverseMatrix")
        insideInverseMatrix = cmds.createNode("inverseMatrix")
        outsideInverseMatrix = cmds.createNode("inverseMatrix")
        outMultMatrix = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{outMultMatrix}.matrixSum",f"{create_obj_dic[('Drv',clr,'LegIK')]}.offsetParentMatrix")
        #con
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        composeMatrix1 = cmds.createNode("composeMatrix")
        floatComposite1 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite1}.operation",2)
        cmds.setAttr(f"{floatComposite1}.floatA",1)
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.matrix",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(F"{decomposeMatrix1}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(F"{decomposeMatrix1}.outputTranslate",f"{composeMatrix1}.inputTranslate")
        cmds.connectAttr(F"{composeMatrix1}.outputMatrix",f"{outMultMatrix}.matrixIn[0]")
        cmds.connectAttr(f"{decomposeMatrix1}.outputScaleX",f"{floatComposite1}.floatB")
        cmds.connectAttr(f"{setting}.advance",f"{floatComposite1}.factor")
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{composeMatrix1}.inputScaleX")
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{composeMatrix1}.inputScaleY")
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{composeMatrix1}.inputScaleZ")

        #inside
        insideCondition = cmds.createNode("condition")
        cmds.setAttr(f"{insideCondition}.secondTerm",0)
        cmds.setAttr(f"{insideCondition}.operation",2)
        cmds.setAttr(f"{insideCondition}.colorIfFalseR",0)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.Tilt",f"{insideCondition}.colorIfTrueR")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.Tilt",f"{insideCondition}.firstTerm")
        cmds.connectAttr(f"{insideCondition}.outColorR",f"{insideComposeMatrix}.inputRotateZ")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.FootInsideMatrix",f"{insideInverseMatrix}.inputMatrix")
        cmds.connectAttr(f"{insideInverseMatrix}.outputMatrix",f"{outMultMatrix}.matrixIn[1]")
        cmds.connectAttr(f"{insideComposeMatrix}.outputMatrix",f"{outMultMatrix}.matrixIn[2]")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.FootInsideMatrix",f"{outMultMatrix}.matrixIn[3]")
        #outside
        outsideCondition = cmds.createNode("condition")
        cmds.setAttr(f"{outsideCondition}.secondTerm",0)
        cmds.setAttr(f"{outsideCondition}.operation",4)
        cmds.setAttr(f"{outsideCondition}.colorIfFalseR",0)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.Tilt",f"{outsideCondition}.colorIfTrueR")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.Tilt",f"{outsideCondition}.firstTerm")
        cmds.connectAttr(f"{outsideCondition}.outColorR",f"{outsideComposeMatrix}.inputRotateZ")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.FootOutsideMatrix",f"{outsideInverseMatrix}.inputMatrix")
        cmds.connectAttr(f"{outsideInverseMatrix}.outputMatrix",f"{outMultMatrix}.matrixIn[4]")
        cmds.connectAttr(f"{outsideComposeMatrix}.outputMatrix",f"{outMultMatrix}.matrixIn[5]")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.FootOutsideMatrix",f"{outMultMatrix}.matrixIn[6]")
        #heel
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.HeelRoll",f"{heelComposeMatrix}.inputRotateX")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.HeelRotate",f"{heelComposeMatrix}.inputRotateY")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.HeelMatrix",f"{heelInverseMatrix}.inputMatrix")
        cmds.connectAttr(F"{heelInverseMatrix}.outputMatrix",f"{outMultMatrix}.matrixIn[7]")
        cmds.connectAttr(F"{heelComposeMatrix}.outputMatrix",f"{outMultMatrix}.matrixIn[8]")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.HeelMatrix",f"{outMultMatrix}.matrixIn[9]")
        #toe
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.ToesRoll",f"{toesComposeMatrix}.inputRotateX")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.ToesRotate",f"{toesComposeMatrix}.inputRotateY")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.ToesMatrix",f"{toesInverseMatrix}.inputMatrix")
        cmds.connectAttr(F"{toesInverseMatrix}.outputMatrix",f"{outMultMatrix}.matrixIn[10]")
        cmds.connectAttr(F"{toesComposeMatrix}.outputMatrix",f"{outMultMatrix}.matrixIn[11]")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.ToesMatrix",f"{outMultMatrix}.matrixIn[12]")
        #sole
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.SoleRotate",f"{soleComposeMatrix}.inputRotateY")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.SoleMatrix",f"{soleInverseMatrix}.inputMatrix")
        cmds.connectAttr(F"{soleInverseMatrix}.outputMatrix",f"{outMultMatrix}.matrixIn[13]")
        cmds.connectAttr(F"{soleComposeMatrix}.outputMatrix",f"{outMultMatrix}.matrixIn[14]")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.SoleMatrix",f"{outMultMatrix}.matrixIn[15]")

        cmds.xform(create_obj_dic[('Drv',clr,'LegIK')],ws=True,m=toes_matrix)

        #Foot
        create_obj_dic |= autorig_utility.create_controller("FootIK",root_obj,pos_CLR=clr,con_color=(0.2,0.8,0.2),con_shape="scuare",con_scl=(3,3,3),con_rot=(0,0,90),con_pos=(-5,0,0),
                                                        setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),drv_scale_offset=(1,scl,1))
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.worldMatrix",f"{create_obj_dic[('Grp',clr,'FootIK')]}.offsetParentMatrix")
        cmds.xform(create_obj_dic[('Drv',clr,'FootIK')],ws=True,m=foot_matrix)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'FootIK')]}.t",0,0,0)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'FootIK')]}.s",1,scl,1)
        #matrix
        cmds.addAttr(create_obj_dic[('Drv',clr,'FootIK')],ln="FootMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(foot_matrix)*OpenMaya.MMatrix(toes_matrix).inverse()
        cmds.setAttr(F"{create_obj_dic[('Drv',clr,'FootIK')]}.FootMatrix",*matrix,typ="matrix",k=False,l=True)
        
        #legLength
        cmds.addAttr(ik_parent,ln="LegLength",at="float")
        upperLeg_pos = [upperLeg_matrix[12],upperLeg_matrix[13],upperLeg_matrix[14]]
        lowerLeg_pos = [lowerLeg_matrix[12],lowerLeg_matrix[13],lowerLeg_matrix[14]]
        foot_pos = [foot_matrix[12],foot_matrix[13],foot_matrix[14]]
        cmds.setAttr(F"{ik_parent}.LegLength",math.dist(upperLeg_pos,lowerLeg_pos)+math.dist(lowerLeg_pos,foot_pos),k=False,l=True)

        #IKHandle作成
        ikHandle_parent = cmds.group(em=True,n=f"Grp_{clr}_LegIkHandle",p=root_obj)
        ikHandle = cmds.ikHandle(sj=upperLeg_ik_dummy,ee=foot_ik_dummy)[0]
        ikHandle = cmds.parent(ikHandle,ikHandle_parent)[0]
        cmds.setAttr(f"{ikHandle}.t",0,0,0)
        cmds.setAttr(f"{ikHandle_parent}.v",0,l=True)

        #アトリビュート作成
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="stretch",at="float",max=1,min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.stretch",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="multUpperLegStretch",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.multUpperLegStretch",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="multLowerLegStretch",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.multLowerLegStretch",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="multLegStretch",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.multLegStretch",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="legThickness",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.legThickness",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="legUniformScale",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.legUniformScale",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="smoothIK",at="float",max=1,min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.smoothIK",0,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="smoothRange",at="float",min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.smoothRange",5,k=True)

        #計算
        multMatrix1 = cmds.createNode("multMatrix")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'FootIK')]}.FootMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'FootIK')]}.worldMatrix[0]",f"{multMatrix1}.matrixIn[1]")
        distanceBetween1 = cmds.createNode("distanceBetween")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{distanceBetween1}.inMatrix1")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'LegRoot')]}.worldMatrix[0]",f"{distanceBetween1}.inMatrix2")
        aimMatrix1 = cmds.createNode("aimMatrix")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{aimMatrix1}.primaryTargetMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'LegRoot')]}.worldMatrix[0]",f"{aimMatrix1}.inputMatrix")
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{aimMatrix1}.outputMatrix",f"{decomposeMatrix1}.inputMatrix")
        composeMatrix1 = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.connectAttr(F"{decomposeMatrix1}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(F"{decomposeMatrix1}.outputTranslate",f"{composeMatrix1}.inputTranslate")
        multMatrix2 = cmds.createNode("multMatrix")
        composeMatrix2 = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix2}.matrixIn[0]")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix2}.matrixIn[1]")
        floatMath1 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath1}.operation",2)
        cmds.connectAttr(F"{decomposeMatrix1}.outputScaleX",f"{floatMath1}.floatA")
        floatComposite1 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite1}.operation",2)
        cmds.setAttr(f"{floatComposite1}.floatA",1)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.legUniformScale",f"{floatComposite1}.floatB")
        cmds.connectAttr(f"{setting}.advance",f"{floatComposite1}.factor")
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{floatMath1}.floatB")
        floatMath2 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath2}.operation",3)
        cmds.connectAttr(F"{distanceBetween1}.distance",f"{floatMath2}.floatA")
        cmds.connectAttr(F"{floatMath1}.outFloat",f"{floatMath2}.floatB")
        floatMath3 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath3}.operation",1)
        cmds.connectAttr(F"{floatMath2}.outFloat",f"{floatMath3}.floatA")
        cmds.connectAttr(F"{ik_parent}.LegLength",f"{floatMath3}.floatB")
        floatMath4 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath4}.operation",3)
        cmds.connectAttr(F"{floatMath3}.outFloat",f"{floatMath4}.floatA")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.smoothRange",f"{floatMath4}.floatB")
        floatMath5 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath5}.operation",0)
        cmds.setAttr(f"{floatMath5}.floatB",1)
        cmds.connectAttr(F"{floatMath4}.outFloat",f"{floatMath5}.floatA")
        floatMath6 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath6}.operation",2)
        cmds.connectAttr(F"{floatMath5}.outFloat",f"{floatMath6}.floatA")
        cmds.connectAttr(F"{floatMath5}.outFloat",f"{floatMath6}.floatB")
        floatMath7 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath7}.operation",2)
        cmds.setAttr(f"{floatMath7}.floatB",-0.25)
        cmds.connectAttr(F"{floatMath6}.outFloat",f"{floatMath7}.floatA")
        floatMath8 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath8}.operation",0)
        cmds.connectAttr(F"{floatMath5}.outFloat",f"{floatMath8}.floatA")
        cmds.connectAttr(F"{floatMath7}.outFloat",f"{floatMath8}.floatB")
        floatMath9 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath9}.operation",2)
        cmds.connectAttr(F"{floatMath8}.outFloat",f"{floatMath9}.floatA")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.smoothRange",f"{floatMath9}.floatB")
        floatMath10 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath10}.operation",0)
        cmds.connectAttr(F"{floatMath9}.outFloat",f"{floatMath10}.floatB")
        floatMath11 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath11}.operation",1)
        cmds.connectAttr(F"{floatMath11}.outFloat",f"{floatMath10}.floatA")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.smoothRange",f"{floatMath11}.floatB")
        cmds.connectAttr(F"{ik_parent}.LegLength",f"{floatMath11}.floatA")
        condition1 = cmds.createNode("condition")
        condition2 = cmds.createNode("condition")
        cmds.setAttr(f"{condition1}.operation",3)
        cmds.setAttr(f"{condition2}.operation",5)
        cmds.setAttr(f"{condition1}.secondTerm",0)
        cmds.setAttr(f"{condition2}.secondTerm",2)
        cmds.connectAttr(F"{floatMath9}.outFloat",f"{condition1}.firstTerm")
        cmds.connectAttr(F"{floatMath5}.outFloat",f"{condition2}.firstTerm")
        cmds.connectAttr(F"{floatMath10}.outFloat",f"{condition1}.colorIfTrueR")
        cmds.connectAttr(F"{floatMath2}.outFloat",f"{condition1}.colorIfFalseR")
        cmds.connectAttr(F"{condition1}.outColorR",f"{condition2}.colorIfTrueR")
        cmds.connectAttr(F"{ik_parent}.LegLength",f"{condition2}.colorIfFalseR")
        floatMath12 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath12}.operation",2)
        cmds.connectAttr(F"{condition2}.outColorR",f"{floatMath12}.floatA")
        cmds.connectAttr(F"{floatMath1}.outFloat",f"{floatMath12}.floatB")
        floatComposite2 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite2}.operation",2)
        cmds.connectAttr(f"{distanceBetween1}.distance",f"{floatComposite2}.floatA")
        cmds.connectAttr(f"{floatMath12}.outFloat",f"{floatComposite2}.floatB")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.smoothIK",f"{floatComposite2}.factor")
        cmds.connectAttr(F"{floatComposite2}.outFloat",f"{composeMatrix2}.inputTranslateX")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{ikHandle_parent}.offsetParentMatrix")
        distanceBetween2 = cmds.createNode("distanceBetween")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{distanceBetween2}.inMatrix1")
        cmds.connectAttr(F"{ik_parent}.worldMatrix[0]",f"{distanceBetween2}.inMatrix2")
        floatMath13 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath13}.operation",3)
        cmds.connectAttr(F"{distanceBetween2}.distance",f"{floatMath13}.floatA")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{ik_parent}.worldMatrix[0]",f"{decomposeMatrix2}.inputMatrix")
        floatMath14 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath14}.operation",2)
        cmds.connectAttr(F"{decomposeMatrix2}.outputScaleX",f"{floatMath14}.floatA")
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{floatMath14}.floatB")
        floatMath15 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath15}.operation",2)
        cmds.connectAttr(F"{floatMath14}.outFloat",f"{floatMath15}.floatA")
        cmds.connectAttr(F"{ik_parent}.LegLength",f"{floatMath15}.floatB")
        cmds.connectAttr(F"{floatMath15}.outFloat",f"{floatMath13}.floatB")
        floatMath16 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath16}.operation",2)
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{floatMath16}.floatB")
        cmds.connectAttr(F"{floatMath13}.outFloat",f"{floatMath16}.floatA")
        condition3 = cmds.createNode("condition")
        cmds.setAttr(f"{condition3}.operation",2)
        cmds.setAttr(f"{condition3}.secondTerm",1)
        cmds.connectAttr(F"{floatMath16}.outFloat",f"{condition3}.colorIfTrueR")
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{condition3}.colorIfFalseR")
        cmds.connectAttr(F"{floatMath13}.outFloat",f"{condition3}.firstTerm")
        floatComposite3 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite3}.operation",2)
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{floatComposite3}.floatA")
        cmds.connectAttr(f"{condition3}.outColorR",f"{floatComposite3}.floatB")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.stretch",f"{floatComposite3}.factor")
        floatComposite4 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite4}.operation",2)
        cmds.setAttr(f"{floatComposite4}.floatA",1)
        cmds.connectAttr(f"{floatComposite3}.outFloat",f"{floatComposite4}.floatB")
        cmds.connectAttr(f"{setting}.advance",f"{floatComposite4}.factor")
        floatMath17 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath17}.operation",2)
        cmds.connectAttr(F"{floatComposite4}.outFloat",f"{floatMath17}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.multLegStretch",f"{floatMath17}.floatB")
        floatMath18 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath18}.operation",2)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.multLowerLegStretch",f"{floatMath18}.floatA")
        cmds.connectAttr(f"{floatMath17}.outFloat",f"{floatMath18}.floatB")
        floatMath19 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath19}.operation",2)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.multUpperLegStretch",f"{floatMath19}.floatA")
        cmds.connectAttr(f"{floatMath17}.outFloat",f"{floatMath19}.floatB")
        floatComposite5 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite5}.operation",2)
        cmds.setAttr(f"{floatComposite5}.floatA",1)
        cmds.connectAttr(f"{setting}.advance",f"{floatComposite5}.factor")
        cmds.connectAttr(f"{floatMath18}.outFloat",f"{floatComposite5}.floatB")
        floatComposite6 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite6}.operation",2)
        cmds.setAttr(f"{floatComposite6}.floatA",1)
        cmds.connectAttr(f"{setting}.advance",f"{floatComposite6}.factor")
        cmds.connectAttr(f"{floatMath19}.outFloat",f"{floatComposite6}.floatB")

        floatComposite7 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite7}.operation",2)
        cmds.setAttr(f"{floatComposite7}.floatA",1)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.legThickness",f"{floatComposite7}.floatB")
        cmds.connectAttr(f"{setting}.advance",f"{floatComposite7}.factor")
        floatMath20 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath20}.operation",2)
        cmds.connectAttr(f"{floatComposite7}.outFloat",f"{floatMath20}.floatA")
        cmds.connectAttr(f"{floatComposite1}.outFloat",f"{floatMath20}.floatB")

        #UpperLeg
        upperJoint_matrix = cmds.xform(upperLeg_ik_dummy,m=True,ws=True,q=True)
        upper_vec = []
        for i in [0,1,2]:
            upper_vec.append(lowerLeg_pos[i]-upperLeg_pos[i])
        magnitude = math.sqrt(sum(x**2 for x in upper_vec))
        upper_vec = [x / magnitude for x in upper_vec]
        x_vec = []
        for i in [0,1,2]:
            x_vec.append(upperJoint_matrix[i])
        magnitude = math.sqrt(sum(x**2 for x in x_vec))
        x_vec = [x / magnitude for x in x_vec]
        y_vec = []
        for i in [4,5,6]:
            y_vec.append(upperJoint_matrix[i])
        magnitude = math.sqrt(sum(x**2 for x in y_vec))
        y_vec = [x / magnitude for x in y_vec]
        z_vec = []
        for i in [8,9,10]:
            z_vec.append(upperJoint_matrix[i])
        magnitude = math.sqrt(sum(x**2 for x in z_vec))
        z_vec = [x / magnitude for x in z_vec]
        dot=[]
        for i in [x_vec,y_vec,z_vec]:
            dot_product = abs(sum(x * y for x, y in zip(upper_vec, i)))
            dot.append(dot_product)
        if(dot[0]>dot[1] and dot[0]>dot[2]):
            cmds.connectAttr(f"{floatComposite6}.outFloat",f"{upperLeg_ik_dummy}.sx")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{upperLeg_ik_dummy}.sy")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{upperLeg_ik_dummy}.sz")
        elif(dot[1]>dot[0] and dot[1]>dot[2]):
            cmds.connectAttr(f"{floatComposite6}.outFloat",f"{upperLeg_ik_dummy}.sy")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{upperLeg_ik_dummy}.sx")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{upperLeg_ik_dummy}.sz")
        else:
            cmds.connectAttr(f"{floatComposite6}.outFloat",f"{upperLeg_ik_dummy}.sz")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{upperLeg_ik_dummy}.sx")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{upperLeg_ik_dummy}.sy")
        #LowerLeg
        lowerJoint_matrix = cmds.xform(lowerLeg_ik_dummy,m=True,ws=True,q=True)
        lower_vec = []
        for i in [0,1,2]:
            lower_vec.append(foot_pos[i]-lowerLeg_pos[i])
        magnitude = math.sqrt(sum(x**2 for x in lower_vec))
        lower_vec = [x / magnitude for x in lower_vec]
        x_vec = []
        for i in [0,1,2]:
            x_vec.append(lowerJoint_matrix[i])
        magnitude = math.sqrt(sum(x**2 for x in x_vec))
        x_vec = [x / magnitude for x in x_vec]
        y_vec = []
        for i in [4,5,6]:
            y_vec.append(lowerJoint_matrix[i])
        magnitude = math.sqrt(sum(x**2 for x in y_vec))
        y_vec = [x / magnitude for x in y_vec]
        z_vec = []
        for i in [8,9,10]:
            z_vec.append(lowerJoint_matrix[i])
        magnitude = math.sqrt(sum(x**2 for x in z_vec))
        z_vec = [x / magnitude for x in z_vec]
        dot=[]
        for i in [x_vec,y_vec,z_vec]:
            dot_product = abs(sum(x * y for x, y in zip(lower_vec, i)))
            dot.append(dot_product)
        if(dot[0]>dot[1] and dot[0]>dot[2]):
            cmds.connectAttr(f"{floatComposite5}.outFloat",f"{lowerLeg_ik_dummy}.sx")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{lowerLeg_ik_dummy}.sy")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{lowerLeg_ik_dummy}.sz")
        elif(dot[1]>dot[0] and dot[1]>dot[2]):
            cmds.connectAttr(f"{floatComposite5}.outFloat",f"{lowerLeg_ik_dummy}.sy")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{lowerLeg_ik_dummy}.sx")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{lowerLeg_ik_dummy}.sz")
        else:
            cmds.connectAttr(f"{floatComposite5}.outFloat",f"{lowerLeg_ik_dummy}.sz")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{lowerLeg_ik_dummy}.sx")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{lowerLeg_ik_dummy}.sy")

        #足首回転
        Drv_Obj = create_obj_dic[('Drv',clr,'FootIK')]
        Dvn_Obj = foot_ik
        drv_matrix = cmds.xform(Drv_Obj,q=True,ws=True,m=True)
        dvn_matrix = cmds.xform(Dvn_Obj,q=True,ws=True,m=True)
        cmds.addAttr(Drv_Obj,ln="WorldBindMatrix",at="matrix")
        cmds.setAttr(f"{Drv_Obj}.WorldBindMatrix",*drv_matrix,typ="matrix")
        cmds.setAttr(f"{Drv_Obj}.WorldBindMatrix",lock=True, keyable=False)
        cmds.setAttr(f"{Dvn_Obj}.jointOrient" ,*(0,0,0),typ="double3")
        multMatrix1 = cmds.createNode("multMatrix")
        multMatrix2 = cmds.createNode("multMatrix")
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        inverseMatrix = cmds.createNode("inverseMatrix")
        cmds.connectAttr(f"{Drv_Obj}.worldMatrix[0]",f"{multMatrix1}.matrixIn[0]",f=True)
        cmds.connectAttr(f"{Dvn_Obj}.parentInverseMatrix",f"{multMatrix1}.matrixIn[1]",f=True)
        cmds.connectAttr(f"{Drv_Obj}.WorldBindMatrix",f"{inverseMatrix}.inputMatrix",f=True)
        cmds.connectAttr(f"{Dvn_Obj}.WorldBindMatrix",f"{multMatrix2}.matrixIn[0]",f=True)
        cmds.connectAttr(f"{inverseMatrix}.outputMatrix",f"{multMatrix2}.matrixIn[1]")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{multMatrix2}.matrixIn[2]")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(f"{Dvn_Obj}.rotateOrder",f"{decomposeMatrix1}.inputRotateOrder",f=True)
        cmds.connectAttr(f"{decomposeMatrix1}.outputRotate",f"{Dvn_Obj}.r",f=True)
        cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{Dvn_Obj}.s",f=True)
        cmds.connectAttr(f"{decomposeMatrix1}.outputShear",f"{Dvn_Obj}.shear",f=True)

        #つま先
        create_obj_dic |= autorig_utility.create_controller("ToesIK",root_obj,pos_CLR=clr,con_color=(0.2,0.8,0.2),con_shape="scuare",con_scl=(3,3,3),con_rot=(0,0,90),con_pos=(5,0,0),
                                                        setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),drv_scale_offset=(1,scl,1))
        
        matrix = OpenMaya.MMatrix(toes_matrix)*OpenMaya.MMatrix(cmds.xform(foot_ik,q=True,ws=True,m=True)).inverse()
        cmds.addAttr(create_obj_dic[('Con',clr,'ToesIK')],ln="toesMatrix",at="matrix")
        cmds.setAttr(F"{create_obj_dic[('Con',clr,'ToesIK')]}.toesMatrix",*matrix,typ="matrix",k=False,l=True)

        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        composeMatrix1 = cmds.createNode("composeMatrix")
        multMatrix1 = cmds.createNode("multMatrix")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'ToesIK')]}.toesMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(F"{foot_ik}.worldMatrix",f"{multMatrix1}.matrixIn[1]")
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.connectAttr(F"{multMatrix1}.matrixSum",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.worldMatrix",f"{decomposeMatrix2}.inputMatrix")
        cmds.connectAttr(F"{decomposeMatrix2}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(F"{decomposeMatrix2}.outputScale",f"{composeMatrix1}.inputScale")
        cmds.connectAttr(F"{decomposeMatrix1}.outputTranslate",f"{composeMatrix1}.inputTranslate")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{create_obj_dic[('Grp',clr,'ToesIK')]}.offsetParentMatrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'ToesIK')]}.sy",scl)
        autorig_utility.matrix_constraint(Drv_Obj=create_obj_dic[('Drv',clr,'ToesIK')],Dvn_Obj=toes_ik)

        #PoleVector
        #lowerLegに一番近いfootとupperLeg結んだ直線状の点特定
        upperLeg_length = math.dist(upperLeg_pos,lowerLeg_pos)
        lowerLeg_length = math.dist(lowerLeg_pos,foot_pos)
        hiritu = upperLeg_length/(upperLeg_length+lowerLeg_length)
        pos = [(foot_pos[i]-upperLeg_pos[i])*hiritu for i in range(3)]
        length = math.sqrt(((pos[0]+upperLeg_pos[0])-lowerLeg_pos[0])**2+((pos[1]+upperLeg_pos[1])-lowerLeg_pos[1])**2+((pos[2]+upperLeg_pos[2])-lowerLeg_pos[2])**2)
        baitiru = ((upperLeg_length+lowerLeg_length)*0.6)/length
        pv_pos = [((lowerLeg_pos[i]-upperLeg_pos[i])-pos[i])*baitiru+(pos[i]+upperLeg_pos[i]) for i in range(3) ]

        create_obj_dic |= autorig_utility.create_controller("LegPV",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0),con_shape="dia1",con_scl=(2,2,2),con_pos=[pv_pos[i]-(pos[i]+upperLeg_pos[i]) for i in range(3)],
                                                            setting=setting,connect_drv=False,uniform_scale=True)
        cmds.xform(f"{create_obj_dic[('Grp',clr,'LegPV')]}",t=[pos[i]+upperLeg_pos[i] for i in range(3) ],ws=True)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegPV')]}.matrix",f"{create_obj_dic[('Drv',clr,'LegPV')]}.offsetParentMatrix",)
        cmds.xform(f"{create_obj_dic[('Drv',clr,'LegPV')]}",t=pv_pos,ws=True)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'LegPV')]}.sx",scl)
        cmds.poleVectorConstraint(create_obj_dic[('Drv',clr,'LegPV')],ikHandle)

        outputComposeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{outputComposeMatrix}.useEulerRotation",0)
        cmds.connectAttr(f"{outputComposeMatrix}.outputMatrix",f"{create_obj_dic[('Grp',clr,'LegPV')]}.offsetParentMatrix")
        
        rotA_matrix = cmds.xform(create_obj_dic[('Drv',clr,'LegRoot')],q=True,ws=True,m=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegPV')],ln="rotAMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(rotA_matrix).inverse()
        matrix = list(matrix)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegPV')]}.rotAMatrix",matrix,typ="matrix",l=True)
        multMatrixA = cmds.createNode("multMatrix")
        decomposeMatrixA = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegPV')]}.rotAMatrix",f"{multMatrixA}.matrixIn[0]")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'LegRoot')]}.worldMatrix[0]",f"{multMatrixA}.matrixIn[1]")
        cmds.connectAttr(f"{multMatrixA}.matrixSum",f"{decomposeMatrixA}.inputMatrix")
        rotB_matrix = cmds.xform(create_obj_dic[('Drv',clr,'LegIK')],q=True,ws=True,m=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegPV')],ln="rotBMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(rotB_matrix).inverse()
        matrix = list(matrix)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegPV')]}.rotBMatrix",matrix,typ="matrix",l=True)
        multMatrixB = cmds.createNode("multMatrix")
        decomposeMatrixB = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegPV')]}.rotBMatrix",f"{multMatrixB}.matrixIn[0]")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'LegIK')]}.worldMatrix[0]",f"{multMatrixB}.matrixIn[1]")
        cmds.connectAttr(f"{multMatrixB}.matrixSum",f"{decomposeMatrixB}.inputMatrix")
        quatSlerp=cmds.createNode("quatSlerp")
        cmds.connectAttr(f"{decomposeMatrixA}.outputQuat",f"{quatSlerp}.input1Quat")
        cmds.connectAttr(f"{decomposeMatrixB}.outputQuat",f"{quatSlerp}.input2Quat")
        cmds.addAttr(create_obj_dic[('Con',clr,'LegPV')],ln="rotParent",at="float",max=1,min=0,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegPV')]}.rotParent",1)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegPV')]}.rotParent",f"{quatSlerp}.inputT")
        cmds.connectAttr(f"{quatSlerp}.outputQuat",f"{outputComposeMatrix}.inputQuat")
        
        decomposeMatrixA = cmds.createNode("decomposeMatrix")
        decomposeMatrixB = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'LegRoot')]}.worldMatrix[0]",f"{decomposeMatrixA}.inputMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.worldMatrix[0]",f"{decomposeMatrixB}.inputMatrix")
        blendColors = cmds.createNode("blendColors")
        cmds.connectAttr(f"{decomposeMatrixA}.outputTranslate",f"{blendColors}.color1")
        cmds.connectAttr(f"{decomposeMatrixB}.outputTranslate",f"{blendColors}.color2")
        cmds.setAttr(f"{blendColors}.blender",lowerLeg_length/(upperLeg_length+lowerLeg_length))
        cmds.connectAttr(f"{blendColors}.output",f"{outputComposeMatrix}.inputTranslate")
        cmds.xform(f"{create_obj_dic[('Grp',clr,'LegPV')]}",t=[pos[i]+upperLeg_pos[i] for i in range(3) ],ws=True)

        cmds.connectAttr(f"{decomposeMatrixA}.outputScale",f"{outputComposeMatrix}.inputScale")

        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="twist",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.twist",0,k=True)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.twist",f"{ikHandle}.twist")

        #IKFKSwitch
        cmds.setAttr(f"{ik_parent}.v",0,l=True)

        fkCondition = cmds.createNode("condition")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK",f"{fkCondition}.firstTerm")
        cmds.setAttr(f"{fkCondition}.secondTerm",0)
        cmds.setAttr(f"{fkCondition}.operation",1)
        cmds.setAttr(f"{fkCondition}.colorIfTrueR",1)
        cmds.setAttr(f"{fkCondition}.colorIfFalseR",0)
        cmds.setAttr( f"{create_obj_dic[('Grp',clr,'UpperLegFK')]}.v", lock=False)
        cmds.connectAttr(f"{fkCondition}.outColorR",f"{create_obj_dic[('Grp',clr,'UpperLegFK')]}.v")
        cmds.setAttr( f"{create_obj_dic[('Grp',clr,'LowerLegFK')]}.v", lock=False)
        cmds.connectAttr(f"{fkCondition}.outColorR",f"{create_obj_dic[('Grp',clr,'LowerLegFK')]}.v")
        cmds.setAttr( f"{create_obj_dic[('Grp',clr,'FootFK')]}.v", lock=False)
        cmds.connectAttr(f"{fkCondition}.outColorR",f"{create_obj_dic[('Grp',clr,'FootFK')]}.v")
        cmds.setAttr( f"{create_obj_dic[('Grp',clr,'ToesFK')]}.v", lock=False)
        cmds.connectAttr(f"{fkCondition}.outColorR",f"{create_obj_dic[('Grp',clr,'ToesFK')]}.v")

        ikCondition = cmds.createNode("condition")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK",f"{ikCondition}.firstTerm")
        cmds.setAttr(f"{ikCondition}.secondTerm",1)
        cmds.setAttr(f"{ikCondition}.operation",1)
        cmds.setAttr(f"{ikCondition}.colorIfTrueR",1)
        cmds.setAttr(f"{ikCondition}.colorIfFalseR",0)
        cmds.setAttr( f"{create_obj_dic[('Grp',clr,'LegIK')]}.v", lock=False)
        cmds.connectAttr(f"{ikCondition}.outColorR",f"{create_obj_dic[('Grp',clr,'LegIK')]}.v")
        cmds.setAttr( f"{create_obj_dic[('Grp',clr,'FootIK')]}.v", lock=False)
        cmds.connectAttr(f"{ikCondition}.outColorR",f"{create_obj_dic[('Grp',clr,'FootIK')]}.v")
        cmds.setAttr( f"{create_obj_dic[('Grp',clr,'ToesIK')]}.v", lock=False)
        cmds.connectAttr(f"{ikCondition}.outColorR",f"{create_obj_dic[('Grp',clr,'ToesIK')]}.v")
        cmds.setAttr( f"{create_obj_dic[('Grp',clr,'LegPV')]}.v", lock=False)
        cmds.connectAttr(f"{ikCondition}.outColorR",f"{create_obj_dic[('Grp',clr,'LegPV')]}.v")

    return create_obj_dic

def create_arm(character_name:str, parent:str, obj_dic:dict, joint_dic:dict ,orientation_dic:dict):
    """
    リグ作成

    Parameters
    ----------
        string character_name : 名前
        string parent : 親になるオブジェクト
        dictionary obj_dic : 作成済みのオブジェクト
        dictionary joint_dic : ダミーのHUmanoidジョイント
        dictionary orientation_dic : 回転オブジェ

    Returns
    -------
        作成したオブジェ入った辞書
    """
    create_obj_dic={}
    setting = obj_dic[('Con','C','Setting')]

    #親作成
    root_center_obj = cmds.group(em=True,n=f"Grp_C_Arm",p=parent)
    create_obj_dic[('Grp','C','Arm')]=root_center_obj

    hips_joint_matrix = cmds.xform(joint_dic["c_hips"],m=True,ws=True,q=True)
    spine_joint_matrix = cmds.xform(joint_dic["c_spine"],m=True,ws=True,q=True)
    chest_joint_matrix = cmds.xform(joint_dic["c_chest"],m=True,ws=True,q=True)
    head_joint_matrix = cmds.xform(joint_dic["c_head"],m=True,ws=True,q=True)

    #左右繰り返し
    for clr in ("L","R"):
        clr_lower = clr.lower()
        root_obj = cmds.group(em=True,n=f"Grp_{clr}_Arm",p=root_center_obj)
        create_obj_dic[('Grp',clr,'Arm')]=root_obj
        if(clr == "L"):
            scl = 1
        else:
            scl = -1

        #matrix取得
        upperArm_matrix = cmds.xform(orientation_dic[f"{clr_lower}_upperArm"],m=True,ws=True,q=True)
        lowerArm_matrix = cmds.xform(orientation_dic[f"{clr_lower}_lowerArm"],m=True,ws=True,q=True)
        shoulder_matrix = cmds.xform(orientation_dic[f"{clr_lower}_shoulder"],m=True,ws=True,q=True)
        hand_matrix = cmds.xform(orientation_dic[f"{clr_lower}_hand"],m=True,ws=True,q=True)

        #Shoulder
        create_obj_dic |= autorig_utility.create_controller("Shoulder",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0.2),con_shape="cube",con_scl=(3,3,3),con_rot=(0,0,0),
                                                            setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),drv_scale_offset=(1,scl,1))
        cmds.xform(create_obj_dic[('Grp',clr,'Shoulder')],m=shoulder_matrix,ws=True)

        if(f'c_upperChest' not in joint_dic):
            autorig_utility.switch_parent(posA=obj_dic[('Drv','C','ChestIK')],sclA=obj_dic[('Drv','C','Root3')],
                                    rotA=obj_dic[('Drv','C','Root3')],rotB=obj_dic[('Drv','C','ChestIK')],
                                    dvn_con=create_obj_dic[('Con',clr,'Shoulder')],dvn_grp=create_obj_dic[('Grp',clr,'Shoulder')])
        else:
            autorig_utility.switch_parent(posA=obj_dic[('Drv','C','UpperChest')],sclA=obj_dic[('Drv','C','Root3')],
                                    rotA=obj_dic[('Drv','C','Root3')],rotB=obj_dic[('Drv','C','UpperChest')],
                                    dvn_con=create_obj_dic[('Con',clr,'Shoulder')],dvn_grp=create_obj_dic[('Grp',clr,'Shoulder')])


        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'Shoulder')]}.sy",scl)
        autorig_utility.matrix_constraint(Drv_Obj=create_obj_dic[('Drv',clr,'Shoulder')], Dvn_Obj=joint_dic[f"{clr_lower}_shoulder"])
        

        #ダミージョイント複製
        upperArm_fk = cmds.duplicate(joint_dic[f"{clr_lower}_upperArm"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_upperArm"],l=False)[0]+"_fk")[0]
        lowerArm_fk = cmds.duplicate(joint_dic[f"{clr_lower}_lowerArm"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_lowerArm"],l=False)[0]+"_fk")[0]
        hand_fk = cmds.duplicate(joint_dic[f"{clr_lower}_hand"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_hand"],l=False)[0]+"_fk")[0]
        lowerArm_fk = cmds.parent(lowerArm_fk,upperArm_fk)[0]
        hand_fk = cmds.parent(hand_fk,lowerArm_fk)[0]
        cmds.xform(hand_fk,m=hand_matrix,ws=True)
        upperArm_ik = cmds.duplicate(joint_dic[f"{clr_lower}_upperArm"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_upperArm"],l=False)[0]+"_ik")[0]
        lowerArm_ik = cmds.duplicate(joint_dic[f"{clr_lower}_lowerArm"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_lowerArm"],l=False)[0]+"_ik")[0]
        hand_ik = cmds.duplicate(joint_dic[f"{clr_lower}_hand"],f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_hand"],l=False)[0]+"_ik")[0]
        lowerArm_ik = cmds.parent(lowerArm_ik,upperArm_ik)[0]
        hand_ik = cmds.parent(hand_ik,lowerArm_ik)[0]
        cmds.xform(hand_ik,m=hand_matrix,ws=True)

        create_obj_dic[('Joint',clr,'UpperArmFK')]=upperArm_fk
        create_obj_dic[('Joint',clr,'UpperArmIK')]=upperArm_ik
        create_obj_dic[('Joint',clr,'LowerArmFK')]=lowerArm_fk
        create_obj_dic[('Joint',clr,'LowerArmIK')]=lowerArm_ik
        create_obj_dic[('Joint',clr,'HandFK')]=hand_fk

        jointOrient = cmds.getAttr(f"{upperArm_ik}.jointOrient")[0]
        cmds.setAttr(f"{upperArm_ik}.preferredAngleX",jointOrient[0])
        cmds.setAttr(f"{upperArm_ik}.preferredAngleY",jointOrient[1])
        cmds.setAttr(f"{upperArm_ik}.preferredAngleZ",jointOrient[2])
        cmds.setAttr(f"{upperArm_ik}.jointOrient",*(0,0,0),typ="double3")
        rot = cmds.xform(upperArm_ik,ro=True,q=True,ws=False)
        cmds.setAttr(f"{upperArm_ik}.r",*jointOrient,typ="double3")
        cmds.xform(upperArm_ik,eu=True,ro=rot,r=True)


        #IKFK選択
        cmds.addAttr(create_obj_dic[('Con',clr,'Shoulder')],ln="IKFK",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'Shoulder')]}.IKFK",1,k=True)

        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        quatSlerp = cmds.createNode("quatSlerp")
        quatToEuler = cmds.createNode("quatToEuler")
        pairBlend = cmds.createNode("pairBlend")
        blendColors = cmds.createNode("blendColors")
        cmds.connectAttr(f"{upperArm_fk}.jointOrient",f"{joint_dic[f'{clr_lower}_upperArm']}.jointOrient")
        cmds.connectAttr(f"{upperArm_ik}.matrix", f"{decomposeMatrix2}.inputMatrix")
        cmds.connectAttr(f"{upperArm_fk}.matrix", f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{quatSlerp}.input2Quat")
        cmds.connectAttr(f"{decomposeMatrix2}.outputQuat",f"{quatSlerp}.input1Quat")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'Shoulder')]}.IKFK", f"{quatSlerp}.inputT")
        cmds.connectAttr(f"{decomposeMatrix2}.outputTranslate",f"{pairBlend}.inTranslate1")
        cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{pairBlend}.inTranslate2")
        cmds.connectAttr(f"{decomposeMatrix2}.outputScale",f"{pairBlend}.inRotate1")
        cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{pairBlend}.inRotate2")
        cmds.connectAttr(f"{decomposeMatrix2}.outputShear",f"{blendColors}.color2")
        cmds.connectAttr(f"{decomposeMatrix1}.outputShear",f"{blendColors}.color1")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'Shoulder')]}.IKFK", f"{pairBlend}.weight")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'Shoulder')]}.IKFK", f"{blendColors}.blender")
        cmds.connectAttr(f"{quatSlerp}.outputQuat",f"{quatToEuler}.inputQuat")
        cmds.connectAttr(f"{joint_dic[f'{clr_lower}_upperArm']}.rotateOrder",f"{quatToEuler}.inputRotateOrder")
        cmds.connectAttr(f"{quatToEuler}.outputRotate",f"{joint_dic[f'{clr_lower}_upperArm']}.rotate")
        cmds.connectAttr(f"{pairBlend}.outTranslate",f"{joint_dic[f'{clr_lower}_upperArm']}.translate")
        cmds.connectAttr(f"{pairBlend}.outRotate",f"{joint_dic[f'{clr_lower}_upperArm']}.scale")
        cmds.connectAttr(f"{blendColors}.output",f"{joint_dic[f'{clr_lower}_upperArm']}.shear")
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        quatSlerp = cmds.createNode("quatSlerp")
        quatToEuler = cmds.createNode("quatToEuler")
        pairBlend = cmds.createNode("pairBlend")
        blendColors = cmds.createNode("blendColors")
        cmds.connectAttr(f"{lowerArm_fk}.jointOrient",f"{joint_dic[f'{clr_lower}_lowerArm']}.jointOrient")
        cmds.connectAttr(f"{lowerArm_ik}.matrix", f"{decomposeMatrix2}.inputMatrix")
        cmds.connectAttr(f"{lowerArm_fk}.matrix", f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{quatSlerp}.input2Quat")
        cmds.connectAttr(f"{decomposeMatrix2}.outputQuat",f"{quatSlerp}.input1Quat")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'Shoulder')]}.IKFK", f"{quatSlerp}.inputT")
        cmds.connectAttr(f"{decomposeMatrix2}.outputTranslate",f"{pairBlend}.inTranslate1")
        cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{pairBlend}.inTranslate2")
        cmds.connectAttr(f"{decomposeMatrix2}.outputScale",f"{pairBlend}.inRotate1")
        cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{pairBlend}.inRotate2")
        cmds.connectAttr(f"{decomposeMatrix2}.outputShear",f"{blendColors}.color2")
        cmds.connectAttr(f"{decomposeMatrix1}.outputShear",f"{blendColors}.color1")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'Shoulder')]}.IKFK", f"{pairBlend}.weight")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'Shoulder')]}.IKFK", f"{blendColors}.blender")
        cmds.connectAttr(f"{quatSlerp}.outputQuat",f"{quatToEuler}.inputQuat")
        cmds.connectAttr(f"{joint_dic[f'{clr_lower}_lowerArm']}.rotateOrder",f"{quatToEuler}.inputRotateOrder")
        cmds.connectAttr(f"{quatToEuler}.outputRotate",f"{joint_dic[f'{clr_lower}_lowerArm']}.rotate")
        cmds.connectAttr(f"{pairBlend}.outTranslate",f"{joint_dic[f'{clr_lower}_lowerArm']}.translate")
        cmds.connectAttr(f"{pairBlend}.outRotate",f"{joint_dic[f'{clr_lower}_lowerArm']}.scale")
        cmds.connectAttr(f"{blendColors}.output",f"{joint_dic[f'{clr_lower}_lowerArm']}.shear")

        #FK作成
        #UpperArm
        create_obj_dic |= autorig_utility.create_controller("UpperArmFK",root_obj,pos_CLR=clr,con_color=(0.2,0.8,0.8),con_shape="circle",con_scl=(3,3,3),con_rot=(90,90,0),con_pos=(9,0,0),
                                                            setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),drv_scale_offset=(1,scl,1))
        cmds.xform(create_obj_dic[('Grp',clr,'UpperArmFK')],m=upperArm_matrix,ws=True)
        autorig_utility.switch_parent(posA=create_obj_dic[('Drv',clr,'Shoulder')],sclA=obj_dic[('Drv','C','Root3')],
                                    rotA=obj_dic[('Drv','C','Root3')],rotB=obj_dic[('Drv','C','ChestIK')],
                                    dvn_con=create_obj_dic[('Con',clr,'UpperArmFK')],dvn_grp=create_obj_dic[('Grp',clr,'UpperArmFK')])
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'UpperArmFK')]}.sy",scl)
        #LowerArm
        create_obj_dic |= autorig_utility.create_controller("LowerArmFK",root_obj,pos_CLR=clr,con_color=(0.2,0.8,0.8),con_shape="circle",con_scl=(3,3,3),con_rot=(90,90,0),con_pos=(9,0,0),
                                                            setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),drv_scale_offset=(1,scl,1))
        cmds.xform(create_obj_dic[('Grp',clr,'LowerArmFK')],m=lowerArm_matrix,ws=True)

        upperArm_fk_dummy = cmds.group(em=True,n=f"Grp_{clr}_UpparArnDummy",p=root_obj)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'UpperArmFK')]}.worldMatrix[0]",f"{upperArm_fk_dummy}.offsetParentMatrix")
        cmds.setAttr(f"{upperArm_fk_dummy}.sy",scl)
        cmds.setAttr(f"{upperArm_fk_dummy}.t",l=True)
        cmds.setAttr(f"{upperArm_fk_dummy}.r",l=True)
        cmds.setAttr(f"{upperArm_fk_dummy}.s",l=True)
        cmds.setAttr(f"{upperArm_fk_dummy}.v",0,l=True)

        autorig_utility.switch_parent(posA=create_obj_dic[('Drv',clr,'UpperArmFK')],
                                      sclA=upperArm_fk_dummy,sclB=create_obj_dic[('Drv',clr,'UpperArmFK')],
                                    rotA=upperArm_fk_dummy,rotB=create_obj_dic[('Drv',clr,'UpperArmFK')],
                                    dvn_con=create_obj_dic[('Con',clr,'LowerArmFK')],dvn_grp=create_obj_dic[('Grp',clr,'LowerArmFK')])
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'LowerArmFK')]}.sy",scl)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LowerArmFK')]}.rotParent",1)
        
        #接続
        autorig_utility.matrix_constraint(Drv_Obj=create_obj_dic[('Drv',clr,'UpperArmFK')], Dvn_Obj=upperArm_fk)
        autorig_utility.matrix_constraint(Drv_Obj=create_obj_dic[('Drv',clr,'LowerArmFK')], Dvn_Obj=lowerArm_fk)

        #IK作成
        create_obj_dic |= autorig_utility.create_controller("HandIK",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0),con_shape="hexagon1",con_scl=(5,5,5),con_rot=(90,90,0),
                                                            setting=setting,con_rot_lock=(True,True,True),con_scl_lock=(True,True,True),drv_scale_offset=(1,scl,1))
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.sy",scl)
        shoulder_joint_matrix = cmds.xform(joint_dic[f"{clr_lower}_shoulder"],m=True,ws=True,q=True)
        upperArm_joint_matrix = cmds.xform(joint_dic[f"{clr_lower}_upperArm"],m=True,ws=True,q=True)
        lowerArm_joint_matrix = cmds.xform(joint_dic[f"{clr_lower}_lowerArm"],m=True,ws=True,q=True)

        en="Root:Shoulder:Hips:Spine:Chest:Head:LeftUpperLeg:LeftLowerLeg:LeftFoot:RightUpperLeg:RightLowerLeg:RightFoot"
        if(clr=="R"):
            en+=":LeftHand"
        cmds.addAttr(create_obj_dic[('Con',clr,'HandIK')],ln="parent",at="enum",en=en,k=True)
        blendMatrix = cmds.createNode("blendMatrix")
        #Root
        cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="Root3Matrix",at="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.Root3Matrix",*hand_matrix,typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.Root3Matrix",lock=True, keyable=False)
        root_decomposeMatrix = cmds.createNode("decomposeMatrix")
        root_multmatrix=cmds.createNode("multMatrix")
        root_condition=cmds.createNode("condition")
        cmds.setAttr(f"{root_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{root_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{root_condition}.secondTerm",0)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.Root3Matrix",f"{root_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix",f"{root_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix",f"{root_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{root_condition}.firstTerm")
        cmds.connectAttr(f"{root_multmatrix}.matrixSum",f"{blendMatrix}.target[0].targetMatrix")
        cmds.connectAttr(f"{root_condition}.outColorR",f"{blendMatrix}.target[0].weight")
        #回転
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        composeMatrix = cmds.createNode("composeMatrix")
        quatSlerp = cmds.createNode("quatSlerp")
        cmds.setAttr(f"{composeMatrix}.useEulerRotation",0)
        cmds.addAttr(create_obj_dic[('Con',clr,'HandIK')],ln="rotParent",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.rotParent",1,k=True)
        cmds.connectAttr(f"{decomposeMatrix2}.outputQuat",f"{quatSlerp}.input1Quat")
        cmds.connectAttr(f"{blendMatrix}.outputMatrix",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(f"{root_multmatrix}.matrixSum",f"{decomposeMatrix2}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{quatSlerp}.input2Quat")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.rotParent",f"{quatSlerp}.inputT")
        cmds.connectAttr(f"{composeMatrix}.outputMatrix",f"{create_obj_dic[('Grp',clr,'HandIK')]}.offsetParentMatrix")
        cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{composeMatrix}.inputScale")
        cmds.connectAttr(f"{quatSlerp}.outputQuat",f"{composeMatrix}.inputQuat")

        #Shoulder
        cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="ShoulderMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(shoulder_joint_matrix).inverse()
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.ShoulderMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.ShoulderMatrix",lock=True, keyable=False)
        shoulder_decomposeMatrix = cmds.createNode("decomposeMatrix")
        shoulder_composeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{shoulder_composeMatrix}.useEulerRotation",0)
        shoulder_multmatrix=cmds.createNode("multMatrix")
        shoulder_condition=cmds.createNode("condition")
        cmds.setAttr(f"{shoulder_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{shoulder_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{shoulder_condition}.secondTerm",1)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.ShoulderMatrix",f"{shoulder_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{shoulder_composeMatrix}.outputMatrix",f"{shoulder_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{joint_dic[f'{clr_lower}_shoulder']}.worldMatrix",f"{shoulder_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{shoulder_decomposeMatrix}.outputQuat",f"{shoulder_composeMatrix}.inputQuat")
        cmds.connectAttr(f"{shoulder_decomposeMatrix}.outputTranslate",f"{shoulder_composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{shoulder_composeMatrix}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{shoulder_composeMatrix}.inputShear")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{shoulder_condition}.firstTerm")
        cmds.connectAttr(f"{shoulder_multmatrix}.matrixSum",f"{blendMatrix}.target[1].targetMatrix")
        cmds.connectAttr(f"{shoulder_condition}.outColorR",f"{blendMatrix}.target[1].weight")
#Hips
        cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="HipsMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(hips_joint_matrix).inverse()
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.HipsMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.HipsMatrix",lock=True, keyable=False)
        hips_decomposeMatrix = cmds.createNode("decomposeMatrix")
        hips_composeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{hips_composeMatrix}.useEulerRotation",0)
        hips_multmatrix=cmds.createNode("multMatrix")
        hips_condition=cmds.createNode("condition")
        cmds.setAttr(f"{hips_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{hips_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{hips_condition}.secondTerm",2)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.HipsMatrix",f"{hips_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{hips_composeMatrix}.outputMatrix",f"{hips_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{joint_dic[f'c_hips']}.worldMatrix",f"{hips_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{hips_decomposeMatrix}.outputQuat",f"{hips_composeMatrix}.inputQuat")
        cmds.connectAttr(f"{hips_decomposeMatrix}.outputTranslate",f"{hips_composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{hips_composeMatrix}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{hips_composeMatrix}.inputShear")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{hips_condition}.firstTerm")
        cmds.connectAttr(f"{hips_multmatrix}.matrixSum",f"{blendMatrix}.target[2].targetMatrix")
        cmds.connectAttr(f"{hips_condition}.outColorR",f"{blendMatrix}.target[2].weight")
        #Spine
        cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="SpineMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(spine_joint_matrix).inverse()
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.SpineMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.SpineMatrix",lock=True, keyable=False)
        spine_decomposeMatrix = cmds.createNode("decomposeMatrix")
        spine_composeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{spine_composeMatrix}.useEulerRotation",0)
        spine_multmatrix=cmds.createNode("multMatrix")
        spine_condition=cmds.createNode("condition")
        cmds.setAttr(f"{spine_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{spine_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{spine_condition}.secondTerm",3)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.SpineMatrix",f"{spine_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{spine_composeMatrix}.outputMatrix",f"{spine_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{joint_dic[f'c_spine']}.worldMatrix",f"{spine_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{spine_decomposeMatrix}.outputQuat",f"{spine_composeMatrix}.inputQuat")
        cmds.connectAttr(f"{spine_decomposeMatrix}.outputTranslate",f"{spine_composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{spine_composeMatrix}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{spine_composeMatrix}.inputShear")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{spine_condition}.firstTerm")
        cmds.connectAttr(f"{spine_multmatrix}.matrixSum",f"{blendMatrix}.target[3].targetMatrix")
        cmds.connectAttr(f"{spine_condition}.outColorR",f"{blendMatrix}.target[3].weight")
        #Chest
        cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="ChestMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(chest_joint_matrix).inverse()
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.ChestMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.ChestMatrix",lock=True, keyable=False)
        chest_decomposeMatrix = cmds.createNode("decomposeMatrix")
        chest_composeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{chest_composeMatrix}.useEulerRotation",0)
        chest_multmatrix=cmds.createNode("multMatrix")
        chest_condition=cmds.createNode("condition")
        cmds.setAttr(f"{chest_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{chest_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{chest_condition}.secondTerm",4)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.ChestMatrix",f"{chest_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{chest_composeMatrix}.outputMatrix",f"{chest_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{joint_dic[f'c_chest']}.worldMatrix",f"{chest_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{chest_decomposeMatrix}.outputQuat",f"{chest_composeMatrix}.inputQuat")
        cmds.connectAttr(f"{chest_decomposeMatrix}.outputTranslate",f"{chest_composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{chest_composeMatrix}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{chest_composeMatrix}.inputShear")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{chest_condition}.firstTerm")
        cmds.connectAttr(f"{chest_multmatrix}.matrixSum",f"{blendMatrix}.target[4].targetMatrix")
        cmds.connectAttr(f"{chest_condition}.outColorR",f"{blendMatrix}.target[4].weight")
        #Head
        cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="HeadMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(head_joint_matrix).inverse()
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.HeadMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.HeadMatrix",lock=True, keyable=False)
        head_decomposeMatrix = cmds.createNode("decomposeMatrix")
        head_composeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{head_composeMatrix}.useEulerRotation",0)
        head_multmatrix=cmds.createNode("multMatrix")
        head_condition=cmds.createNode("condition")
        cmds.setAttr(f"{head_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{head_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{head_condition}.secondTerm",5)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.HeadMatrix",f"{head_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{head_composeMatrix}.outputMatrix",f"{head_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{joint_dic[f'c_head']}.worldMatrix",f"{head_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputQuat",f"{head_composeMatrix}.inputQuat")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputTranslate",f"{head_composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{head_composeMatrix}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{head_composeMatrix}.inputShear")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{head_condition}.firstTerm")
        cmds.connectAttr(f"{head_multmatrix}.matrixSum",f"{blendMatrix}.target[5].targetMatrix")
        cmds.connectAttr(f"{head_condition}.outColorR",f"{blendMatrix}.target[5].weight")

        #LeftUpperLeg
        l_upperLeg_joint_matrix = cmds.xform(joint_dic["l_upperLeg"],q=True,ws=True,m=True)
        cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="LeftUpperLegMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(l_upperLeg_joint_matrix).inverse()
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.LeftUpperLegMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.LeftUpperLegMatrix",lock=True, keyable=False)
        head_decomposeMatrix = cmds.createNode("decomposeMatrix")
        head_composeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{head_composeMatrix}.useEulerRotation",0)
        head_multmatrix=cmds.createNode("multMatrix")
        head_condition=cmds.createNode("condition")
        cmds.setAttr(f"{head_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{head_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{head_condition}.secondTerm",6)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.LeftUpperLegMatrix",f"{head_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{head_composeMatrix}.outputMatrix",f"{head_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{joint_dic[f'l_upperLeg']}.worldMatrix",f"{head_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputQuat",f"{head_composeMatrix}.inputQuat")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputTranslate",f"{head_composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{head_composeMatrix}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{head_composeMatrix}.inputShear")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{head_condition}.firstTerm")
        cmds.connectAttr(f"{head_multmatrix}.matrixSum",f"{blendMatrix}.target[6].targetMatrix")
        cmds.connectAttr(f"{head_condition}.outColorR",f"{blendMatrix}.target[6].weight")
        #LeftLowerLeg
        l_lowerLeg_joint_matrix = cmds.xform(joint_dic["l_lowerLeg"],q=True,ws=True,m=True)
        cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="LeftLowerLegMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(l_upperLeg_joint_matrix).inverse()
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.LeftLowerLegMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.LeftLowerLegMatrix",lock=True, keyable=False)
        head_decomposeMatrix = cmds.createNode("decomposeMatrix")
        head_composeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{head_composeMatrix}.useEulerRotation",0)
        head_multmatrix=cmds.createNode("multMatrix")
        head_condition=cmds.createNode("condition")
        cmds.setAttr(f"{head_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{head_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{head_condition}.secondTerm",7)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.LeftLowerLegMatrix",f"{head_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{head_composeMatrix}.outputMatrix",f"{head_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{joint_dic[f'l_lowerLeg']}.worldMatrix",f"{head_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputQuat",f"{head_composeMatrix}.inputQuat")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputTranslate",f"{head_composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{head_composeMatrix}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{head_composeMatrix}.inputShear")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{head_condition}.firstTerm")
        cmds.connectAttr(f"{head_multmatrix}.matrixSum",f"{blendMatrix}.target[7].targetMatrix")
        cmds.connectAttr(f"{head_condition}.outColorR",f"{blendMatrix}.target[7].weight")
        #LeftFoot
        l_foot_joint_matrix = cmds.xform(joint_dic["l_foot"],q=True,ws=True,m=True)
        cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="LeftFootMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(l_upperLeg_joint_matrix).inverse()
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.LeftFootMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.LeftFootMatrix",lock=True, keyable=False)
        head_decomposeMatrix = cmds.createNode("decomposeMatrix")
        head_composeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{head_composeMatrix}.useEulerRotation",0)
        head_multmatrix=cmds.createNode("multMatrix")
        head_condition=cmds.createNode("condition")
        cmds.setAttr(f"{head_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{head_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{head_condition}.secondTerm",8)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.LeftFootMatrix",f"{head_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{head_composeMatrix}.outputMatrix",f"{head_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{joint_dic[f'l_foot']}.worldMatrix",f"{head_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputQuat",f"{head_composeMatrix}.inputQuat")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputTranslate",f"{head_composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{head_composeMatrix}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{head_composeMatrix}.inputShear")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{head_condition}.firstTerm")
        cmds.connectAttr(f"{head_multmatrix}.matrixSum",f"{blendMatrix}.target[8].targetMatrix")
        cmds.connectAttr(f"{head_condition}.outColorR",f"{blendMatrix}.target[8].weight")
        #RightUpperLeg
        r_upperLeg_joint_matrix = cmds.xform(joint_dic["r_upperLeg"],q=True,ws=True,m=True)
        cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="RightUpperLegMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(r_upperLeg_joint_matrix).inverse()
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.RightUpperLegMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.RightUpperLegMatrix",lock=True, keyable=False)
        head_decomposeMatrix = cmds.createNode("decomposeMatrix")
        head_composeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{head_composeMatrix}.useEulerRotation",0)
        head_multmatrix=cmds.createNode("multMatrix")
        head_condition=cmds.createNode("condition")
        cmds.setAttr(f"{head_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{head_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{head_condition}.secondTerm",9)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.RightUpperLegMatrix",f"{head_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{head_composeMatrix}.outputMatrix",f"{head_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{joint_dic[f'r_upperLeg']}.worldMatrix",f"{head_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputQuat",f"{head_composeMatrix}.inputQuat")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputTranslate",f"{head_composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{head_composeMatrix}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{head_composeMatrix}.inputShear")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{head_condition}.firstTerm")
        cmds.connectAttr(f"{head_multmatrix}.matrixSum",f"{blendMatrix}.target[9].targetMatrix")
        cmds.connectAttr(f"{head_condition}.outColorR",f"{blendMatrix}.target[9].weight")
        #RightLowerLeg
        r_lowerLeg_joint_matrix = cmds.xform(joint_dic["r_lowerLeg"],q=True,ws=True,m=True)
        cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="RightLowerLegMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(r_lowerLeg_joint_matrix).inverse()
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.RightLowerLegMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.RightLowerLegMatrix",lock=True, keyable=False)
        head_decomposeMatrix = cmds.createNode("decomposeMatrix")
        head_composeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{head_composeMatrix}.useEulerRotation",0)
        head_multmatrix=cmds.createNode("multMatrix")
        head_condition=cmds.createNode("condition")
        cmds.setAttr(f"{head_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{head_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{head_condition}.secondTerm",10)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.RightLowerLegMatrix",f"{head_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{head_composeMatrix}.outputMatrix",f"{head_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{joint_dic[f'r_lowerLeg']}.worldMatrix",f"{head_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputQuat",f"{head_composeMatrix}.inputQuat")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputTranslate",f"{head_composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{head_composeMatrix}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{head_composeMatrix}.inputShear")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{head_condition}.firstTerm")
        cmds.connectAttr(f"{head_multmatrix}.matrixSum",f"{blendMatrix}.target[10].targetMatrix")
        cmds.connectAttr(f"{head_condition}.outColorR",f"{blendMatrix}.target[10].weight")
        #RightFoot
        r_foot_joint_matrix = cmds.xform(joint_dic["r_foot"],q=True,ws=True,m=True)
        cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="RightFootMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(r_foot_joint_matrix).inverse()
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.RightFootMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.RightFootMatrix",lock=True, keyable=False)
        head_decomposeMatrix = cmds.createNode("decomposeMatrix")
        head_composeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{head_composeMatrix}.useEulerRotation",0)
        head_multmatrix=cmds.createNode("multMatrix")
        head_condition=cmds.createNode("condition")
        cmds.setAttr(f"{head_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{head_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{head_condition}.secondTerm",11)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.RightFootMatrix",f"{head_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{head_composeMatrix}.outputMatrix",f"{head_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{joint_dic[f'r_foot']}.worldMatrix",f"{head_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputQuat",f"{head_composeMatrix}.inputQuat")
        cmds.connectAttr(f"{head_decomposeMatrix}.outputTranslate",f"{head_composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{head_composeMatrix}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{head_composeMatrix}.inputShear")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{head_condition}.firstTerm")
        cmds.connectAttr(f"{head_multmatrix}.matrixSum",f"{blendMatrix}.target[11].targetMatrix")
        cmds.connectAttr(f"{head_condition}.outColorR",f"{blendMatrix}.target[11].weight")
        if(clr=="R"):
            #LeftHand
            l_hand_joint_matrix = cmds.xform(joint_dic["l_hand"],q=True,ws=True,m=True)
            cmds.addAttr(create_obj_dic[('Grp',clr,'HandIK')],ln="LeftHandMatrix",at="matrix")
            matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(l_hand_joint_matrix).inverse()
            cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.LeftHandMatrix",list(matrix),typ="matrix")
            cmds.setAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.LeftHandMatrix",lock=True, keyable=False)
            head_decomposeMatrix = cmds.createNode("decomposeMatrix")
            head_composeMatrix = cmds.createNode("composeMatrix")
            cmds.setAttr(f"{head_composeMatrix}.useEulerRotation",0)
            head_multmatrix=cmds.createNode("multMatrix")
            head_condition=cmds.createNode("condition")
            cmds.setAttr(f"{head_condition}.colorIfFalseR",0)
            cmds.setAttr(f"{head_condition}.colorIfTrueR",1)
            cmds.setAttr(f"{head_condition}.secondTerm",12)
            cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'HandIK')]}.LeftHandMatrix",f"{head_multmatrix}.matrixIn[0]")
            cmds.connectAttr(f"{head_composeMatrix}.outputMatrix",f"{head_multmatrix}.matrixIn[1]")
            cmds.connectAttr(f"{joint_dic[f'l_hand']}.worldMatrix",f"{head_decomposeMatrix}.inputMatrix")
            cmds.connectAttr(f"{head_decomposeMatrix}.outputQuat",f"{head_composeMatrix}.inputQuat")
            cmds.connectAttr(f"{head_decomposeMatrix}.outputTranslate",f"{head_composeMatrix}.inputTranslate")
            cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{head_composeMatrix}.inputScale")
            cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{head_composeMatrix}.inputShear")
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.parent",f"{head_condition}.firstTerm")
            cmds.connectAttr(f"{head_multmatrix}.matrixSum",f"{blendMatrix}.target[12].targetMatrix")
            cmds.connectAttr(f"{head_condition}.outColorR",f"{blendMatrix}.target[12].weight")

        matrix = cmds.xform(upperArm_fk,q=True,ws=False,m=True)
        ik_parent = cmds.group(em=True,n=f"Grp_{clr}_ArmIK",p=root_obj)
        create_obj_dic[('Grp',clr,'ArmIK')] = ik_parent
        cmds.addAttr(ik_parent,ln="BindMatrix",at="matrix")
        cmds.setAttr(f"{ik_parent}.BindMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{ik_parent}.BindMatrix",lock=True, keyable=False)
        multMatrix = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{ik_parent}.BindMatrix",f"{multMatrix}.matrixIn[0]")
        cmds.connectAttr(f"{joint_dic[f'{clr_lower}_shoulder']}.worldMatrix",f"{multMatrix}.matrixIn[1]")
        decomposeMatrix = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{multMatrix}.matrixSum",f"{decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix}.outputTranslate",f"{ik_parent}.t")
        cmds.connectAttr(f"{decomposeMatrix}.outputRotate",f"{ik_parent}.r")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{ik_parent}.s")
        cmds.connectAttr(f"{ik_parent}.rotateOrder",f"{decomposeMatrix}.inputRotateOrder")

        upperArm_ik_dummy = cmds.duplicate(upperArm_ik,f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_upperArm"],l=False)[0]+"_ik_dummy")[0]
        lowerArm_ik_dummy = cmds.duplicate(lowerArm_ik,f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_lowerArm"],l=False)[0]+"_ik_dummy")[0]
        hand_ik_dummy = cmds.duplicate(hand_ik,f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_hand"],l=False)[0]+"_ik_dummy")[0]
        upperArm_ik_dummy = cmds.parent(upperArm_ik_dummy,ik_parent)[0]
        lowerArm_ik_dummy = cmds.parent(lowerArm_ik_dummy,upperArm_ik_dummy)[0]
        hand_ik_dummy = cmds.parent(hand_ik_dummy,lowerArm_ik_dummy)[0]
       

        cmds.makeIdentity(upperArm_ik_dummy,a=True,t=False,r=True,s=False,n=False,pn=True)
        cmds.makeIdentity(lowerArm_ik_dummy,a=True,t=False,r=True,s=False,n=False,pn=True)

        autorig_utility.matrix_constraint(upperArm_ik_dummy,upperArm_ik)
        autorig_utility.matrix_constraint(lowerArm_ik_dummy,lowerArm_ik)
        autorig_utility.matrix_constraint(hand_ik_dummy,hand_ik)
        
        orient = cmds.getAttr(f"{lowerArm_ik_dummy}.jointOrient")
        cmds.setAttr(f"{lowerArm_ik_dummy}.preferredAngleX",orient[0][0])
        cmds.setAttr(f"{lowerArm_ik_dummy}.preferredAngleZ",orient[0][1])
        cmds.setAttr(f"{lowerArm_ik_dummy}.preferredAngleY",orient[0][2])

        #IKHandle作成
        ikHandle_parent = cmds.group(em=True,n=f"Grp_{clr}_ArmIkHandle",p=root_obj)
        ikHandle = cmds.ikHandle(sj=upperArm_ik_dummy,ee=hand_ik_dummy,sol='ikRPsolver')[0]
        ikHandle = cmds.parent(ikHandle,ikHandle_parent)[0]
        cmds.setAttr(f"{ikHandle}.v",0,l=True)
        cmds.setAttr(f"{ikHandle}.t",*(0,0,0),typ="double3",l=True)
        cmds.setAttr(f"{ikHandle}.r",*(0,0,0),typ="double3",l=True)
        cmds.setAttr(f"{ikHandle}.s",*(1,1,1),typ="double3",l=True)






        #armLength
        cmds.addAttr(ik_parent,ln="ArmLength",at="float")
        upperArm_pos = [upperArm_matrix[12],upperArm_matrix[13],upperArm_matrix[14]]
        lowerArm_pos = [lowerArm_matrix[12],lowerArm_matrix[13],lowerArm_matrix[14]]
        foot_pos = [hand_matrix[12],hand_matrix[13],hand_matrix[14]]
        length = math.dist(upperArm_pos,lowerArm_pos)+math.dist(lowerArm_pos,foot_pos)
        cmds.setAttr(F"{ik_parent}.ArmLength",length,k=False,l=True)


        #アトリビュート作成
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="stretch",at="float",max=1,min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.stretch",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="multUpperArmStretch",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.multUpperArmStretch",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="multLowerArmStretch",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.multLowerArmStretch",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="multArmStretch",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.multArmStretch",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="armThickness",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.armThickness",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="armUniformScale",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.armUniformScale",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="smoothIK",at="float",max=1,min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.smoothIK",0,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="smoothRange",at="float",min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.smoothRange",5,k=True)

        #matrix
        cmds.addAttr(create_obj_dic[('Drv',clr,'HandIK')],ln="ArmMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(upperArm_matrix)*OpenMaya.MMatrix(shoulder_matrix).inverse()
        cmds.setAttr(F"{create_obj_dic[('Drv',clr,'HandIK')]}.ArmMatrix",*matrix,typ="matrix",k=False,l=True)

        #計算
        multMatrix1 = cmds.createNode("multMatrix")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'HandIK')]}.ArmMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'Shoulder')]}.worldMatrix[0]",f"{multMatrix1}.matrixIn[1]")
        distanceBetween1 = cmds.createNode("distanceBetween")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'HandIK')]}.worldMatrix[0]",f"{distanceBetween1}.inMatrix1")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{distanceBetween1}.inMatrix2")
        aimMatrix1 = cmds.createNode("aimMatrix")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'HandIK')]}.worldMatrix[0]",f"{aimMatrix1}.primaryTargetMatrix")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{aimMatrix1}.inputMatrix")
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{aimMatrix1}.outputMatrix",f"{decomposeMatrix1}.inputMatrix")
        composeMatrix1 = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.connectAttr(F"{decomposeMatrix1}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(F"{decomposeMatrix1}.outputTranslate",f"{composeMatrix1}.inputTranslate")
        multMatrix2 = cmds.createNode("multMatrix")
        composeMatrix2 = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix2}.matrixIn[0]")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix2}.matrixIn[1]")
        floatMath1 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath1}.operation",2)
        cmds.connectAttr(F"{decomposeMatrix1}.outputScaleX",f"{floatMath1}.floatA")
        floatComposite1 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite1}.operation",2)
        cmds.setAttr(f"{floatComposite1}.floatA",1)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.armUniformScale",f"{floatComposite1}.floatB")
        cmds.connectAttr(f"{setting}.advance",f"{floatComposite1}.factor")
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{floatMath1}.floatB")
        floatMath2 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath2}.operation",3)
        cmds.connectAttr(F"{distanceBetween1}.distance",f"{floatMath2}.floatA")
        cmds.connectAttr(F"{floatMath1}.outFloat",f"{floatMath2}.floatB")
        floatMath3 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath3}.operation",1)
        cmds.connectAttr(F"{floatMath2}.outFloat",f"{floatMath3}.floatA")
        cmds.connectAttr(F"{ik_parent}.ArmLength",f"{floatMath3}.floatB")
        floatMath4 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath4}.operation",3)
        cmds.connectAttr(F"{floatMath3}.outFloat",f"{floatMath4}.floatA")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'HandIK')]}.smoothRange",f"{floatMath4}.floatB")
        floatMath5 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath5}.operation",0)
        cmds.setAttr(f"{floatMath5}.floatB",1)
        cmds.connectAttr(F"{floatMath4}.outFloat",f"{floatMath5}.floatA")
        floatMath6 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath6}.operation",2)
        cmds.connectAttr(F"{floatMath5}.outFloat",f"{floatMath6}.floatA")
        cmds.connectAttr(F"{floatMath5}.outFloat",f"{floatMath6}.floatB")
        floatMath7 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath7}.operation",2)
        cmds.setAttr(f"{floatMath7}.floatB",-0.25)
        cmds.connectAttr(F"{floatMath6}.outFloat",f"{floatMath7}.floatA")
        floatMath8 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath8}.operation",0)
        cmds.connectAttr(F"{floatMath5}.outFloat",f"{floatMath8}.floatA")
        cmds.connectAttr(F"{floatMath7}.outFloat",f"{floatMath8}.floatB")
        floatMath9 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath9}.operation",2)
        cmds.connectAttr(F"{floatMath8}.outFloat",f"{floatMath9}.floatA")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'HandIK')]}.smoothRange",f"{floatMath9}.floatB")
        floatMath10 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath10}.operation",0)
        cmds.connectAttr(F"{floatMath9}.outFloat",f"{floatMath10}.floatB")
        floatMath11 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath11}.operation",1)
        cmds.connectAttr(F"{floatMath11}.outFloat",f"{floatMath10}.floatA")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'HandIK')]}.smoothRange",f"{floatMath11}.floatB")
        cmds.connectAttr(F"{ik_parent}.ArmLength",f"{floatMath11}.floatA")
        condition1 = cmds.createNode("condition")
        condition2 = cmds.createNode("condition")
        cmds.setAttr(f"{condition1}.operation",3)
        cmds.setAttr(f"{condition2}.operation",5)
        cmds.setAttr(f"{condition1}.secondTerm",0)
        cmds.setAttr(f"{condition2}.secondTerm",2)
        cmds.connectAttr(F"{floatMath9}.outFloat",f"{condition1}.firstTerm")
        cmds.connectAttr(F"{floatMath5}.outFloat",f"{condition2}.firstTerm")
        cmds.connectAttr(F"{floatMath10}.outFloat",f"{condition1}.colorIfTrueR")
        cmds.connectAttr(F"{floatMath2}.outFloat",f"{condition1}.colorIfFalseR")
        cmds.connectAttr(F"{condition1}.outColorR",f"{condition2}.colorIfTrueR")
        cmds.connectAttr(F"{ik_parent}.ArmLength",f"{condition2}.colorIfFalseR")
        floatMath12 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath12}.operation",2)
        cmds.connectAttr(F"{condition2}.outColorR",f"{floatMath12}.floatA")
        cmds.connectAttr(F"{floatMath1}.outFloat",f"{floatMath12}.floatB")
        floatComposite2 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite2}.operation",2)
        cmds.connectAttr(f"{distanceBetween1}.distance",f"{floatComposite2}.floatA")
        cmds.connectAttr(f"{floatMath12}.outFloat",f"{floatComposite2}.floatB")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.smoothIK",f"{floatComposite2}.factor")
        cmds.connectAttr(F"{floatComposite2}.outFloat",f"{composeMatrix2}.inputTranslateX")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{ikHandle_parent}.offsetParentMatrix")
        distanceBetween2 = cmds.createNode("distanceBetween")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{distanceBetween2}.inMatrix1")
        cmds.connectAttr(F"{ik_parent}.worldMatrix[0]",f"{distanceBetween2}.inMatrix2")
        floatMath13 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath13}.operation",3)
        cmds.connectAttr(F"{distanceBetween2}.distance",f"{floatMath13}.floatA")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{ik_parent}.worldMatrix[0]",f"{decomposeMatrix2}.inputMatrix")
        floatMath14 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath14}.operation",2)
        cmds.connectAttr(F"{decomposeMatrix2}.outputScaleX",f"{floatMath14}.floatA")
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{floatMath14}.floatB")
        floatMath15 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath15}.operation",2)
        cmds.connectAttr(F"{floatMath14}.outFloat",f"{floatMath15}.floatA")
        cmds.connectAttr(F"{ik_parent}.ArmLength",f"{floatMath15}.floatB")
        cmds.connectAttr(F"{floatMath15}.outFloat",f"{floatMath13}.floatB")
        floatMath16 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath16}.operation",2)
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{floatMath16}.floatB")
        cmds.connectAttr(F"{floatMath13}.outFloat",f"{floatMath16}.floatA")
        condition3 = cmds.createNode("condition")
        cmds.setAttr(f"{condition3}.operation",2)
        cmds.setAttr(f"{condition3}.secondTerm",1)
        cmds.connectAttr(F"{floatMath16}.outFloat",f"{condition3}.colorIfTrueR")
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{condition3}.colorIfFalseR")
        cmds.connectAttr(F"{floatMath13}.outFloat",f"{condition3}.firstTerm")
        floatComposite3 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite3}.operation",2)
        cmds.connectAttr(F"{floatComposite1}.outFloat",f"{floatComposite3}.floatA")
        cmds.connectAttr(f"{condition3}.outColorR",f"{floatComposite3}.floatB")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.stretch",f"{floatComposite3}.factor")
        floatComposite4 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite4}.operation",2)
        cmds.setAttr(f"{floatComposite4}.floatA",1)
        cmds.connectAttr(f"{floatComposite3}.outFloat",f"{floatComposite4}.floatB")
        cmds.connectAttr(f"{setting}.advance",f"{floatComposite4}.factor")
        floatMath17 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath17}.operation",2)
        cmds.connectAttr(F"{floatComposite4}.outFloat",f"{floatMath17}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.multArmStretch",f"{floatMath17}.floatB")
        floatMath18 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath18}.operation",2)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.multLowerArmStretch",f"{floatMath18}.floatA")
        cmds.connectAttr(f"{floatMath17}.outFloat",f"{floatMath18}.floatB")
        floatMath19 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath19}.operation",2)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.multUpperArmStretch",f"{floatMath19}.floatA")
        cmds.connectAttr(f"{floatMath17}.outFloat",f"{floatMath19}.floatB")
        floatComposite5 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite5}.operation",2)
        cmds.setAttr(f"{floatComposite5}.floatA",1)
        cmds.connectAttr(f"{setting}.advance",f"{floatComposite5}.factor")
        cmds.connectAttr(f"{floatMath18}.outFloat",f"{floatComposite5}.floatB")
        floatComposite6 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite6}.operation",2)
        cmds.setAttr(f"{floatComposite6}.floatA",1)
        cmds.connectAttr(f"{setting}.advance",f"{floatComposite6}.factor")
        cmds.connectAttr(f"{floatMath19}.outFloat",f"{floatComposite6}.floatB")

        floatComposite7 = cmds.createNode("floatComposite")
        cmds.setAttr(f"{floatComposite7}.operation",2)
        cmds.setAttr(f"{floatComposite7}.floatA",1)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.armThickness",f"{floatComposite7}.floatB")
        cmds.connectAttr(f"{setting}.advance",f"{floatComposite7}.factor")
        floatMath20 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath20}.operation",2)
        cmds.connectAttr(f"{floatComposite7}.outFloat",f"{floatMath20}.floatA")
        cmds.connectAttr(f"{floatComposite1}.outFloat",f"{floatMath20}.floatB")

        #UpperArm
        upperJoint_matrix = cmds.xform(upperArm_ik_dummy,m=True,ws=True,q=True)
        upper_vec = []
        for i in [0,1,2]:
            upper_vec.append(lowerArm_pos[i]-upperArm_pos[i])
        magnitude = math.sqrt(sum(x**2 for x in upper_vec))
        upper_vec = [x / magnitude for x in upper_vec]
        x_vec = []
        for i in [0,1,2]:
            x_vec.append(upperJoint_matrix[i])
        magnitude = math.sqrt(sum(x**2 for x in x_vec))
        x_vec = [x / magnitude for x in x_vec]
        y_vec = []
        for i in [4,5,6]:
            y_vec.append(upperJoint_matrix[i])
        magnitude = math.sqrt(sum(x**2 for x in y_vec))
        y_vec = [x / magnitude for x in y_vec]
        z_vec = []
        for i in [8,9,10]:
            z_vec.append(upperJoint_matrix[i])
        magnitude = math.sqrt(sum(x**2 for x in z_vec))
        z_vec = [x / magnitude for x in z_vec]
        dot=[]
        for i in [x_vec,y_vec,z_vec]:
            dot_product = abs(sum(x * y for x, y in zip(upper_vec, i)))
            dot.append(dot_product)
        if(dot[0]>dot[1] and dot[0]>dot[2]):
            cmds.connectAttr(f"{floatComposite6}.outFloat",f"{upperArm_ik_dummy}.sx")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{upperArm_ik_dummy}.sy")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{upperArm_ik_dummy}.sz")
        elif(dot[1]>dot[0] and dot[1]>dot[2]):
            cmds.connectAttr(f"{floatComposite6}.outFloat",f"{upperArm_ik_dummy}.sy")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{upperArm_ik_dummy}.sx")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{upperArm_ik_dummy}.sz")
        else:
            cmds.connectAttr(f"{floatComposite6}.outFloat",f"{upperArm_ik_dummy}.sz")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{upperArm_ik_dummy}.sx")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{upperArm_ik_dummy}.sy")
        #LowerLeg
        lowerJoint_matrix = cmds.xform(lowerArm_ik_dummy,m=True,ws=True,q=True)
        lower_vec = []
        for i in [0,1,2]:
            lower_vec.append(foot_pos[i]-lowerArm_pos[i])
        magnitude = math.sqrt(sum(x**2 for x in lower_vec))
        lower_vec = [x / magnitude for x in lower_vec]
        x_vec = []
        for i in [0,1,2]:
            x_vec.append(lowerJoint_matrix[i])
        magnitude = math.sqrt(sum(x**2 for x in x_vec))
        x_vec = [x / magnitude for x in x_vec]
        y_vec = []
        for i in [4,5,6]:
            y_vec.append(lowerJoint_matrix[i])
        magnitude = math.sqrt(sum(x**2 for x in y_vec))
        y_vec = [x / magnitude for x in y_vec]
        z_vec = []
        for i in [8,9,10]:
            z_vec.append(lowerJoint_matrix[i])
        magnitude = math.sqrt(sum(x**2 for x in z_vec))
        z_vec = [x / magnitude for x in z_vec]
        dot=[]
        for i in [x_vec,y_vec,z_vec]:
            dot_product = abs(sum(x * y for x, y in zip(lower_vec, i)))
            dot.append(dot_product)
        if(dot[0]>dot[1] and dot[0]>dot[2]):
            cmds.connectAttr(f"{floatComposite5}.outFloat",f"{lowerArm_ik_dummy}.sx")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{lowerArm_ik_dummy}.sy")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{lowerArm_ik_dummy}.sz")
        elif(dot[1]>dot[0] and dot[1]>dot[2]):
            cmds.connectAttr(f"{floatComposite5}.outFloat",f"{lowerArm_ik_dummy}.sy")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{lowerArm_ik_dummy}.sx")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{lowerArm_ik_dummy}.sz")
        else:
            cmds.connectAttr(f"{floatComposite5}.outFloat",f"{lowerArm_ik_dummy}.sz")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{lowerArm_ik_dummy}.sx")
            cmds.connectAttr(f"{floatMath20}.outFloat",f"{lowerArm_ik_dummy}.sy")


        #poleVector作成
        composeMatrix1 = cmds.createNode("composeMatrix")
        blendColors1 = cmds.createNode("blendColors")
        handIk_decomposeMatrix = cmds.createNode("decomposeMatrix")
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{composeMatrix1}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{composeMatrix1}.inputShear")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(f"{shoulder_decomposeMatrix}.outputTranslate",f"{blendColors1}.color1")
        cmds.connectAttr(f"{handIk_decomposeMatrix}.outputTranslate",f"{blendColors1}.color2")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'HandIK')]}.worldMatrix",f"{handIk_decomposeMatrix}.inputMatrix")
        cmds.setAttr(f"{blendColors1}.blender",0.5)
        cmds.connectAttr(f"{blendColors1}.output",f"{composeMatrix1}.inputTranslate")
        lowerArm_pos = cmds.xform(orientation_dic[f"{clr_lower}_lowerArm"],ws=True,t=True,q=True)
        hand_pos = cmds.xform(orientation_dic[f"{clr_lower}_hand"],ws=True,t=True,q=True)
        upperArm_pos = cmds.xform(orientation_dic[f"{clr_lower}_upperArm"],ws=True,t=True,q=True)
        upperArm_length = math.sqrt((upperArm_pos[0]-lowerArm_pos[0])**2+(upperArm_pos[1]-lowerArm_pos[1])**2+(upperArm_pos[2]-lowerArm_pos[2])**2)
        lowerArm_length = math.sqrt((hand_pos[0]-lowerArm_pos[0])**2+(hand_pos[1]-lowerArm_pos[1])**2+(hand_pos[2]-lowerArm_pos[2])**2)

        #lowerArmに一番近いhandとupperArm結んだ直線状の点特定
        hiritu = upperArm_length/(upperArm_length+lowerArm_length)
        pos = [(hand_pos[i]-upperArm_pos[i])*hiritu for i in range(3)]
        length = math.sqrt(((pos[0]+upperArm_pos[0])-lowerArm_pos[0])**2+((pos[1]+upperArm_pos[1])-lowerArm_pos[1])**2+((pos[2]+upperArm_pos[2])-lowerArm_pos[2])**2)
        baitiru = ((upperArm_length+lowerArm_length)*0.6)/length

        pv_pos = [((lowerArm_pos[i]-upperArm_pos[i])-pos[i])*baitiru+(pos[i]+upperArm_pos[i]) for i in range(3) ]


        create_obj_dic |= autorig_utility.create_controller("ArmPV",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0),con_shape="dia1",con_scl=(2,2,2),con_pos=[pv_pos[i]-(pos[i]+upperArm_pos[i]) for i in range(3)],
                                                            setting=setting,uniform_scale=True,connect_drv=False)
        
        cmds.connectAttr(F"{composeMatrix1}.outputMatrix",f"{create_obj_dic[('Grp',clr,'ArmPV')]}.offsetParentMatrix")
        cmds.xform(f"{create_obj_dic[('Grp',clr,'ArmPV')]}",t=[pos[i]+upperArm_pos[i] for i in range(3) ],ws=True)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'ArmPV')]}.sx",scl)
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'ArmPV')]}.matrix",F"{create_obj_dic[('Drv',clr,'ArmPV')]}.offsetParentMatrix")
        cmds.xform(f"{create_obj_dic[('Drv',clr,'ArmPV')]}",t=pv_pos,ws=True)
        cmds.poleVectorConstraint(create_obj_dic[('Drv',clr,'ArmPV')],ikHandle)

        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="twist",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.twist",0,k=True)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.twist",f"{ikHandle}.twist")

        cmds.setAttr(f"{lowerArm_ik_dummy}.preferredAngleX",0)
        cmds.setAttr(f"{lowerArm_ik_dummy}.preferredAngleY",0)
        cmds.setAttr(f"{lowerArm_ik_dummy}.preferredAngleZ",0)

        
        #IKFKSwitch
        cmds.setAttr(f"{ik_parent}.v",0,l=True)

        fkCondition = cmds.createNode("condition")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'Shoulder')]}.IKFK",f"{fkCondition}.firstTerm")
        cmds.setAttr(f"{fkCondition}.secondTerm",0)
        cmds.setAttr(f"{fkCondition}.operation",1)
        cmds.setAttr(f"{fkCondition}.colorIfTrueR",1)
        cmds.setAttr(f"{fkCondition}.colorIfFalseR",0)
        cmds.setAttr( f"{create_obj_dic[('Grp',clr,'LowerArmFK')]}.v", lock=False)
        cmds.connectAttr(f"{fkCondition}.outColorR",f"{create_obj_dic[('Grp',clr,'LowerArmFK')]}.v")
        cmds.setAttr( f"{create_obj_dic[('Grp',clr,'UpperArmFK')]}.v", lock=False)
        cmds.connectAttr(f"{fkCondition}.outColorR",f"{create_obj_dic[('Grp',clr,'UpperArmFK')]}.v")

        ikCondition = cmds.createNode("condition")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'Shoulder')]}.IKFK",f"{ikCondition}.firstTerm")
        cmds.setAttr(f"{ikCondition}.secondTerm",1)
        cmds.setAttr(f"{ikCondition}.operation",1)
        cmds.setAttr(f"{ikCondition}.colorIfTrueR",1)
        cmds.setAttr(f"{ikCondition}.colorIfFalseR",0)
        cmds.setAttr( f"{create_obj_dic[('Grp',clr,'ArmPV')]}.v", lock=False)
        cmds.connectAttr(f"{ikCondition}.outColorR",f"{create_obj_dic[('Grp',clr,'ArmPV')]}.v")
        cmds.setAttr( f"{create_obj_dic[('Grp',clr,'HandIK')]}.v", lock=False)
        cmds.connectAttr(f"{ikCondition}.outColorR",f"{create_obj_dic[('Grp',clr,'HandIK')]}.v")

    return create_obj_dic

def create_hand(character_name:str, parent:str, obj_dic:dict, joint_dic:dict ,orientation_dic:dict):
    """
    リグ作成

    Parameters
    ----------
        string character_name : 名前
        string parent : 親になるオブジェクト
        dictionary obj_dic : 作成済みのオブジェクト
        dictionary joint_dic : ダミーのHUmanoidジョイント
        dictionary orientation_dic : 回転オブジェ
        dictionary pos_dic : 位置の基準

    Returns
    -------
        作成したオブジェ入った辞書
    """
    create_obj_dic={}
    setting = obj_dic[('Con','C','Setting')]

    #親作成
    root_center_obj = cmds.group(em=True,n=f"Grp_C_Hand",p=parent)
    create_obj_dic[('Grp','C','Hand')]=root_center_obj

    #左右繰り返し
    for clr in ("L","R"):
        clr_lower = clr.lower()
        root_obj = cmds.group(em=True,n=f"Grp_{clr}_Hand",p=root_center_obj)
        create_obj_dic[('Grp',clr,'Hand')]=root_obj
        if(clr == "L"):
            scl = 1
        else:
            scl = -1

        hand_matrix = cmds.xform(orientation_dic[f'{clr_lower}_hand'],q=True,ws=True,m=True)

        #手首 Hand
        create_obj_dic |= autorig_utility.create_controller("Wrist",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0),con_shape="cube",con_scl=(4,4,4),con_rot=(90,90,0),con_pos=(2,0,0),
                                                            setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True),uniform_scale=True,drv_scale_offset=(1,scl,1))
        cmds.xform(create_obj_dic[('Grp',clr,'Wrist')],m=hand_matrix,ws=True)
        autorig_utility.switch_parent(posA=joint_dic[f'{clr_lower}_lowerArm'],sclA=obj_dic[('Drv','C','Root3')],
                                      rotA=obj_dic[('Drv','C','Root3')],rotB=joint_dic[f'{clr_lower}_lowerArm'],
                                      dvn_grp=create_obj_dic[('Grp',clr,'Wrist')],dvn_con=create_obj_dic[('Con',clr,'Wrist')])
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'Wrist')]}.sy",scl)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'Wrist')]}.rotParent",1)
        autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv',clr,'Wrist')]}",joint_dic[f'{clr_lower}_hand'])

        #指一括操作コントローラー
        create_obj_dic |= autorig_utility.create_controller("FingerBundle",root_obj,pos_CLR=clr,con_color=(0.8,0.2,0.2),con_shape="triangular",con_scl=(2,2,2),con_rot=(-90,0,0),
                                                            setting=setting,drv_scale_offset=(1,scl,1),uniform_scale=True)
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'Wrist')]}.worldMatrix",f"{create_obj_dic[('Grp',clr,'FingerBundle')]}.offsetParentMatrix")
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'FingerBundle')]}.tx",3)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'FingerBundle')]}.sy",scl)

        finger_name_list = ("Thumb","Index","Middle","Ring","Little")
        number_name_list=("Root","Proximal","Intermediate","Distal")


        for finger in finger_name_list:
            for number in range(4):
                name = f"{finger}{number_name_list[number]}"
                #根本
                if(number==0):
                    create_obj_dic[('Grp',clr,name)]=cmds.group(em=True,n=f"Grp_{clr}_{name}",p=root_obj)
                    create_obj_dic[('Drv',clr,name)]=cmds.group(em=True,n=f"Drv_{clr}_{name}",p=create_obj_dic[('Grp',clr,name)])
                    matrix = cmds.xform(orientation_dic[f'{clr_lower}_{finger.lower()}1'],ws=True,q=True,m=True)

                    #中手骨
                    if(f'{clr_lower}_{finger.lower()}0' in joint_dic):
                        metacarpal_joint = joint_dic[f'{clr_lower}_{finger.lower()}0']
                        metacarpal_name = f'{finger}Metacarpal'
                        create_obj_dic |= autorig_utility.create_controller(metacarpal_name,root_obj,pos_CLR=clr,con_color=(0.2,0.8,0.8),con_shape="arrorSingle",con_scl=(1,1,1),drv_scale_offset=(1,scl,1),
                                                                            con_rot=(90,180,-90),setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True))
                        metacarpal_matrix = cmds.xform(orientation_dic[f'{clr_lower}_{finger.lower()}0'],ws=True,q=True,m=True)
                        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'Wrist')]}.worldMatrix",f"{create_obj_dic[('Grp',clr,metacarpal_name)]}.offsetParentMatrix")
                        cmds.xform(create_obj_dic[('Grp',clr,metacarpal_name)],ws=True,m=metacarpal_matrix)

                        cmds.xform(create_obj_dic[('Grp',clr,name)],ws=True,m=matrix)
                        autorig_utility.switch_parent(posA=create_obj_dic[('Drv',clr,metacarpal_name)],sclA=create_obj_dic[('Drv',clr,metacarpal_name)],
                                  rotA=create_obj_dic[('Drv',clr,'Wrist')],rotB=create_obj_dic[('Drv',clr,metacarpal_name)],
                                  dvn_con=create_obj_dic[('Grp',clr,name)],dvn_grp=create_obj_dic[('Grp',clr,name)])
                        cmds.addAttr(create_obj_dic[('Con',clr,metacarpal_name)],ln="rotParent",at="float",max=1,min=0,k=True)
                        cmds.connectAttr(F"{create_obj_dic[('Con',clr,metacarpal_name)]}.rotParent",F"{create_obj_dic[('Grp',clr,name)]}.rotParent")

                        joint=joint_dic[f'{clr_lower}_{finger.lower()}{0}']
                        autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv',clr,metacarpal_name)]}",joint)
                    else:
                        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'Wrist')]}.worldMatrix",f"{create_obj_dic[('Grp',clr,name)]}.offsetParentMatrix")
                        cmds.xform(create_obj_dic[('Grp',clr,name)],ws=True,m=matrix)

                    cmds.addAttr(create_obj_dic[('Drv',clr,name)],ln="WorldBindMatrix",at="matrix")
                    cmds.setAttr(f"{create_obj_dic[('Drv',clr,name)]}.WorldBindMatrix",*matrix,typ="matrix")
                    cmds.setAttr(f"{create_obj_dic[('Drv',clr,name)]}.WorldBindMatrix",lock=True, keyable=False)
                else:
                    parent_name = f"{finger}{number_name_list[number-1]}"
                    root_name = f"{finger}{number_name_list[0]}"
                    matrix = cmds.xform(orientation_dic[f'{clr_lower}_{finger.lower()}{number}'],ws=True,q=True,m=True)

                    create_obj_dic |= autorig_utility.create_controller(name,root_obj,pos_CLR=clr,con_color=(0.2,0.8,0.8),con_shape="pentagon",con_scl=(1,1,1),drv_scale_offset=(1,scl,1),
                                                                            con_rot=(0,180,90),setting=setting,con_advance_pos=(True,True,True),con_advance_scl=(True,True,True))
                    cmds.xform(create_obj_dic[('Grp',clr,name)],ws=True,m=matrix)
                    autorig_utility.switch_parent(posA=create_obj_dic[('Drv',clr,parent_name)],
                                      sclA=create_obj_dic[('Drv',clr,'Wrist')],sclB=create_obj_dic[('Drv',clr,parent_name)],
                                    rotA=create_obj_dic[('Drv',clr,'Wrist')],rotB=create_obj_dic[('Drv',clr,parent_name)],
                                    dvn_con=create_obj_dic[('Con',clr,name)],dvn_grp=create_obj_dic[('Grp',clr,name)],postScl=True)
                    cmds.setAttr(f"{create_obj_dic[('Con',clr,name)]}.rotParent",1)
                    cmds.setAttr(f"{create_obj_dic[('Grp',clr,name)]}.sy",scl)

                    create_obj_dic[('Dvn',clr,name)]=cmds.group(em=True,n=f"Dvn_{clr}_{name}",p=create_obj_dic[('Grp',clr,name)])
                    create_obj_dic.update({('Con',clr,name):cmds.parent(create_obj_dic[('Con',clr,name)],create_obj_dic[('Dvn',clr,name)])[0]})
                    create_obj_dic.update({('Drv',clr,name):cmds.parent(create_obj_dic[('Drv',clr,name)],create_obj_dic[('Dvn',clr,name)])[0]})

                    joint=joint_dic[f'{clr_lower}_{finger.lower()}{number}']
                    autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv',clr,name)]}",joint)


                    #一括制御用
                    eulerToQuatT = cmds.createNode("eulerToQuat")
                    eulerToQuatR = cmds.createNode("eulerToQuat")
                    quatSlerpT = cmds.createNode("quatSlerp")
                    quatSlerpR = cmds.createNode("quatSlerp")
                    cmds.connectAttr(f"{eulerToQuatT}.outputQuat",F"{quatSlerpT}.input2Quat")
                    cmds.connectAttr(f"{eulerToQuatR}.outputQuat",F"{quatSlerpR}.input2Quat")
                    cmds.connectAttr(F"{create_obj_dic[('Con',clr,'FingerBundle')]}.rotateOrder",f"{eulerToQuatT}.inputRotateOrder")
                    cmds.connectAttr(F"{create_obj_dic[('Con',clr,'FingerBundle')]}.rotateOrder",f"{eulerToQuatR}.inputRotateOrder")
                    cmds.connectAttr(F"{create_obj_dic[('Con',clr,'FingerBundle')]}.sx",F"{quatSlerpT}.inputT")
                    cmds.connectAttr(F"{create_obj_dic[('Con',clr,'FingerBundle')]}.sx",F"{quatSlerpR}.inputT")

                    quatProd1 = cmds.createNode("quatProd")
                    quatToEuler1 = cmds.createNode("quatToEuler")
                    cmds.connectAttr(f"{quatSlerpT}.outputQuat",F"{quatProd1}.input2Quat")
                    cmds.connectAttr(f"{quatSlerpR}.outputQuat",F"{quatProd1}.input1Quat")
                    cmds.connectAttr(F"{quatProd1}.outputQuat",f"{quatToEuler1}.inputQuat")
                    cmds.connectAttr(f"{quatToEuler1}.outputRotate",f"{create_obj_dic[('Dvn',clr,name)]}.rotate")
                    cmds.connectAttr(f"{create_obj_dic[('Dvn',clr,name)]}.rotateOrder",f"{quatToEuler1}.inputRotateOrder")

                    #一括制御用(グリップポーズ): FingerBundleのtranslate/rotateに関節ごとの重み
                    #(name+軸のカスタムAttr)を掛けてeulerToQuatT/Rへ渡す。
                    #  以前は軸ごとにfloatMath(乗算)を作りeulerToQuatT/R.inputRotateX/Y/Zへ個別接続していたが、
                    #  floatMathの出力(単位型を持たない一般のfloat)を角度チャンネルへ軸ごとに直結すると
                    #  Mayaが自動でunitConversionノードを挟む(このリグのunitConversionの半数以上がここ由来だった)。
                    #  multiplyDivide1個+.inputRotateへの複合アトリビュート接続にまとめて回避する。
                    fingerBundle_con = create_obj_dic[('Con',clr,'FingerBundle')]
                    for i1 in ("TX","TY","TZ","RX","RY","RZ"):
                        cmds.addAttr(fingerBundle_con,ln=f"{name}{i1}",at="double",dv=0)

                        if(i1=="RX" or i1=="RZ"):
                            if(number==1):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",1,k=True)
                            else:
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",0,k=True)
                        elif(i1=="RY"):
                            if(number==1):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",1,k=True)
                            elif(number==2):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",1.1,k=True)
                            elif(number==3):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",0.9,k=True)

                        if(i1=="TX"):
                            if(number!=1 or finger=="Middle"):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",0,k=True)
                            elif(finger=="Thumb"):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",10,k=True)
                            elif(finger=="Index"):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",5,k=True)
                            elif(finger=="Ring"):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",5,k=True)
                            elif(finger=="Little"):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",10,k=True)

                        if(i1=="TZ"):
                            if(number!=1 or finger=="Middle"):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",0,k=True)
                            elif(finger=="Thumb"):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",-10,k=True)
                            elif(finger=="Index"):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",-10,k=True)
                            elif(finger=="Ring"):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",5,k=True)
                            elif(finger=="Little"):
                                cmds.setAttr(f"{fingerBundle_con}.{name}{i1}",10,k=True)

                    #T(translate系)・R(rotate系)それぞれをmultiplyDivide1個にまとめ、.inputRotateへ複合接続する
                    for eulerToQuatNode,channel,axes in ((eulerToQuatT,"translate",("TX","TY","TZ")),
                                                          (eulerToQuatR,"rotate",("RX","RY","RZ"))):
                        multiplyDivide = cmds.createNode("multiplyDivide")
                        cmds.setAttr(f"{multiplyDivide}.operation",1)  #Multiply
                        cmds.connectAttr(f"{fingerBundle_con}.{channel}",f"{multiplyDivide}.input1")
                        for axis,input2_child in zip(axes,("input2X","input2Y","input2Z")):
                            cmds.connectAttr(f"{fingerBundle_con}.{name}{axis}",f"{multiplyDivide}.{input2_child}")
                        cmds.connectAttr(f"{multiplyDivide}.output",f"{eulerToQuatNode}.inputRotate")

        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.ThumbProximalTY",-5,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.IndexProximalTY",-10,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.MiddleProximalTY",5,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.RingProximalTY",15,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.LittleProximalTY",30,k=True)

        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.ThumbIntermediateTY",-1,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.IndexIntermediateTY",-1,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.MiddleIntermediateTY",-1,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.RingIntermediateTY",-1,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.LittleIntermediateTY",-1,k=True)
        
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.ThumbDistalTY",-2,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.IndexDistalTY",-2,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.MiddleDistalTY",-2,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.RingDistalTY",-2,k=True)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'FingerBundle')]}.LittleDistalTY",-2,k=True)

    return create_obj_dic

def clean_obj(character_name:str,obj_dic:dict):
    """
    リグ作成

    Parameters
    ----------
        dictionary obj_dic : 作成済みのオブジェクト

    Returns
    -------
        無し
    """
    setting = obj_dic[('Con','C','Setting')]
    root = obj_dic[('Con','C','Root1')]

    v_list=("BodyV","HeadV","LegV","LegLeftV","LegRightV","ArmV","ArmLeftV","ArmRightV","HandV","HandLeftV","HandRightV")
    for v in v_list:
        cmds.addAttr(setting,ln=v,at="bool")
        cmds.setAttr(f"{setting}.{v}",1,k=True,l=False)
    cmds.connectAttr(F"{setting}.BodyV",f"{obj_dic[('Grp','C','Body')]}.v")
    cmds.connectAttr(F"{setting}.HeadV",f"{obj_dic[('Grp','C','Heads')]}.v")
    cmds.connectAttr(F"{setting}.LegV",f"{obj_dic[('Grp','C','Leg')]}.v")
    cmds.connectAttr(F"{setting}.LegLeftV",f"{obj_dic[('Grp','L','Leg')]}.v")
    cmds.connectAttr(F"{setting}.LegRightV",f"{obj_dic[('Grp','R','Leg')]}.v")
    cmds.connectAttr(F"{setting}.ArmV",f"{obj_dic[('Grp','C','Arm')]}.v")
    cmds.connectAttr(F"{setting}.ArmLeftV",f"{obj_dic[('Grp','L','Arm')]}.v")
    cmds.connectAttr(F"{setting}.ArmRightV",f"{obj_dic[('Grp','R','Arm')]}.v")
    cmds.connectAttr(F"{setting}.HandV",f"{obj_dic[('Grp','C','Hand')]}.v")
    cmds.connectAttr(F"{setting}.HandLeftV",f"{obj_dic[('Grp','L','Hand')]}.v")
    cmds.connectAttr(F"{setting}.HandRightV",f"{obj_dic[('Grp','R','Hand')]}.v")

    #元からあるアトリビュート取得
    temp = cmds.group(em=True, name='null')
    temp_atter_list = cmds.listAttr(temp)
    cmds.delete(temp)
    
    for obj in obj_dic:
        attr_list=cmds.listAttr(obj_dic[obj])

        #初期値保存
        if obj[0]=='Con':
            for attr in attr_list:
                if(attr not in temp_atter_list and cmds.getAttr(f"{obj_dic[obj]}.{attr}", keyable=True)):
                    data_type=cmds.getAttr(F"{obj_dic[obj]}.{attr}",typ=True)
                    print(data_type)
                    if(data_type == "double"):
                        data=cmds.getAttr(F"{obj_dic[obj]}.{attr}")
                        cmds.addAttr(obj_dic[obj],ln=f"{attr}_Default",at="double",dv=data)
                        cmds.setAttr(F"{obj_dic[obj]}.{attr}_Default",k=False)
                    if(data_type == "float"):
                        data=cmds.getAttr(F"{obj_dic[obj]}.{attr}")
                        cmds.addAttr(obj_dic[obj],ln=f"{attr}_Default",at="float",dv=data)
                        cmds.setAttr(F"{obj_dic[obj]}.{attr}_Default",k=False)
                    if(data_type == "enum"):
                        data=cmds.getAttr(F"{obj_dic[obj]}.{attr}")
                        cmds.addAttr(obj_dic[obj],ln=f"{attr}_Default",at="long",dv=data)
                        cmds.setAttr(F"{obj_dic[obj]}.{attr}_Default",k=False)

        #コントローラー以外ロック
        if obj[0]=='Grp' or obj[0]=='Drv' or obj[0]=='Dvn':
            cmds.setAttr(f"{obj_dic[obj]}.t",k=False,l=True,cb=True)
            cmds.setAttr(f"{obj_dic[obj]}.s",k=False,l=True,cb=True)
            cmds.setAttr(f"{obj_dic[obj]}.r",k=False,l=True,cb=True)
            cmds.setAttr(f"{obj_dic[obj]}.v",k=False,l=True,cb=True)
            for attr in attr_list:
                if(attr not in temp_atter_list and not cmds.getAttr(f"{obj_dic[obj]}.{attr}", lock=True)):
                    cmds.setAttr(F"{obj_dic[obj]}.{attr}",l=True)

    #全ノード再計算
    cmds.dgdirty(a=True)
    current_time = cmds.currentTime(q=True)
    cmds.currentTime(current_time, edit=True)

    #ピッカー用
    info_obj_name = "ARFH_information"
    info_obj = cmds.group(em=True,n=info_obj_name)
    cmds.setAttr(f"{info_obj}.t",k=False,l=True,cb=True)
    cmds.setAttr(f"{info_obj}.s",k=False,l=True,cb=True)
    cmds.setAttr(f"{info_obj}.r",k=False,l=True,cb=True)
    cmds.setAttr(f"{info_obj}.v",0,k=False,l=True,cb=True)

    cmds.addAttr(f"{info_obj}",ln="characterName",dt="string")
    cmds.setAttr(f"{info_obj}.characterName",character_name,typ="string")

    obj_dic_uuid={}
    for key in obj_dic:
        uuid=cmds.ls(obj_dic[key],uuid=True)[0]
        obj_dic_uuid[key]=uuid
    obj_dic_text = json.dumps({str(k): v for k, v in obj_dic_uuid.items()})

    cmds.addAttr(f"{info_obj}",ln=character_name,dt="string")
    cmds.setAttr(f"{info_obj}.{character_name}",obj_dic_text,typ="string")

    