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

    #Rootコントローラ作成
    obj_dic |= create_root(character_name,rig_grp)
    obj_dic |= create_body(character_name,rig_grp,obj_dic,joint_dic,orientation_dic)
    obj_dic |= create_head(character_name,rig_grp,obj_dic,joint_dic,orientation_dic)
    obj_dic |= create_arm(character_name,rig_grp,obj_dic,joint_dic,orientation_dic)
    obj_dic |= create_leg(character_name,rig_grp,obj_dic,joint_dic,orientation_dic,pos_dic)

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
    #Unityアトリビュート
    create_obj_dic = autorig_utility.create_controller("UnitySetting",root_obj,pos_CLR="C",con_shape="unity",con_color=[0.9,0.9,0.9],pos=(0,0,20),
                                                        con_pos_lock=(False,False,False),con_rot_lock=(False,False,False),con_scl_lock=(False,False,False),
                                                        create_drv=False,keyable_rotateOrder=False)
    cmds.addAttr(create_obj_dic[("Con","C","UnitySetting")],ln="UnitySupport",at="bool")
    cmds.addAttr(create_obj_dic[("Con","C","UnitySetting")],ln="HumanoidSupport",at="bool")
    cmds.setAttr(f"{create_obj_dic[('Con','C','UnitySetting')]}.UnitySupport",1,k=True)
    cmds.setAttr(f"{create_obj_dic[('Con','C','UnitySetting')]}.HumanoidSupport",1,k=True)
    cmds.addAttr(create_obj_dic[("Con","C","UnitySetting")],ln="Moveable",at="double",dv=False)
    cmds.addAttr(create_obj_dic[("Con","C","UnitySetting")],ln="Scalable",at="double",dv=False)
    #scalable,moveable用の計算
    floatMath01=cmds.shadingNode("floatMath",asUtility=True)
    cmds.setAttr(f"{floatMath01}.operation",2)
    cmds.connectAttr(f"{create_obj_dic[('Con','C','UnitySetting')]}.HumanoidSupport",f"{floatMath01}.floatA",f=True)
    cmds.connectAttr(f"{create_obj_dic[('Con','C','UnitySetting')]}.UnitySupport",f"{floatMath01}.floatB",f=True)
    floatMath02=cmds.shadingNode("floatMath",asUtility=True)
    cmds.setAttr(f"{floatMath02}.operation",2)
    cmds.setAttr(f"{floatMath02}.floatB",-1)
    cmds.connectAttr(f"{floatMath01}.outFloat",f"{floatMath02}.floatA",f=True)
    floatMath03=cmds.shadingNode("floatMath",asUtility=True)
    cmds.setAttr(f"{floatMath03}.floatB",1)
    cmds.connectAttr(f"{floatMath02}.outFloat",f"{floatMath03}.floatA",f=True)
    cmds.connectAttr(f"{floatMath03}.outFloat",f"{create_obj_dic[('Con','C','UnitySetting')]}.Moveable",f=True)
    floatMath04=cmds.shadingNode("floatMath",asUtility=True)
    cmds.setAttr(f"{floatMath04}.operation",2)
    cmds.setAttr(f"{floatMath04}.floatB",-1)
    cmds.connectAttr(f"{create_obj_dic[('Con','C','UnitySetting')]}.UnitySupport",f"{floatMath04}.floatA",f=True)
    floatMath05=cmds.shadingNode("floatMath",asUtility=True)
    cmds.setAttr(f"{floatMath05}.floatB",1)
    cmds.connectAttr(f"{floatMath05}.outFloat",f"{create_obj_dic[('Con','C','UnitySetting')]}.Scalable",f=True)
    cmds.connectAttr(f"{floatMath04}.outFloat",f"{floatMath05}.floatA",f=True)

    #Rootコントローラ
    create_obj_dic |= autorig_utility.create_controller("Root1",root_obj,pos_CLR="C",con_shape="scuare",con_color=[0.8,0.2,0.2],con_size=(40,40,40),uniform_scale=True,
                                                        scale_unable=True,unity_setting=create_obj_dic[("Con","C","UnitySetting")])
    create_obj_dic |= autorig_utility.create_controller("Root2",root_obj,pos_CLR="C",con_shape="scuare",con_color=[0.2,0.8,0.2],con_size=(36,36,36),uniform_scale=True,
                                                        scale_unable=True,unity_setting=create_obj_dic[("Con","C","UnitySetting")])
    create_obj_dic |= autorig_utility.create_controller("Root3",root_obj,pos_CLR="C",con_shape="scuare",con_color=[0.2,0.2,0.8],con_size=(32,32,32),uniform_scale=True,
                                                        scale_unable=True,unity_setting=create_obj_dic[("Con","C","UnitySetting")])
    #接続
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Root1')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','Root2')]}.offsetParentMatrix")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Root2')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','Root3')]}.offsetParentMatrix")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Root3')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','UnitySetting')]}.offsetParentMatrix")

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
    unity_setting = obj_dic[('Con','C','UnitySetting')]

    #親作成
    root_obj = cmds.group(em=True,n=f"Grp_C_Body",p=parent)
    cmds.setAttr( f"{root_obj}.t", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{root_obj}.r", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{root_obj}.s", lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f"{root_obj}.v",keyable=False,channelBox=True)

    #matrix取得
    hips_matrix = cmds.xform(orientation_dic["c_hips"],m=True,ws=True,q=True)
    spine_matrix = cmds.xform(orientation_dic["c_spine"],m=True,ws=True,q=True)
    chest_matrix = cmds.xform(orientation_dic["c_chest"],m=True,ws=True,q=True)
    if("c_upperChest" in orientation_dic):
        upperChest_matrix = cmds.xform(orientation_dic["c_upperChest"],m=True,ws=True,q=True)

    #腰親作成
    create_obj_dic |= autorig_utility.create_controller("Waist",root_obj,pos_CLR="C",con_color=(0.8,0.8,0.2),con_shape="arrorFour",con_size=(10,10,10),con_rotate=(0,0,90),
                                                        uniform_scale=True,unity_setting=unity_setting,scale_unable=True)
    cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','Waist')]}.offsetParentMatrix")
    cmds.xform(create_obj_dic[('Grp','C','Waist')],m=spine_matrix,ws=True)

    #尻コントローラー
    create_obj_dic |= autorig_utility.create_controller("Hips",root_obj,pos_CLR="C",con_color=(0.2,0.8,0.2),con_shape="cube",con_size=(7,13,13),con_position=(-4,0,0),
                                                        unity_setting=unity_setting,scale_unable=True,pos_unable=True)
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Waist')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','Hips')]}.offsetParentMatrix")

    #胴体FK
    #Spine
    create_obj_dic |= autorig_utility.create_controller("SpineFK",root_obj,pos_CLR="C",con_color=(0.2,0,1),con_shape="circle",con_size=(9,9,9),con_rotate=(0,0,90),
                                                        unity_setting=unity_setting,scale_unable=True,pos_unable=True)
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Waist')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','SpineFK')]}.offsetParentMatrix")
    cmds.xform(create_obj_dic[('Grp','C','SpineFK')],m=spine_matrix,ws=True)
    #ChestFK
    create_obj_dic |= autorig_utility.create_controller("ChestFK",root_obj,pos_CLR="C",con_color=(0.2,0,1),con_shape="circle",con_size=(9,9,9),con_rotate=(0,0,90),
                                                        unity_setting=unity_setting,scale_unable=True,pos_unable=True)
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','SpineFK')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','ChestFK')]}.offsetParentMatrix")
    cmds.xform(create_obj_dic[('Grp','C','ChestFK')],m=chest_matrix,ws=True)
    autorig_utility.layerd_scale_rotate(create_obj_dic[('Grp','C','SpineFK')],create_obj_dic[('Drv','C','SpineFK')],
                                create_obj_dic[('Grp','C','ChestFK')],create_obj_dic[('Con','C','ChestFK')])
    #UpperChestFK
    if("c_upperChestFK" in orientation_dic):
        create_obj_dic |= autorig_utility.create_controller("UpperChestFK",root_obj,pos_CLR="C",con_color=(0.2,0,1),con_shape="circle",con_size=(9,9,9),con_rotate=(0,0,90),
                                                            unity_setting=unity_setting,scale_unable=True,pos_unable=True)
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','ChestFK')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','UpperChestFK')]}.offsetParentMatrix")
        cmds.xform(create_obj_dic[('Grp','C','UpperChestFK')],m=upperChest_matrix,ws=True)
        autorig_utility.layerd_scale_rotate(create_obj_dic[('Grp','C','SpineFK')],create_obj_dic[('Drv','C','ChestFK')],
                                    create_obj_dic[('Grp','C','UpperChestFK')],create_obj_dic[('Con','C','UpperChestFK')])

    #IK
    if("c_upperChest" not in orientation_dic):
        create_obj_dic |= autorig_utility.create_controller("ChestIK",root_obj,pos_CLR="C",con_shape="cube",con_color=(0.2,0.8,0.2),con_size=(13,13,13),con_position=(8,0,0),
                                                            unity_setting=unity_setting,scale_unable=True)
        decomposeMatrix = cmds.createNode("decomposeMatrix")
        composeMatrix1 = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        composeMatrix2 = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{composeMatrix2}.useEulerRotation",0)
        multMatrix = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','ChestFK')]}.worldMatrix[0]",f"{decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(f"{decomposeMatrix}.outputShear",f"{composeMatrix1}.inputShear")
        cmds.connectAttr(f"{decomposeMatrix}.outputTranslate",f"{composeMatrix1}.inputTranslate")
        cmds.connectAttr(f"{decomposeMatrix}.outputScale",f"{composeMatrix2}.inputScale")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{create_obj_dic[('Grp','C','ChestIK')]}.offsetParentMatrix",f=True)
        cmds.connectAttr(f"{create_obj_dic[('Con','C','ChestIK')]}.inverseMatrix",f"{multMatrix}.matrixIn[0]")
        cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix}.matrixIn[1]")
        cmds.connectAttr(f"{create_obj_dic[('Con','C','ChestIK')]}.matrix",f"{multMatrix}.matrixIn[2]")
        cmds.connectAttr(f"{multMatrix}.matrixSum",f"{create_obj_dic[('Con','C','ChestIK')]}.offsetParentMatrix",f=True)
        cmds.xform(create_obj_dic[('Grp','C','ChestIK')],m=chest_matrix,ws=True)

        create_obj_dic |= autorig_utility.create_controller("SpineIK",root_obj,pos_CLR="C",con_shape="fatCross",con_color=(0.2,0.8,0.2),con_size=(4,4,4),con_rotate=(0,0,90),
                                                            unity_setting=unity_setting,scale_unable=True,pos_unable=True,rot_unable=(False,True,True))
        #ノード作成
        decomposeMatrix=cmds.createNode("decomposeMatrix")
        composeMatrix1=cmds.createNode("composeMatrix")
        composeMatrix2=cmds.createNode("composeMatrix")
        composeMatrix3=cmds.createNode("composeMatrix")
        composeMatrix4=cmds.createNode("composeMatrix")
        multMatrix1=cmds.createNode("multMatrix")
        multMatrix2=cmds.createNode("multMatrix")
        aimMatrix=cmds.createNode("aimMatrix")
        eulerToQuat=cmds.createNode("eulerToQuat")
        dotProduct=cmds.createNode("dotProduct")
        quatSlerp=cmds.createNode("quatSlerp")
        #アトリビュート作成
        cmds.addAttr(f"{create_obj_dic[('Con','C','SpineIK')]}",ln="FollowTwist",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con','C','SpineIK')]}.FollowTwist",0.4,k=True)
        cmds.connectAttr(f"{create_obj_dic[('Con','C','SpineIK')]}.FollowTwist",f"{quatSlerp}.inputT",f=True)
        cmds.addAttr(f"{create_obj_dic[('Con','C','SpineIK')]}",ln="FollowStretch",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con','C','SpineIK')]}.FollowStretch",0.3,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con','C','ChestIK')]}",ln="StretchIK",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con','C','ChestIK')]}.StretchIK",1,k=True)
        #計算
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.setAttr(f"{composeMatrix2}.useEulerRotation",0)
        cmds.setAttr(f"{composeMatrix3}.useEulerRotation",0)
        cmds.setAttr(f"{composeMatrix4}.useEulerRotation",0)
        cmds.setAttr(f"{composeMatrix2}.inputTranslateY",1)
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','SpineFK')]}.worldMatrix[0]",f"{decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(f"{decomposeMatrix}.outputTranslate",f"{composeMatrix1}.inputTranslate")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{aimMatrix}.inputMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','ChestIK')]}.worldMatrix[0]",f"{aimMatrix}.primaryTargetMatrix")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{aimMatrix}.secondaryTargetMatrix")
        cmds.connectAttr(f"{aimMatrix}.outputMatrix",f"{create_obj_dic[('Grp','C','SpineIK')]}.offsetParentMatrix")
        cmds.setAttr(f"{aimMatrix}.secondaryMode",1)
        cmds.setAttr(f"{composeMatrix2}.inputTranslateY",1)
        cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(f"{composeMatrix4}.outputMatrix",f"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','SpineFK')]}.worldMatrix[0]",f"{multMatrix1}.matrixIn[2]")
        cmds.connectAttr(f"{decomposeMatrix}.outputScale",f"{composeMatrix3}.inputScale")
        cmds.connectAttr(f"{create_obj_dic[('Con','C','SpineIK')]}.inverseMatrix",f"{multMatrix2}.matrixIn[0]")
        cmds.connectAttr(f"{composeMatrix3}.outputMatrix",f"{multMatrix2}.matrixIn[1]")
        cmds.connectAttr(f"{create_obj_dic[('Con','C','SpineIK')]}.matrix",f"{multMatrix2}.matrixIn[2]")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{create_obj_dic[('Con','C','SpineIK')]}.offsetParentMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Con','C','ChestIK')]}.rotate",f"{eulerToQuat}.inputRotate")
        cmds.connectAttr(f"{create_obj_dic[('Con','C','ChestIK')]}.rotateOrder",f"{eulerToQuat}.inputRotateOrder")
        cmds.connectAttr(f"{eulerToQuat}.outputQuatX",f"{dotProduct}.input1X")
        cmds.connectAttr(f"{eulerToQuat}.outputQuatY",f"{dotProduct}.input1Y")
        cmds.connectAttr(f"{eulerToQuat}.outputQuatZ",f"{dotProduct}.input1Z")
        cmds.setAttr(f"{dotProduct}.input2X",1)
        cmds.connectAttr(f"{quatSlerp}.outputQuat",f"{composeMatrix4}.inputQuat")
        cmds.connectAttr(f"{dotProduct}.output",f"{quatSlerp}.input2QuatX")
        cmds.connectAttr(f"{eulerToQuat}.outputQuatW",f"{quatSlerp}.input2QuatW")

        #接続
        autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','Hips')]}",joint_dic["c_hips"])
        autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','ChestIK')]}",joint_dic["c_chest"])
        autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','SpineIK')]}",joint_dic["c_spine"])

        #後半
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        decomposeMatrix3 = cmds.createNode("decomposeMatrix")
        composeMatrix1 = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        composeMatrix2 = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{composeMatrix2}.useEulerRotation",0)
        colorMath1 = cmds.createNode("colorMath")
        cmds.setAttr(f"{colorMath1}.operation",1)
        colorMath2 = cmds.createNode("colorMath")
        cmds.setAttr(f"{colorMath2}.operation",2)
        colorMath3 = cmds.createNode("colorMath")
        length1 = cmds.createNode("length")
        floatMath1 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath1}.operation",3)
        floatMath2 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath2}.operation",2)
        floatMath3 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath3}.floatB",-1)
        cmds.setAttr(f"{floatMath3}.operation",2)
        floatMath4 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath4}.floatB",1)
        floatMath5 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath5}.operation",3)
        floatMath6 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath6}.floatB",-1)
        floatMath7 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath7}.operation",2)
        floatMath8 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath8}.operation",2)
        floatMath9 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath9}.operation",2)
        floatMath10 = cmds.createNode("floatMath")
        cmds.setAttr(f"{floatMath10}.floatB",1)
        blendColors1 = cmds.createNode("blendColors")
        multMatrix1 = cmds.createNode("multMatrix")
        multMatrix2 = cmds.createNode("multMatrix")
        multMatrix3 = cmds.createNode("multMatrix")
        inverseMatrix1 = cmds.createNode("inverseMatrix")
        distanceBetween1 = cmds.createNode("distanceBetween")
        distanceBetween2 = cmds.createNode("distanceBetween")
        #接続
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','ChestIK')]}.worldMatrix[0]",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','SpineIK')]}.worldMatrix[0]",f"{decomposeMatrix2}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{colorMath1}.colorA")
        cmds.connectAttr(f"{decomposeMatrix2}.outputTranslate",f"{colorMath1}.colorB")
        cmds.connectAttr(f"{colorMath1}.outColor",f"{length1}.input")
        cmds.connectAttr(f"{length1}.output",f"{floatMath1}.floatB")
        cmds.connectAttr(f"{distanceBetween2}.distance",f"{floatMath1}.floatA")
        cmds.connectAttr(f"{floatMath1}.outFloat",f"{colorMath2}.colorBR")
        cmds.connectAttr(f"{floatMath1}.outFloat",f"{colorMath2}.colorBG")
        cmds.connectAttr(f"{floatMath1}.outFloat",f"{colorMath2}.colorBB")
        cmds.connectAttr(f"{colorMath1}.outColor",f"{colorMath2}.colorA")
        cmds.connectAttr(f"{colorMath2}.outColor",f"{colorMath3}.colorA")
        cmds.connectAttr(f"{decomposeMatrix2}.outputTranslate",f"{colorMath3}.colorB")
        cmds.connectAttr(f"{colorMath3}.outColor",f"{blendColors1}.color1")
        cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{blendColors1}.color2")
        cmds.connectAttr(f"{floatMath4}.outFloat",f"{blendColors1}.blender")
        cmds.connectAttr(f"{blendColors1}.output",f"{composeMatrix1}.inputTranslate")
        cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(f"{decomposeMatrix1}.outputShear",f"{composeMatrix1}.inputShear")
        cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{composeMatrix1}.inputScale")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(f"{joint_dic['c_chest']}.parentInverseMatrix",f"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(f"{joint_dic['c_chest']}.WorldBindMatrix",f"{multMatrix2}.matrixIn[0]")
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','ChestIK')]}.WorldBindMatrix",f"{inverseMatrix1}.inputMatrix")
        cmds.connectAttr(f"{inverseMatrix1}.outputMatrix",f"{multMatrix2}.matrixIn[1]")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{multMatrix2}.matrixIn[2]")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{decomposeMatrix3}.inputMatrix")
        cmds.connectAttr(f"{joint_dic['c_chest']}.rotateOrder",f"{decomposeMatrix3}.inputRotateOrder")
        cmds.connectAttr(f"{decomposeMatrix3}.outputTranslate",f"{joint_dic['c_chest']}.t",f=True)
        cmds.connectAttr(f"{decomposeMatrix3}.outputRotate",f"{joint_dic['c_chest']}.r",f=True)
        cmds.connectAttr(f"{decomposeMatrix3}.outputScale",f"{joint_dic['c_chest']}.s",f=True)
        cmds.connectAttr(f"{decomposeMatrix3}.outputShear",f"{joint_dic['c_chest']}.shear",f=True)
        cmds.connectAttr(f"{create_obj_dic[('Con','C','ChestIK')]}.StretchIK",f"{floatMath2}.floatB")
        cmds.connectAttr(f"{obj_dic[('Con','C','UnitySetting')]}.Scalable",f"{floatMath2}.floatA")
        cmds.connectAttr(f"{floatMath2}.outFloat",f"{floatMath3}.floatA")
        cmds.connectAttr(f"{floatMath3}.outFloat",f"{floatMath4}.floatA")
        cmds.connectAttr(f"{aimMatrix}.outputMatrix",f"{distanceBetween1}.inMatrix1")
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','ChestIK')]}.worldMatrix[0]",f"{distanceBetween1}.inMatrix2")
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','SpineIK')]}.WorldBindMatrix",f"{distanceBetween2}.inMatrix1")
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','ChestIK')]}.WorldBindMatrix",f"{distanceBetween2}.inMatrix2")
        cmds.connectAttr(f"{distanceBetween1}.distance",f"{floatMath5}.floatA")
        cmds.connectAttr(f"{distanceBetween2}.distance",f"{floatMath5}.floatB")
        cmds.connectAttr(f"{floatMath5}.outFloat",f"{floatMath6}.floatA")
        cmds.connectAttr(f"{floatMath6}.outFloat",f"{floatMath7}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con','C','ChestIK')]}.StretchIK",f"{floatMath7}.floatB")
        cmds.connectAttr(f"{floatMath7}.outFloat",f"{floatMath8}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con','C','SpineIK')]}.FollowStretch",f"{floatMath8}.floatB")
        cmds.connectAttr(f"{floatMath8}.outFloat",f"{floatMath9}.floatA")
        cmds.connectAttr(f"{obj_dic[('Con','C','UnitySetting')]}.Scalable",f"{floatMath9}.floatB")
        cmds.connectAttr(f"{floatMath9}.outFloat",f"{floatMath10}.floatA")
        cmds.connectAttr(f"{floatMath10}.outFloat",f"{composeMatrix2}.inputScaleX")
        cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix3}.matrixIn[0]")
        cmds.connectAttr(f"{aimMatrix}.outputMatrix",f"{multMatrix3}.matrixIn[1]")
        cmds.connectAttr(f"{multMatrix3}.matrixSum",f"{create_obj_dic[('Grp','C','SpineIK')]}.offsetParentMatrix",f=True)


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
    unity_setting = obj_dic[('Con','C','UnitySetting')]

    #親作成
    root_obj = cmds.group(em=True,n=f"Grp_C_Heads",p=parent)
    cmds.setAttr( f"{root_obj}.t", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{root_obj}.r", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{root_obj}.s", lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f"{root_obj}.v",keyable=False,channelBox=True)

    #matrix取得
    neck_matrix = cmds.xform(orientation_dic["c_neck"],m=True,ws=True,q=True)
    head_matrix = cmds.xform(orientation_dic["c_head"],m=True,ws=True,q=True)
    if("l_eye" in orientation_dic):
        eye_l_matrix = cmds.xform(orientation_dic["l_eye"],m=True,ws=True,q=True)
    if("r_eye" in orientation_dic):
        eye_r_matrix = cmds.xform(orientation_dic["r_eye"],m=True,ws=True,q=True)

    #Neck
    create_obj_dic |= autorig_utility.create_controller("Neck",root_obj,pos_CLR="C",con_color=(0.2,0,1),con_shape="circle",con_size=(3,3,3),con_rotate=(0,0,90),
                                                        unity_setting=unity_setting,scale_unable=True,pos_unable=True)
    cmds.setAttr(f"{create_obj_dic[('Grp','C','Neck')]}.offsetParentMatrix",*cmds.xform(joint_dic["c_chest"],q=True,ws=True,m=True),typ="matrix")
    cmds.xform(create_obj_dic[('Grp','C','Neck')],m=neck_matrix,ws=True)
    autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','Neck')]}",joint_dic["c_neck"])
    #アトリビュート作成
    cmds.addAttr(create_obj_dic[('Con','C','Neck')],ln="LayeredRotate",at="double",min=0,max=1,dv=0)
    cmds.setAttr(f"{create_obj_dic[('Con','C','Neck')]}.LayeredRotate",0,k=True)
    decomposeMatrix1 = cmds.createNode("decomposeMatrix")
    decomposeMatrix2 = cmds.createNode("decomposeMatrix")
    decomposeMatrix3 = cmds.createNode("decomposeMatrix")
    decomposeMatrix4 = cmds.createNode("decomposeMatrix")
    decomposeMatrix5 = cmds.createNode("decomposeMatrix")
    composeMatrix1 = cmds.createNode("composeMatrix")
    cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
    multMatrix1 = cmds.createNode("multMatrix")
    multMatrix2 = cmds.createNode("multMatrix")
    quatProd1 = cmds.createNode("quatProd")
    quatProd2 = cmds.createNode("quatProd")
    quatSlerp = cmds.createNode("quatSlerp")
    cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{quatProd1}.input1Quat")
    cmds.connectAttr(f"{decomposeMatrix2}.outputQuat",f"{quatProd1}.input2Quat")
    cmds.connectAttr(f"{create_obj_dic[('Grp','C','Neck')]}.matrix",f"{decomposeMatrix1}.inputMatrix")
    cmds.connectAttr(f"{joint_dic['c_chest']}.worldMatrix[0]",f"{decomposeMatrix2}.inputMatrix")
    cmds.connectAttr(f"{create_obj_dic[('Grp','C','Neck')]}.matrix",f"{multMatrix1}.matrixIn[0]")
    cmds.connectAttr(f"{joint_dic['c_chest']}.worldMatrix[0]",f"{multMatrix1}.matrixIn[1]")
    cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{decomposeMatrix3}.inputMatrix")
    cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix[0]",f"{decomposeMatrix4}.inputMatrix")
    cmds.connectAttr(f"{quatProd1}.outputQuat",f"{quatSlerp}.input2Quat")
    cmds.connectAttr(f"{create_obj_dic[('Con','C','Neck')]}.LayeredRotate",f"{quatSlerp}.inputT")
    cmds.connectAttr(f"{quatSlerp}.outputQuat",f"{composeMatrix1}.inputQuat")
    cmds.connectAttr(f"{create_obj_dic[('Grp','C','Neck')]}.inverseMatrix",f"{multMatrix2}.matrixIn[0]")
    cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix2}.matrixIn[1]")
    cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{create_obj_dic[('Grp','C','Neck')]}.offsetParentMatrix")
    cmds.connectAttr(f"{decomposeMatrix3}.outputTranslate",f"{composeMatrix1}.inputTranslate")
    cmds.connectAttr(f"{decomposeMatrix4}.outputScale",f"{composeMatrix1}.inputScale")
    cmds.connectAttr(f"{decomposeMatrix4}.outputShear",f"{composeMatrix1}.inputShear")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Neck')]}.WorldBindMatrix",f"{decomposeMatrix5}.inputMatrix")
    cmds.connectAttr(f"{decomposeMatrix5}.outputQuat",f"{quatProd2}.input1Quat")
    cmds.connectAttr(f"{decomposeMatrix4}.outputQuat",f"{quatProd2}.input2Quat")
    cmds.connectAttr(f"{quatProd2}.outputQuat",f"{quatSlerp}.input1Quat")

    #Head
    create_obj_dic |= autorig_utility.create_controller("Head",root_obj,pos_CLR="C",con_color=(0.2,0,1),con_shape="circle",con_size=(8,8,8),con_position=(15,0,0),con_rotate=(0,0,90),
                                                        unity_setting=unity_setting,scale_unable=True,pos_unable=True)
    cmds.setAttr(f"{create_obj_dic[('Grp','C','Head')]}.offsetParentMatrix",*cmds.xform(joint_dic["c_neck"],q=True,ws=True,m=True),typ="matrix")
    cmds.xform(create_obj_dic[('Grp','C','Head')],m=head_matrix,ws=True)
    autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','Head')]}",joint_dic["c_head"])
    #アトリビュート作成
    cmds.addAttr(create_obj_dic[('Con','C','Head')],ln="LayeredRotate",at="double",min=0,max=1,dv=0)
    cmds.setAttr(f"{create_obj_dic[('Con','C','Head')]}.LayeredRotate",0,k=True)
    decomposeMatrix1 = cmds.createNode("decomposeMatrix")
    decomposeMatrix2 = cmds.createNode("decomposeMatrix")
    decomposeMatrix3 = cmds.createNode("decomposeMatrix")
    decomposeMatrix4 = cmds.createNode("decomposeMatrix")
    decomposeMatrix5 = cmds.createNode("decomposeMatrix")
    composeMatrix1 = cmds.createNode("composeMatrix")
    cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
    multMatrix1 = cmds.createNode("multMatrix")
    multMatrix2 = cmds.createNode("multMatrix")
    quatProd1 = cmds.createNode("quatProd")
    quatProd2 = cmds.createNode("quatProd")
    quatSlerp = cmds.createNode("quatSlerp")
    cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{quatProd1}.input1Quat")
    cmds.connectAttr(f"{decomposeMatrix2}.outputQuat",f"{quatProd1}.input2Quat")
    cmds.connectAttr(f"{create_obj_dic[('Grp','C','Head')]}.matrix",f"{decomposeMatrix1}.inputMatrix")
    cmds.connectAttr(f"{joint_dic['c_neck']}.worldMatrix[0]",f"{decomposeMatrix2}.inputMatrix")
    cmds.connectAttr(f"{create_obj_dic[('Grp','C','Head')]}.matrix",f"{multMatrix1}.matrixIn[0]")
    cmds.connectAttr(f"{joint_dic['c_neck']}.worldMatrix[0]",f"{multMatrix1}.matrixIn[1]")
    cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{decomposeMatrix3}.inputMatrix")
    cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix[0]",f"{decomposeMatrix4}.inputMatrix")
    cmds.connectAttr(f"{quatProd1}.outputQuat",f"{quatSlerp}.input2Quat")
    cmds.connectAttr(f"{create_obj_dic[('Con','C','Head')]}.LayeredRotate",f"{quatSlerp}.inputT")
    cmds.connectAttr(f"{quatSlerp}.outputQuat",f"{composeMatrix1}.inputQuat")
    cmds.connectAttr(f"{create_obj_dic[('Grp','C','Head')]}.inverseMatrix",f"{multMatrix2}.matrixIn[0]")
    cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix2}.matrixIn[1]")
    cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{create_obj_dic[('Grp','C','Head')]}.offsetParentMatrix")
    cmds.connectAttr(f"{decomposeMatrix3}.outputTranslate",f"{composeMatrix1}.inputTranslate")
    cmds.connectAttr(f"{decomposeMatrix4}.outputScale",f"{composeMatrix1}.inputScale")
    cmds.connectAttr(f"{decomposeMatrix4}.outputShear",f"{composeMatrix1}.inputShear")
    cmds.connectAttr(f"{create_obj_dic[('Drv','C','Head')]}.WorldBindMatrix",f"{decomposeMatrix5}.inputMatrix")
    cmds.connectAttr(f"{decomposeMatrix5}.outputQuat",f"{quatProd2}.input1Quat")
    cmds.connectAttr(f"{decomposeMatrix4}.outputQuat",f"{quatProd2}.input2Quat")
    cmds.connectAttr(f"{quatProd2}.outputQuat",f"{quatSlerp}.input1Quat")

    if("l_eye" in orientation_dic and "r_eye" in orientation_dic):
        eye_c_pos = [(v*0.5) + (cmds.xform(orientation_dic["r_eye"],t=True,ws=True,q=True)[n] * 0.5) for n,v in enumerate(cmds.xform(orientation_dic["l_eye"],t=True,ws=True,q=True))]
        eye_c_pos[2]+=eye_c_pos[1]/2
        create_obj_dic |= autorig_utility.create_controller("EyeAim",root_obj,pos_CLR="C",con_color=(0.6,0.6,0),con_shape="scuare",con_size=(3,3,6),con_position=(0,0,0),con_rotate=(90,0,90),
                                                            unity_setting=unity_setting,uniform_scale=True)

        translate_vector = OpenMaya.MVector(eye_c_pos[0],eye_c_pos[1],eye_c_pos[2])
        cmds.addAttr(create_obj_dic[('Drv','C','EyeAim')],ln="WorldBindMatrix",at="matrix")
        cmds.setAttr(f"{create_obj_dic[('Drv','C','EyeAim')]}.WorldBindMatrix",*[1,0,0,0,0,1,0,0,0,0,1,0,translate_vector[0],translate_vector[1],translate_vector[2],1],typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Drv','C','EyeAim')]}.WorldBindMatrix",lock=True, keyable=False)
        cmds.addAttr(create_obj_dic[('Con','C','EyeAim')],ln="LayeredTranslate",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con','C','EyeAim')]}.LayeredTranslate",1,k=True)
        cmds.addAttr(create_obj_dic[('Con','C','EyeAim')],ln="LayeredRotate",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con','C','EyeAim')]}.LayeredRotate",1,k=True)
        cmds.addAttr(create_obj_dic[('Con','C','EyeAim')],ln="LayeredScale",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con','C','EyeAim')]}.LayeredScale",1,k=True)

        multMatrix1 = cmds.createNode("multMatrix")
        multMatrix2 = cmds.createNode("multMatrix")
        multMatrix3 = cmds.createNode("multMatrix")
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        decomposeMatrix3 = cmds.createNode("decomposeMatrix")
        decomposeMatrix4 = cmds.createNode("decomposeMatrix")
        composeMatrix1 = cmds.createNode("composeMatrix")
        composeMatrix2 = cmds.createNode("composeMatrix")
        pairBlend1 = cmds.createNode("pairBlend")
        pairBlend2 = cmds.createNode("pairBlend")
        quatSlerp1 = cmds.createNode("quatSlerp")
        quatSlerp2 = cmds.createNode("quatSlerp")
        inverseMatrix1 = cmds.createNode("inverseMatrix")
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.setAttr(f"{composeMatrix2}.useEulerRotation",0)

        cmds.connectAttr(f"{create_obj_dic[('Drv','C','Head')]}.WorldBindMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','Head')]}.worldMatrix",f"{decomposeMatrix2}.inputMatrix")
        cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix",f"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','Head')]}.WorldBindMatrix",f"{inverseMatrix1}.inputMatrix")
        cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix",f"{decomposeMatrix4}.inputMatrix")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','EyeAim')]}.WorldBindMatrix",f"{multMatrix3}.matrixIn[0]")
        cmds.connectAttr(f"{inverseMatrix1}.outputMatrix",f"{multMatrix3}.matrixIn[1]")
        cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{quatSlerp1}.input1Quat")
        cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{pairBlend1}.inRotate1")
        cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{pairBlend1}.inTranslate1")
        cmds.connectAttr(f"{decomposeMatrix2}.outputQuat",f"{quatSlerp1}.input2Quat")
        cmds.connectAttr(f"{decomposeMatrix2}.outputScale",f"{pairBlend1}.inRotate2")
        cmds.connectAttr(f"{decomposeMatrix2}.outputShear",f"{composeMatrix1}.inputShear")
        cmds.connectAttr(f"{decomposeMatrix2}.outputTranslate",f"{pairBlend1}.inTranslate2")
        cmds.connectAttr(f"{create_obj_dic[('Con','C','EyeAim')]}.LayeredTranslate",f"{quatSlerp1}.inputT")
        cmds.connectAttr(f"{create_obj_dic[('Con','C','EyeAim')]}.LayeredTranslate",f"{pairBlend1}.weight")
        cmds.connectAttr(f"{quatSlerp1}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(f"{pairBlend1}.outRotate",f"{composeMatrix1}.inputScale")
        cmds.connectAttr(f"{pairBlend1}.outTranslate",f"{composeMatrix1}.inputTranslate")
        cmds.connectAttr(f"{multMatrix3}.matrixSum",f"{multMatrix2}.matrixIn[0]")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix2}.matrixIn[1]")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{decomposeMatrix3}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix4}.outputQuat",f"{quatSlerp2}.input1Quat")
        cmds.connectAttr(f"{decomposeMatrix4}.outputScale",f"{pairBlend2}.inRotate1")
        cmds.connectAttr(f"{decomposeMatrix4}.outputShear",f"{pairBlend2}.inTranslate1")
        cmds.connectAttr(f"{decomposeMatrix3}.outputQuat",f"{quatSlerp2}.input2Quat")
        cmds.connectAttr(f"{create_obj_dic[('Con','C','EyeAim')]}.LayeredRotate",f"{quatSlerp2}.inputT")
        cmds.connectAttr(f"{decomposeMatrix3}.outputScale",f"{pairBlend2}.inRotate2")
        cmds.connectAttr(f"{decomposeMatrix3}.outputShear",f"{pairBlend2}.inTranslate2")
        cmds.connectAttr(f"{decomposeMatrix3}.outputTranslate",f"{composeMatrix2}.inputTranslate")
        cmds.connectAttr(f"{pairBlend2}.outRotate",f"{composeMatrix2}.inputScale")
        cmds.connectAttr(f"{pairBlend2}.outTranslate",f"{composeMatrix2}.inputShear")
        cmds.connectAttr(f"{quatSlerp2}.outputQuat",f"{composeMatrix2}.inputQuat")
        cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{create_obj_dic[('Grp','C','EyeAim')]}.offsetParentMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Con','C','EyeAim')]}.LayeredScale",f"{pairBlend2}.weight")

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
            create_obj_dic |= autorig_utility.create_controller("EyeAim",root_obj,pos_CLR=i,con_color=(0.6,0.6,0),con_shape="circle",con_size=(2,2,2),con_rotate=(90,0,90),
                                                                unity_setting=unity_setting,con_scl_lock=(False,False,False))
            cmds.connectAttr(f"{create_obj_dic[('Drv','C','EyeAim')]}.worldMatrix",f"{create_obj_dic[('Grp',i,'EyeAim')]}.offsetParentMatrix")
            matrix = OpenMaya.MMatrix(move_matrix)*OpenMaya.MMatrix(lr[i])
            cmds.xform(create_obj_dic[('Grp',i,'EyeAim')],m=list(matrix),ws=True)
            cmds.setAttr(f"{create_obj_dic[('Grp',i,'EyeAim')]}.r",*(0,0,0),typ="double3")
            cmds.setAttr(f"{create_obj_dic[('Grp',i,'EyeAim')]}.s",*(scl,1,1),typ="double3")

            aim_target = cmds.group(em=True, name=f"Grp_{i}_EyeAimTarget", parent=root_obj)
            cmds.connectAttr(f"{create_obj_dic[('Drv','C','Head')]}.worldMatrix",f"{aim_target}.offsetParentMatrix")
            cmds.xform(aim_target,m=lr[i],ws=True)

            create_obj_dic |= autorig_utility.create_controller("Eye",root_obj,pos_CLR=i,con_color=(0.2,0,1),con_shape="circle",con_size=(2,2,2),con_rotate=(90,90,0),
                                                                unity_setting=unity_setting,scale_unable=True,pos_unable=True)
            
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

            cmds.setAttr(f"{create_obj_dic[('Drv',i,'Eye')]}.sz",scl)
            
            autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv',i,'Eye')]}",joint_dic[f"{i.lower()}_eye"])

            

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
    unity_setting = obj_dic[('Con','C','UnitySetting')]

    #親作成
    root_center_obj = cmds.group(em=True,n=f"Grp_C_Arm",p=parent)
    cmds.setAttr( f"{root_center_obj}.t", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{root_center_obj}.r", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{root_center_obj}.s", lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f"{root_center_obj}.v",keyable=False,channelBox=True)

    hips_joint_matrix = cmds.xform(joint_dic["c_hips"],m=True,ws=True,q=True)
    spine_joint_matrix = cmds.xform(joint_dic["c_spine"],m=True,ws=True,q=True)
    chest_joint_matrix = cmds.xform(joint_dic["c_chest"],m=True,ws=True,q=True)
    head_joint_matrix = cmds.xform(joint_dic["c_head"],m=True,ws=True,q=True)

    #左右繰り返し
    for clr in ("L","R"):
        clr_lower = clr.lower()
        root_obj = cmds.group(em=True,n=f"Grp_{clr}_Arm",p=root_center_obj)

        #matrix取得
        upperArm_matrix = cmds.xform(orientation_dic[f"{clr_lower}_upperArm"],m=True,ws=True,q=True)
        lowerArm_matrix = cmds.xform(orientation_dic[f"{clr_lower}_lowerArm"],m=True,ws=True,q=True)
        shoulder_matrix = cmds.xform(orientation_dic[f"{clr_lower}_shoulder"],m=True,ws=True,q=True)
        hand_matrix = cmds.xform(orientation_dic[f"{clr_lower}_hand"],m=True,ws=True,q=True)

        #Shoulder
        create_obj_dic |= autorig_utility.create_controller("Shoulder",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0.2),con_shape="cube",con_size=(3,3,3),con_rotate=(0,0,0),
                                                            unity_setting=unity_setting,scale_unable=True,pos_unable=True)
        cmds.connectAttr(f"{joint_dic['c_chest']}.worldMatrix[0]",f"{create_obj_dic[('Grp',clr,'Shoulder')]}.offsetParentMatrix")
        cmds.xform(create_obj_dic[('Grp',clr,'Shoulder')],m=shoulder_matrix,ws=True)
        if(clr=="R"):
            cmds.setAttr(F"{create_obj_dic[('Grp',clr,'Shoulder')]}.sy",-1)
            cmds.setAttr(F"{create_obj_dic[('Drv',clr,'Shoulder')]}.sz",-1)
        autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv',clr,'Shoulder')]}",joint_dic[f"{clr_lower}_shoulder"])

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

        jointOrient = cmds.getAttr(f"{upperArm_ik}.jointOrient")[0]
        cmds.setAttr(f"{upperArm_ik}.preferredAngleX",jointOrient[0])
        cmds.setAttr(f"{upperArm_ik}.preferredAngleY",jointOrient[1])
        cmds.setAttr(f"{upperArm_ik}.preferredAngleZ",jointOrient[2])
        cmds.setAttr(f"{upperArm_ik}.jointOrient",*(0,0,0),typ="double3")
        cmds.setAttr(f"{upperArm_ik}.r",*jointOrient,typ="double3")

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

        #FKUpper
        create_obj_dic |= autorig_utility.create_controller("UpperArmFK",root_obj,pos_CLR=clr,con_color=(0.2,0,1),con_shape="circle",con_size=(3,3,3),con_rotate=(90,90,0),con_position=(9,0,0),
                                                            unity_setting=unity_setting,scale_unable=True,pos_unable=True)
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'Shoulder')]}.worldMatrix[0]",F"{create_obj_dic[('Grp',clr,'UpperArmFK')]}.offsetParentMatrix")
        cmds.xform(create_obj_dic[('Grp',clr,'UpperArmFK')],m=upperArm_matrix,ws=True)
        autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv',clr,'UpperArmFK')]}",upperArm_fk)

        cmds.addAttr(create_obj_dic[('Con',clr,'UpperArmFK')],ln="LayeredScale",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'UpperArmFK')]}.LayeredScale",0,k=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'UpperArmFK')],ln="LayeredRotate",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'UpperArmFK')]}.LayeredRotate",1,k=True)

        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        decomposeMatrix3 = cmds.createNode("decomposeMatrix")
        decomposeMatrix4 = cmds.createNode("decomposeMatrix")
        decomposeMatrix5 = cmds.createNode("decomposeMatrix")
        multMatrix1 = cmds.createNode("multMatrix")
        multMatrix2 = cmds.createNode("multMatrix")
        multMatrix3 = cmds.createNode("multMatrix")
        composeMatrix1 = cmds.createNode("composeMatrix")
        composeMatrix2 = cmds.createNode("composeMatrix")
        blendColor1 = cmds.createNode("blendColors")
        quatSlerp1 = cmds.createNode("quatSlerp")
        quatProd1 = cmds.createNode("quatProd")
        quatProd2 = cmds.createNode("quatProd")
        quatProd3 = cmds.createNode("quatProd")
        quatInvert1 = cmds.createNode("quatInvert")
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.setAttr(f"{composeMatrix2}.useEulerRotation",0)

        if(clr=="R"):
            cmds.setAttr(F"{create_obj_dic[('Drv',clr,'UpperArmFK')]}.sy",-1)
            composeMatrix3 = cmds.createNode("composeMatrix")
            cmds.setAttr(F"{composeMatrix3}.inputScaleY",-1)
            cmds.connectAttr(f"{composeMatrix3}.outputMatrix",f"{multMatrix3}.matrixIn[0]")
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,'UpperArmFK')]}.inverseMatrix",f"{multMatrix3}.matrixIn[1]")
            cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix3}.matrixIn[2]")
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,'UpperArmFK')]}.matrix",f"{multMatrix3}.matrixIn[3]")
        else:
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,'UpperArmFK')]}.inverseMatrix",f"{multMatrix3}.matrixIn[0]")
            cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix3}.matrixIn[1]")
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,'UpperArmFK')]}.matrix",f"{multMatrix3}.matrixIn[2]")
        cmds.connectAttr(f"{multMatrix3}.matrixSum",f"{create_obj_dic[('Con',clr,'UpperArmFK')]}.offsetParentMatrix")

        cmds.connectAttr(F"{multMatrix2}.matrixSum",F"{create_obj_dic[('Grp',clr,'UpperArmFK')]}.offsetParentMatrix",f=True)
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'Shoulder')]}.worldMatrix",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(F"{create_obj_dic[('Grp',clr,'UpperArmFK')]}.matrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'Shoulder')]}.worldMatrix",f"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'Shoulder')]}.WorldBindMatrix",f"{decomposeMatrix2}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix2}.outputQuat",f"{quatInvert1}.inputQuat")
        cmds.connectAttr(f"{quatInvert1}.outputQuat",f"{quatProd1}.input1Quat")
        cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{quatProd1}.input2Quat")
        cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{blendColor1}.color1")
        cmds.connectAttr(f"{decomposeMatrix4}.outputScale",f"{blendColor1}.color2")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'UpperArmFK')]}.LayeredScale",f"{blendColor1}.blender")
        cmds.connectAttr(f"{quatProd1}.outputQuat",f"{quatProd2}.input2Quat")
        cmds.connectAttr(f"{decomposeMatrix3}.outputQuat",f"{quatProd2}.input1Quat")
        cmds.connectAttr(f"{decomposeMatrix3}.outputQuat",f"{quatProd3}.input1Quat")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'UpperArmFK')]}.WorldBindMatrix",f"{decomposeMatrix3}.inputMatrix")
        cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix",f"{decomposeMatrix4}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix4}.outputQuat",f"{quatProd3}.input2Quat")
        cmds.connectAttr(f"{quatProd3}.outputQuat",f"{quatSlerp1}.input1Quat")
        cmds.connectAttr(f"{quatProd2}.outputQuat",f"{quatSlerp1}.input2Quat")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'UpperArmFK')]}.LayeredRotate",f"{quatSlerp1}.inputT")
        cmds.connectAttr(f"{blendColor1}.output",f"{composeMatrix2}.inputScale")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{decomposeMatrix5}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix5}.outputTranslate",f"{composeMatrix1}.inputTranslate")
        cmds.connectAttr(f"{quatSlerp1}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'UpperArmFK')]}.inverseMatrix",f"{multMatrix2}.matrixIn[0]")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix2}.matrixIn[1]")

        #FKLower
        create_obj_dic |= autorig_utility.create_controller("LowerArmFK",root_obj,pos_CLR=clr,con_color=(0.2,0,1),con_shape="circle",con_size=(3,3,3),con_rotate=(90,90,0),con_position=(9,0,0),
                                                            unity_setting=unity_setting,scale_unable=True,pos_unable=True)
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'UpperArmFK')]}.worldMatrix[0]",F"{create_obj_dic[('Grp',clr,'LowerArmFK')]}.offsetParentMatrix")
        cmds.xform(create_obj_dic[('Grp',clr,'LowerArmFK')],m=lowerArm_matrix,ws=True)
        autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv',clr,'LowerArmFK')]}",lowerArm_fk)

        cmds.addAttr(create_obj_dic[('Con',clr,'LowerArmFK')],ln="LayeredScale",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LowerArmFK')]}.LayeredScale",0,k=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LowerArmFK')],ln="LayeredRotate",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LowerArmFK')]}.LayeredRotate",1,k=True)

        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        decomposeMatrix3 = cmds.createNode("decomposeMatrix")
        decomposeMatrix4 = cmds.createNode("decomposeMatrix")
        decomposeMatrix5 = cmds.createNode("decomposeMatrix")
        multMatrix1 = cmds.createNode("multMatrix")
        multMatrix2 = cmds.createNode("multMatrix")
        multMatrix3 = cmds.createNode("multMatrix")
        composeMatrix1 = cmds.createNode("composeMatrix")
        composeMatrix2 = cmds.createNode("composeMatrix")
        blendColor1 = cmds.createNode("blendColors")
        quatSlerp1 = cmds.createNode("quatSlerp")
        quatProd1 = cmds.createNode("quatProd")
        quatProd2 = cmds.createNode("quatProd")
        quatProd3 = cmds.createNode("quatProd")
        quatInvert1 = cmds.createNode("quatInvert")
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.setAttr(f"{composeMatrix2}.useEulerRotation",0)

        if(clr=="R"):
            cmds.setAttr(F"{create_obj_dic[('Drv',clr,'LowerArmFK')]}.sy",-1)
            composeMatrix3 = cmds.createNode("composeMatrix")
            cmds.setAttr(F"{composeMatrix3}.inputScaleY",-1)
            cmds.connectAttr(f"{composeMatrix3}.outputMatrix",f"{multMatrix3}.matrixIn[0]")
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LowerArmFK')]}.inverseMatrix",f"{multMatrix3}.matrixIn[1]")
            cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix3}.matrixIn[2]")
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LowerArmFK')]}.matrix",f"{multMatrix3}.matrixIn[3]")
        else:
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LowerArmFK')]}.inverseMatrix",f"{multMatrix3}.matrixIn[0]")
            cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix3}.matrixIn[1]")
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LowerArmFK')]}.matrix",f"{multMatrix3}.matrixIn[2]")

        cmds.connectAttr(F"{multMatrix2}.matrixSum",F"{create_obj_dic[('Grp',clr,'LowerArmFK')]}.offsetParentMatrix",f=True)
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'UpperArmFK')]}.worldMatrix",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(F"{create_obj_dic[('Grp',clr,'LowerArmFK')]}.matrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'UpperArmFK')]}.worldMatrix",f"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'UpperArmFK')]}.WorldBindMatrix",f"{decomposeMatrix2}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix2}.outputQuat",f"{quatInvert1}.inputQuat")
        cmds.connectAttr(f"{quatInvert1}.outputQuat",f"{quatProd1}.input1Quat")
        cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{quatProd1}.input2Quat")
        cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{blendColor1}.color1")
        cmds.connectAttr(f"{decomposeMatrix4}.outputScale",f"{blendColor1}.color2")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LowerArmFK')]}.LayeredScale",f"{blendColor1}.blender")
        cmds.connectAttr(f"{quatProd1}.outputQuat",f"{quatProd2}.input2Quat")
        cmds.connectAttr(f"{decomposeMatrix3}.outputQuat",f"{quatProd2}.input1Quat")
        cmds.connectAttr(f"{decomposeMatrix3}.outputQuat",f"{quatProd3}.input1Quat")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'LowerArmFK')]}.WorldBindMatrix",f"{decomposeMatrix3}.inputMatrix")
        cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix",f"{decomposeMatrix4}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix4}.outputQuat",f"{quatProd3}.input2Quat")
        cmds.connectAttr(f"{quatProd3}.outputQuat",f"{quatSlerp1}.input1Quat")
        cmds.connectAttr(f"{quatProd2}.outputQuat",f"{quatSlerp1}.input2Quat")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LowerArmFK')]}.LayeredRotate",f"{quatSlerp1}.inputT")
        cmds.connectAttr(f"{blendColor1}.output",f"{composeMatrix2}.inputScale")
        cmds.connectAttr(f"{multMatrix3}.matrixSum",f"{create_obj_dic[('Con',clr,'LowerArmFK')]}.offsetParentMatrix")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{decomposeMatrix5}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix5}.outputTranslate",f"{composeMatrix1}.inputTranslate")
        cmds.connectAttr(f"{quatSlerp1}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'LowerArmFK')]}.inverseMatrix",f"{multMatrix2}.matrixIn[0]")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix2}.matrixIn[1]")

        #IK
        create_obj_dic |= autorig_utility.create_controller("HandIK",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0),con_shape="hexagon1",con_size=(5,5,5),con_rotate=(90,90,0),
                                                            unity_setting=unity_setting,con_rot_lock=(False,False,False),uniform_scale=True)
        shoulder_joint_matrix = cmds.xform(joint_dic[f"{clr_lower}_shoulder"],m=True,ws=True,q=True)
        upperArm_joint_matrix = cmds.xform(joint_dic[f"{clr_lower}_upperArm"],m=True,ws=True,q=True)
        lowerArm_joint_matrix = cmds.xform(joint_dic[f"{clr_lower}_lowerArm"],m=True,ws=True,q=True)

        if(clr=="R"):
            cmds.setAttr(F"{create_obj_dic[('Con',clr,'HandIK')]}.offsetParentMatrix",*(1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1),typ="matrix")
            cmds.setAttr(F"{create_obj_dic[('Drv',clr,'HandIK')]}.offsetParentMatrix",*(1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1),typ="matrix")

        cmds.addAttr(create_obj_dic[('Con',clr,'HandIK')],ln="parent",at="enum",en="Root:Shoulder:Hips:Spine:Chest:Head:",k=True)
        blendMatrix = cmds.createNode("blendMatrix")
        cmds.connectAttr(f"{blendMatrix}.outputMatrix",f"{create_obj_dic[('Grp',clr,'HandIK')]}.offsetParentMatrix")
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
        cmds.setAttr(f"{upperArm_ik_dummy}.jointOrient",*(0,0,0),typ="double3")
        cmds.setAttr(f"{upperArm_ik_dummy}.r",*(0,0,0),typ="double3")
        cmds.setAttr(f"{lowerArm_ik_dummy}.segmentScaleCompensate",1)

        autorig_utility.matrix_constraint(upperArm_ik_dummy,upperArm_ik)
        autorig_utility.matrix_constraint(lowerArm_ik_dummy,lowerArm_ik)
        autorig_utility.matrix_constraint(hand_ik_dummy,hand_ik)
        
        #IKHandle作成
        ikHandle = cmds.ikHandle(sj=upperArm_ik_dummy,ee=hand_ik_dummy)[0]
        ikHandle = cmds.parent(ikHandle,f"{create_obj_dic[('Drv',clr,'HandIK')]}")[0]
        cmds.setAttr(f"{ikHandle}.v",0,l=True)
        cmds.setAttr(f"{ikHandle}.t",*(0,0,0),typ="double3",l=True)
        cmds.setAttr(f"{ikHandle}.r",*(0,0,0),typ="double3",l=True)
        cmds.setAttr(f"{ikHandle}.s",*(1,1,1),typ="double3",l=True)

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


        create_obj_dic |= autorig_utility.create_controller("ArmPV",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0),con_shape="dia1",con_size=(2,2,2),con_position=[pv_pos[i]-(pos[i]+upperArm_pos[i]) for i in range(3)],
                                                            unity_setting=unity_setting,con_scl_lock=(False,False,False))
        
        cmds.connectAttr(F"{composeMatrix1}.outputMatrix",f"{create_obj_dic[('Grp',clr,'ArmPV')]}.offsetParentMatrix")
        cmds.xform(f"{create_obj_dic[('Grp',clr,'ArmPV')]}",t=[pos[i]+upperArm_pos[i] for i in range(3) ],ws=True)
        cmds.xform(f"{create_obj_dic[('Drv',clr,'ArmPV')]}",t=pv_pos,ws=True)
        if(clr=="R"):
            cmds.setAttr(F"{create_obj_dic[('Grp',clr,'ArmPV')]}.sx",-1)
        cmds.poleVectorConstraint(create_obj_dic[('Drv',clr,'ArmPV')],ikHandle)

        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="twist",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.twist",0,k=True)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.twist",f"{ikHandle}.twist")

        #IKスケーリング
        cmds.addAttr(ik_parent,ln="HandMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(hand_matrix)*OpenMaya.MMatrix(cmds.xform(ik_parent,q=True,ws=True,m=True)).inverse()
        cmds.setAttr(F"{ik_parent}.HandMatrix",*list(matrix),typ="matrix",lock=True, keyable=False)

        cmds.addAttr(ik_parent,ln="LowerArmMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(lowerArm_matrix)*OpenMaya.MMatrix(cmds.xform(ik_parent,q=True,ws=True,m=True)).inverse()
        cmds.setAttr(F"{ik_parent}.LowerArmMatrix",*list(matrix),typ="matrix",lock=True, keyable=False)
        
        #アトリビュート作成
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="stretch",at="float",max=1,min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.stretch",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="addUpperArmStretch",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.addUpperArmStretch",0,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="addLowerArmStretch",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.addLowerArmStretch",0,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="addArmStretch",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.addArmStretch",0,k=True)

        #計算
        multMatrix1 = cmds.createNode("multMatrix")
        multMatrix2 = cmds.createNode("multMatrix")
        distanceBetween1 = cmds.createNode("distanceBetween")
        distanceBetween2 = cmds.createNode("distanceBetween")
        distanceBetween3 = cmds.createNode("distanceBetween")
        blendColors1 = cmds.createNode("blendColors")
        blendColors2 = cmds.createNode("blendColors")
        condition1 = cmds.createNode("condition")
        condition2 = cmds.createNode("condition")
        condition3 = cmds.createNode("condition")
        floatMath1 = cmds.createNode("floatMath")
        floatMath2 = cmds.createNode("floatMath")
        floatMath3 = cmds.createNode("floatMath")
        floatMath4 = cmds.createNode("floatMath")
        floatMath5 = cmds.createNode("floatMath")
        floatMath6 = cmds.createNode("floatMath")
        floatMath7 = cmds.createNode("floatMath")
        floatMath8 = cmds.createNode("floatMath")

        cmds.setAttr(f"{floatMath2}.operation",2)
        cmds.setAttr(f"{floatMath3}.operation",3)
        cmds.setAttr(f"{floatMath4}.operation",2)
        cmds.setAttr(f"{condition1}.operation",2)
        cmds.setAttr(f"{condition2}.operation",0)
        cmds.setAttr(f"{condition3}.operation",0)
        cmds.setAttr(f"{condition2}.secondTerm",1)
        cmds.setAttr(f"{condition3}.secondTerm",1)
        cmds.setAttr(f"{condition2}.colorIfFalseR",1)
        cmds.setAttr(f"{condition2}.colorIfFalseG",1)
        cmds.setAttr(f"{condition2}.colorIfFalseB",1)
        cmds.setAttr(f"{condition3}.colorIfFalseR",1)
        cmds.setAttr(f"{condition3}.colorIfFalseG",1)
        cmds.setAttr(f"{condition3}.colorIfFalseB",1)

        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'ArmIK')]}.HandMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'ArmIK')]}.LowerArmMatrix",f"{multMatrix2}.matrixIn[0]")
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'ArmIK')]}.worldMatrix",f"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'ArmIK')]}.worldMatrix",f"{multMatrix2}.matrixIn[1]")
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'ArmIK')]}.worldMatrix",f"{distanceBetween2}.inMatrix1")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{distanceBetween2}.inMatrix2")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{distanceBetween1}.inMatrix2")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{distanceBetween1}.inMatrix1")
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'ArmIK')]}.worldMatrix",f"{distanceBetween3}.inMatrix2")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'HandIK')]}.worldMatrix",f"{distanceBetween3}.inMatrix1")
        cmds.connectAttr(f"{distanceBetween1}.distance",f"{floatMath1}.floatA")
        cmds.connectAttr(f"{distanceBetween2}.distance",f"{floatMath1}.floatB")
        cmds.connectAttr(f"{floatMath1}.outFloat",f"{floatMath2}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.sx",f"{floatMath2}.floatB")
        cmds.connectAttr(f"{distanceBetween3}.distance",f"{floatMath3}.floatA")
        cmds.connectAttr(f"{floatMath2}.outFloat",f"{floatMath3}.floatB")
        cmds.connectAttr(f"{floatMath3}.outFloat",f"{floatMath4}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.sx",f"{floatMath4}.floatB")
        cmds.connectAttr(f"{distanceBetween3}.distance",f"{condition1}.firstTerm")
        cmds.connectAttr(f"{floatMath2}.outFloat",f"{condition1}.secondTerm")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.sx",f"{condition1}.colorIfFalseR")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.sx",f"{condition1}.colorIfFalseG")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.sx",f"{condition1}.colorIfFalseB")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.sx",f"{condition1}.colorIfTrueR")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.sx",f"{condition1}.colorIfTrueB")
        cmds.connectAttr(f"{floatMath4}.outFloat",f"{condition1}.colorIfTrueG")
        cmds.connectAttr(f"{condition1}.outColor",f"{blendColors1}.color1")
        cmds.connectAttr(f"{condition1}.colorIfFalse",f"{blendColors1}.color2")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.stretch",f"{blendColors1}.blender")
        cmds.connectAttr(f"{condition1}.outColor",f"{blendColors2}.color1")
        cmds.connectAttr(f"{condition1}.colorIfFalse",f"{blendColors2}.color2")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.stretch",f"{blendColors2}.blender")
        cmds.connectAttr(F"{blendColors1}.outputR",f"{condition2}.colorIfTrueR")
        cmds.connectAttr(F"{blendColors1}.outputB",f"{condition2}.colorIfTrueB")
        cmds.connectAttr(F"{blendColors2}.outputR",f"{condition3}.colorIfTrueR")
        cmds.connectAttr(F"{blendColors2}.outputB",f"{condition3}.colorIfTrueB")

        cmds.connectAttr(f"{blendColors1}.outputG",f"{floatMath5}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.addUpperArmStretch",f"{floatMath5}.floatB")
        cmds.connectAttr(F"{floatMath5}.outFloat",f"{floatMath6}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.addArmStretch",f"{floatMath6}.floatB")
        cmds.connectAttr(f"{floatMath6}.outFloat",f"{condition2}.colorIfTrueG")
        cmds.connectAttr(f"{obj_dic[('Con','C','UnitySetting')]}.Scalable",f"{condition2}.firstTerm")

        cmds.connectAttr(f"{blendColors2}.outputG",f"{floatMath7}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.addLowerArmStretch",f"{floatMath7}.floatB")
        cmds.connectAttr(F"{floatMath7}.outFloat",f"{floatMath8}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.addArmStretch",f"{floatMath8}.floatB")
        cmds.connectAttr(f"{floatMath8}.outFloat",f"{condition3}.colorIfTrueG")
        cmds.connectAttr(f"{obj_dic[('Con','C','UnitySetting')]}.Scalable",f"{condition3}.firstTerm")

        #方向特定
        x=[1,0,0,0,0,1,0,0,0,0,1,0,1,0,0,1]
        y=[1,0,0,0,0,1,0,0,0,0,1,0,0,1,0,1]
        z=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,1,1]
        #Lower
        lower_x_pos = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(x)*OpenMaya.MMatrix(lowerArm_joint_matrix)).translation(OpenMaya.MSpace.kWorld)
        lower_y_pos = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(y)*OpenMaya.MMatrix(lowerArm_joint_matrix)).translation(OpenMaya.MSpace.kWorld)
        lower_z_pos = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(z)*OpenMaya.MMatrix(lowerArm_joint_matrix)).translation(OpenMaya.MSpace.kWorld)
        lower_x_distance = [(lower_x_pos[i]-hand_pos[i])**2 for i in range(3)]
        lower_y_distance = [(lower_y_pos[i]-hand_pos[i])**2 for i in range(3)]
        lower_z_distance = [(lower_z_pos[i]-hand_pos[i])**2 for i in range(3)]
        if(lower_x_distance<lower_y_distance and lower_x_distance<lower_z_distance):
            cmds.connectAttr(f"{condition3}.outColorG",f"{lowerArm_ik_dummy}.sx")
            cmds.connectAttr(f"{condition3}.outColorR",f"{lowerArm_ik_dummy}.sy")
            cmds.connectAttr(f"{condition3}.outColorR",f"{lowerArm_ik_dummy}.sz")
        if(lower_y_distance<lower_x_distance and lower_y_distance<lower_z_distance):
            cmds.connectAttr(f"{condition3}.outColorR",f"{lowerArm_ik_dummy}.sx")
            cmds.connectAttr(f"{condition3}.outColorG",f"{lowerArm_ik_dummy}.sy")
            cmds.connectAttr(f"{condition3}.outColorR",f"{lowerArm_ik_dummy}.sz")
        if(lower_z_distance<lower_x_distance and lower_z_distance<lower_y_distance):
            cmds.connectAttr(f"{condition3}.outColorR",f"{lowerArm_ik_dummy}.sx")
            cmds.connectAttr(f"{condition3}.outColorR",f"{lowerArm_ik_dummy}.sy")
            cmds.connectAttr(f"{condition3}.outColorG",f"{lowerArm_ik_dummy}.sz")
        #Upper
        upper_x_pos = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(x)*OpenMaya.MMatrix(upperArm_joint_matrix)).translation(OpenMaya.MSpace.kWorld)
        upper_y_pos = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(y)*OpenMaya.MMatrix(upperArm_joint_matrix)).translation(OpenMaya.MSpace.kWorld)
        upper_z_pos = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(z)*OpenMaya.MMatrix(upperArm_joint_matrix)).translation(OpenMaya.MSpace.kWorld)
        upper_x_distance = [(upper_x_pos[i]-hand_pos[i])**2 for i in range(3)]
        upper_y_distance = [(upper_y_pos[i]-hand_pos[i])**2 for i in range(3)]
        upper_z_distance = [(upper_z_pos[i]-hand_pos[i])**2 for i in range(3)]
        if(upper_x_distance<upper_y_distance and upper_x_distance<upper_z_distance):
            cmds.connectAttr(f"{condition2}.outColorG",f"{upperArm_ik_dummy}.sx")
            cmds.connectAttr(f"{condition2}.outColorR",f"{upperArm_ik_dummy}.sy")
            cmds.connectAttr(f"{condition2}.outColorR",f"{upperArm_ik_dummy}.sz")
        if(upper_y_distance<upper_x_distance and upper_y_distance<upper_z_distance):
            cmds.connectAttr(f"{condition2}.outColorR",f"{upperArm_ik_dummy}.sx")
            cmds.connectAttr(f"{condition2}.outColorG",f"{upperArm_ik_dummy}.sy")
            cmds.connectAttr(f"{condition2}.outColorR",f"{upperArm_ik_dummy}.sz")
        if(upper_z_distance<upper_x_distance and upper_z_distance<upper_y_distance):
            cmds.connectAttr(f"{condition2}.outColorR",f"{upperArm_ik_dummy}.sx")
            cmds.connectAttr(f"{condition2}.outColorR",f"{upperArm_ik_dummy}.sy")
            cmds.connectAttr(f"{condition2}.outColorG",f"{upperArm_ik_dummy}.sz")

        cmds.setAttr(F"{ik_parent}.v",0,k=False,l=True)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'UpperArmFK')]}.v",l=False)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'LowerArmFK')]}.v",l=False)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'ArmPV')]}.v",l=False)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'HandIK')]}.v",l=False)

        floatMath1 = cmds.createNode("floatMath")
        floatMath2 = cmds.createNode("floatMath")
        cmds.setAttr(F"{floatMath1}.operation",2)
        cmds.setAttr(F"{floatMath1}.floatB",-1)
        cmds.setAttr(F"{floatMath2}.floatB",1)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'Shoulder')]}.IKFK",F"{create_obj_dic[('Grp',clr,'UpperArmFK')]}.v")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'Shoulder')]}.IKFK",F"{create_obj_dic[('Grp',clr,'LowerArmFK')]}.v")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'Shoulder')]}.IKFK",F"{floatMath1}.floatA")
        cmds.connectAttr(F"{floatMath1}.outFloat",F"{floatMath2}.floatA")
        cmds.connectAttr(f"{floatMath2}.outFloat",F"{create_obj_dic[('Grp',clr,'ArmPV')]}.v")
        cmds.connectAttr(f"{floatMath2}.outFloat",F"{create_obj_dic[('Grp',clr,'HandIK')]}.v")

        #SmoothIK
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="smoothIK",at="float",max=1,min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.smoothIK",0,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}",ln="smoothRange",at="float",min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'HandIK')]}.smoothRange",5,k=True)
        floatMath1 = cmds.createNode("floatMath")
        floatMath2 = cmds.createNode("floatMath")
        floatMath3 = cmds.createNode("floatMath")
        floatMath4 = cmds.createNode("floatMath")
        floatMath5 = cmds.createNode("floatMath")
        floatMath6 = cmds.createNode("floatMath")
        floatMath7 = cmds.createNode("floatMath")
        floatMath8 = cmds.createNode("floatMath")
        floatMath9 = cmds.createNode("floatMath")
        floatMath10 = cmds.createNode("floatMath")
        floatMath11 = cmds.createNode("floatMath")
        distanceBetween1 = cmds.createNode("distanceBetween")
        distanceBetween2 = cmds.createNode("distanceBetween")
        distanceBetween3 = cmds.createNode("distanceBetween")
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        composeMatrix1 = cmds.createNode("composeMatrix")
        composeMatrix2 = cmds.createNode("composeMatrix")
        aimMatrix1 = cmds.createNode("aimMatrix")
        multMatrix1 = cmds.createNode("multMatrix")
        condition1 = cmds.createNode("condition")
        condition2 = cmds.createNode("condition")
        absolute = cmds.createNode("absolute")
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.setAttr(f"{composeMatrix2}.useEulerRotation",0)
        cmds.setAttr(f"{floatMath1}.operation",2)
        cmds.setAttr(f"{floatMath2}.operation",2)
        cmds.setAttr(f"{floatMath3}.operation",2)
        cmds.setAttr(f"{floatMath4}.operation",1)
        cmds.setAttr(f"{floatMath5}.operation",3)
        cmds.setAttr(f"{floatMath6}.operation",2)
        cmds.setAttr(f"{floatMath7}.operation",0)
        cmds.setAttr(f"{floatMath8}.operation",2)
        cmds.setAttr(f"{floatMath9}.operation",2)
        cmds.setAttr(f"{floatMath10}.operation",2)
        cmds.setAttr(f"{condition1}.operation",2)
        cmds.setAttr(f"{condition2}.operation",2)
        cmds.setAttr(f"{condition1}.colorIfFalseR",0)
        cmds.setAttr(f"{floatMath6}.floatB",0.5)
        cmds.setAttr(f"{floatMath7}.floatB",0.5)
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'HandIK')]}.sx",f"{floatMath1}.floatA")
        cmds.connectAttr(F"{create_obj_dic[('Grp',clr,'ArmIK')]}.sx",f"{floatMath1}.floatB")
        cmds.connectAttr(F"{floatMath1}.outFloat",f"{floatMath2}.floatA")
        cmds.connectAttr(F"{floatMath1}.outFloat",f"{floatMath3}.floatA")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'HandIK')]}.smoothRange",f"{floatMath2}.floatB")
        cmds.connectAttr(F"{distanceBetween1}.distance",f"{floatMath11}.floatA")
        cmds.connectAttr(F"{distanceBetween3}.distance",f"{floatMath11}.floatB")
        cmds.connectAttr(F"{floatMath11}.outFloat",f"{floatMath3}.floatB")
        cmds.connectAttr(f"{hand_ik_dummy}.WorldBindMatrix",f"{distanceBetween1}.inMatrix1")
        cmds.connectAttr(f"{lowerArm_ik_dummy}.WorldBindMatrix",f"{distanceBetween1}.inMatrix2")
        cmds.connectAttr(f"{upperArm_ik_dummy}.WorldBindMatrix",f"{distanceBetween3}.inMatrix1")
        cmds.connectAttr(f"{lowerArm_ik_dummy}.WorldBindMatrix",f"{distanceBetween3}.inMatrix2")
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'ArmIK')]}.worldMatrix",f"{distanceBetween2}.inMatrix1")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'HandIK')]}.parentMatrix",f"{distanceBetween2}.inMatrix2")
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'ArmIK')]}.worldMatrix",f"{aimMatrix1}.primaryTargetMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'HandIK')]}.parentMatrix",f"{aimMatrix1}.inputMatrix")
        cmds.connectAttr(f"{aimMatrix1}.outputMatrix",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'HandIK')]}.parentInverseMatrix",f"{multMatrix1}.matrixIn[2]")
        cmds.connectAttr(F"{decomposeMatrix1}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(F"{decomposeMatrix1}.outputShear",f"{composeMatrix1}.inputShear")
        cmds.connectAttr(F"{decomposeMatrix1}.outputTranslate",f"{composeMatrix1}.inputTranslate")
        cmds.connectAttr(F"{multMatrix1}.matrixSum",f"{decomposeMatrix2}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix2}.outputTranslate",f"{create_obj_dic[('Drv',clr,'HandIK')]}.t")
        cmds.connectAttr(F"{floatMath3}.outFloat",f"{floatMath4}.floatB")
        cmds.connectAttr(F"{distanceBetween2}.distance",f"{floatMath4}.floatA")
        cmds.connectAttr(F"{floatMath2}.outFloat",f"{floatMath5}.floatB")
        cmds.connectAttr(F"{floatMath2}.outFloat",f"{floatMath9}.floatB")
        cmds.connectAttr(F"{floatMath2}.outFloat",F"{condition2}.secondTerm")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'HandIK')]}.smoothIK",f"{floatMath10}.floatB")
        cmds.connectAttr(F"{floatMath4}.outFloat",f"{floatMath5}.floatA")
        cmds.connectAttr(F"{floatMath4}.outFloat",f"{absolute}.input")
        cmds.connectAttr(F"{floatMath4}.outFloat",f"{condition1}.firstTerm")
        cmds.connectAttr(F"{floatMath4}.outFloat",f"{condition1}.colorIfTrueR")
        cmds.connectAttr(f"{absolute}.output",f"{condition2}.firstTerm")
        cmds.connectAttr(f"{condition1}.outColorR",f"{condition2}.colorIfTrueR")
        cmds.connectAttr(F"{floatMath10}.outFloat",f"{composeMatrix2}.inputTranslateX")
        cmds.connectAttr(F"{condition2}.outColorR",f"{floatMath10}.floatA")
        cmds.connectAttr(f"{floatMath9}.outFloat",f"{condition2}.colorIfFalseR")
        cmds.connectAttr(F"{floatMath5}.outFloat",f"{floatMath6}.floatA")
        cmds.connectAttr(F"{floatMath6}.outFloat",f"{floatMath7}.floatA")
        cmds.connectAttr(F"{floatMath7}.outFloat",f"{floatMath8}.floatA")
        cmds.connectAttr(F"{floatMath7}.outFloat",f"{floatMath8}.floatB")
        cmds.connectAttr(F"{floatMath8}.outFloat",f"{floatMath9}.floatA")


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
    unity_setting = obj_dic[('Con','C','UnitySetting')]

    #親作成
    root_center_obj = cmds.group(em=True,n=f"Grp_C_Leg",p=parent)
    cmds.setAttr( f"{root_center_obj}.t", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{root_center_obj}.r", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{root_center_obj}.s", lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f"{root_center_obj}.v",keyable=False,channelBox=True)

    hips_joint_matrix = cmds.xform(joint_dic["c_hips"],m=True,ws=True,q=True)

    #左右繰り返し
    for clr in ("L","R"):
        clr_lower = clr.lower()
        root_obj = cmds.group(em=True,n=f"Grp_{clr}_Leg",p=root_center_obj)

        #matrix取得
        upperLeg_matrix = cmds.xform(orientation_dic[f"{clr_lower}_upperLeg"],m=True,ws=True,q=True)
        lowerLeg_matrix = cmds.xform(orientation_dic[f"{clr_lower}_lowerLeg"],m=True,ws=True,q=True)
        foot_matrix = cmds.xform(orientation_dic[f"{clr_lower}_foot"],m=True,ws=True,q=True)
        toes_matrix = cmds.xform(orientation_dic[f"{clr_lower}_toes"],m=True,ws=True,q=True)

        #LegRoot
        create_obj_dic |= autorig_utility.create_controller("LegRoot",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0.2),con_shape="fatCross",con_size=(0.8,0.8,0.8),con_rotate=(90,0,0),con_position=(0,-4,0),
                                                            unity_setting=unity_setting,scale_unable=True,pos_unable=True,uniform_scale=True)
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        composeMatrix1 = cmds.createNode("composeMatrix")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{create_obj_dic[('Grp',clr,'LegRoot')]}.offsetParentMatrix")
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.connectAttr(F"{obj_dic[('Drv','C','Hips')]}.worldMatrix",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(F"{obj_dic[('Drv','C','Root3')]}.worldMatrix",f"{decomposeMatrix2}.inputMatrix")
        cmds.connectAttr(F"{decomposeMatrix1}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(F"{decomposeMatrix1}.outputTranslate",f"{composeMatrix1}.inputTranslate")
        cmds.connectAttr(F"{decomposeMatrix2}.outputScale",f"{composeMatrix1}.inputScale")
        cmds.connectAttr(F"{decomposeMatrix2}.outputShear",f"{composeMatrix1}.inputShear")
        cmds.xform(create_obj_dic[('Grp',clr,'LegRoot')],m=upperLeg_matrix,ws=True)
        multMatrix1 = cmds.createNode("multMatrix")
        multMatrix2 = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{create_obj_dic[('Grp',clr,'LegRoot')]}.offsetParentMatrix",f=True)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'LegRoot')]}.inverseMatrix",F"{multMatrix2}.matrixIn[0]")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",F"{multMatrix2}.matrixIn[1]")
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'LegRoot')]}.matrix",F"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(f"{obj_dic[('Drv','C','Hips')]}.worldMatrix",F"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(F"{multMatrix1}.matrixSum",f"{decomposeMatrix1}.inputMatrix",f=True)
        if(clr=="R"):
            cmds.setAttr(F"{create_obj_dic[('Con',clr,'LegRoot')]}.offsetParentMatrix",*(1,0,0,0,0,-1,0,0,0,0,1,0,0,0,0,1),typ="matrix")
            cmds.setAttr(F"{create_obj_dic[('Drv',clr,'LegRoot')]}.sy",-1)

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

        for i in (upperLeg_fk,lowerLeg_fk,foot_fk,toes_fk,upperLeg_ik,lowerLeg_ik,foot_ik,toes_ik):
            jointOrient = cmds.getAttr(f"{i}.jointOrient")[0]
            cmds.setAttr(f"{i}.preferredAngleX",jointOrient[0])
            cmds.setAttr(f"{i}.preferredAngleY",jointOrient[1])
            cmds.setAttr(f"{i}.preferredAngleZ",jointOrient[2])
            cmds.setAttr(f"{i}.jointOrient",*(0,0,0),typ="double3")
            cmds.setAttr(f"{i}.r",*jointOrient,typ="double3")

        #IKFK選択
        cmds.addAttr(create_obj_dic[('Con',clr,'LegRoot')],ln="IKFK",at="double",min=0,max=1,dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK",1,k=True)
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

        #FK制作
        decomposeMatrix_legRoot = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'LegRoot')]}.worldMatrix",f"{decomposeMatrix_legRoot}.inputMatrix")
        fk_list = ([upperLeg_matrix,"LegRoot"],[upperLeg_matrix,"UpperLegFK",upperLeg_fk],[lowerLeg_matrix,"LowerLegFK",lowerLeg_fk],[foot_matrix,"FootFK",foot_fk],[toes_matrix,"ToesFK",toes_fk])
        for i in range(4):
            create_obj_dic |= autorig_utility.create_controller(fk_list[i+1][1],root_obj,pos_CLR=clr,con_color=(0.2,0,1),con_shape="circle",con_size=(3,3,3),con_rotate=(90,90,0),con_position=(9,0,0),
                                                                unity_setting=unity_setting,scale_unable=True,pos_unable=True)
            cmds.connectAttr(F"{create_obj_dic[('Drv',clr,fk_list[i][1])]}.worldMatrix[0]",F"{create_obj_dic[('Grp',clr,fk_list[i+1][1])]}.offsetParentMatrix")
            cmds.xform(create_obj_dic[('Grp',clr,fk_list[i+1][1])],m=fk_list[i+1][0],ws=True)
            autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv',clr,fk_list[i+1][1])]}",fk_list[i+1][2])

            cmds.addAttr(create_obj_dic[('Con',clr,fk_list[i+1][1])],ln="LayeredScale",at="double",min=0,max=1,dv=0)
            cmds.setAttr(f"{create_obj_dic[('Con',clr,fk_list[i+1][1])]}.LayeredScale",0,k=True)
            cmds.addAttr(create_obj_dic[('Con',clr,fk_list[i+1][1])],ln="LayeredRotate",at="double",min=0,max=1,dv=0)
            cmds.setAttr(f"{create_obj_dic[('Con',clr,fk_list[i+1][1])]}.LayeredRotate",1,k=True)

            decomposeMatrix1 = cmds.createNode("decomposeMatrix")
            decomposeMatrix2 = cmds.createNode("decomposeMatrix")
            decomposeMatrix3 = cmds.createNode("decomposeMatrix")
            decomposeMatrix4 = cmds.createNode("decomposeMatrix")
            decomposeMatrix5 = cmds.createNode("decomposeMatrix")
            multMatrix1 = cmds.createNode("multMatrix")
            multMatrix2 = cmds.createNode("multMatrix")
            multMatrix3 = cmds.createNode("multMatrix")
            composeMatrix1 = cmds.createNode("composeMatrix")
            composeMatrix2 = cmds.createNode("composeMatrix")
            blendColor1 = cmds.createNode("blendColors")
            quatSlerp1 = cmds.createNode("quatSlerp")
            quatProd1 = cmds.createNode("quatProd")
            quatProd2 = cmds.createNode("quatProd")
            quatProd3 = cmds.createNode("quatProd")
            quatInvert1 = cmds.createNode("quatInvert")
            cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
            cmds.setAttr(f"{composeMatrix2}.useEulerRotation",0)

            if(clr=="R"):
                cmds.setAttr(F"{create_obj_dic[('Drv',clr,fk_list[i+1][1])]}.sy",-1)
                composeMatrix3 = cmds.createNode("composeMatrix")
                cmds.setAttr(F"{composeMatrix3}.inputScaleY",-1)
                cmds.connectAttr(f"{composeMatrix3}.outputMatrix",f"{multMatrix3}.matrixIn[0]")
                cmds.connectAttr(f"{create_obj_dic[('Con',clr,fk_list[i+1][1])]}.inverseMatrix",f"{multMatrix3}.matrixIn[1]")
                cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix3}.matrixIn[2]")
                cmds.connectAttr(f"{create_obj_dic[('Con',clr,fk_list[i+1][1])]}.matrix",f"{multMatrix3}.matrixIn[3]")
            else:
                cmds.connectAttr(f"{create_obj_dic[('Con',clr,fk_list[i+1][1])]}.inverseMatrix",f"{multMatrix3}.matrixIn[0]")
                cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix3}.matrixIn[1]")
                cmds.connectAttr(f"{create_obj_dic[('Con',clr,fk_list[i+1][1])]}.matrix",f"{multMatrix3}.matrixIn[2]")
            cmds.connectAttr(f"{multMatrix3}.matrixSum",f"{create_obj_dic[('Con',clr,fk_list[i+1][1])]}.offsetParentMatrix")

            cmds.connectAttr(F"{multMatrix2}.matrixSum",F"{create_obj_dic[('Grp',clr,fk_list[i+1][1])]}.offsetParentMatrix",f=True)
            cmds.connectAttr(F"{create_obj_dic[('Drv',clr,fk_list[i][1])]}.worldMatrix",f"{decomposeMatrix1}.inputMatrix")
            cmds.connectAttr(F"{create_obj_dic[('Grp',clr,fk_list[i+1][1])]}.matrix",f"{multMatrix1}.matrixIn[0]")
            cmds.connectAttr(F"{create_obj_dic[('Drv',clr,fk_list[i][1])]}.worldMatrix",f"{multMatrix1}.matrixIn[1]")
            cmds.connectAttr(F"{create_obj_dic[('Drv',clr,fk_list[i][1])]}.WorldBindMatrix",f"{decomposeMatrix2}.inputMatrix")
            cmds.connectAttr(f"{decomposeMatrix2}.outputQuat",f"{quatInvert1}.inputQuat")
            cmds.connectAttr(f"{quatInvert1}.outputQuat",f"{quatProd1}.input1Quat")
            cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{quatProd1}.input2Quat")
            cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{blendColor1}.color1")
            cmds.connectAttr(f"{decomposeMatrix_legRoot}.outputScale",f"{blendColor1}.color2")
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,fk_list[i+1][1])]}.LayeredScale",f"{blendColor1}.blender")
            cmds.connectAttr(f"{quatProd1}.outputQuat",f"{quatProd2}.input2Quat")
            cmds.connectAttr(f"{decomposeMatrix3}.outputQuat",f"{quatProd2}.input1Quat")
            cmds.connectAttr(f"{decomposeMatrix3}.outputQuat",f"{quatProd3}.input1Quat")
            cmds.connectAttr(f"{create_obj_dic[('Drv',clr,fk_list[i+1][1])]}.WorldBindMatrix",f"{decomposeMatrix3}.inputMatrix")
            cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix",f"{decomposeMatrix4}.inputMatrix")
            cmds.connectAttr(f"{decomposeMatrix4}.outputQuat",f"{quatProd3}.input2Quat")
            cmds.connectAttr(f"{quatProd3}.outputQuat",f"{quatSlerp1}.input1Quat")
            cmds.connectAttr(f"{quatProd2}.outputQuat",f"{quatSlerp1}.input2Quat")
            cmds.connectAttr(f"{create_obj_dic[('Con',clr,fk_list[i+1][1])]}.LayeredRotate",f"{quatSlerp1}.inputT")
            cmds.connectAttr(f"{blendColor1}.output",f"{composeMatrix2}.inputScale")
            cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{decomposeMatrix5}.inputMatrix")
            cmds.connectAttr(f"{decomposeMatrix5}.outputTranslate",f"{composeMatrix1}.inputTranslate")
            cmds.connectAttr(f"{quatSlerp1}.outputQuat",f"{composeMatrix1}.inputQuat")
            cmds.connectAttr(f"{create_obj_dic[('Grp',clr,fk_list[i+1][1])]}.inverseMatrix",f"{multMatrix2}.matrixIn[0]")
            cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix2}.matrixIn[1]")

        #IK用ダミー
        matrix = cmds.xform(upperLeg_fk,q=True,ws=True,m=True)
        ik_parent = cmds.group(em=True,n=f"Grp_{clr}_LegIk",p=root_obj)
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegRoot')]}.worldMatrix",f"{ik_parent}.offsetParentMatrix")
        cmds.xform(ik_parent,m=matrix,ws=True)

        upperLeg_ik_dummy = cmds.duplicate(upperLeg_ik,f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_upperLeg"],l=False)[0]+"_ik_dummy")[0]
        lowerLeg_ik_dummy = cmds.duplicate(lowerLeg_ik,f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_lowerLeg"],l=False)[0]+"_ik_dummy")[0]
        foot_ik_dummy = cmds.duplicate(foot_ik,f=True,po=True,n=cmds.ls(joint_dic[f"{clr_lower}_foot"],l=False)[0]+"_ik_dummy")[0]
        upperLeg_ik_dummy = cmds.parent(upperLeg_ik_dummy,ik_parent)[0]
        lowerLeg_ik_dummy = cmds.parent(lowerLeg_ik_dummy,upperLeg_ik_dummy)[0]
        foot_ik_dummy = cmds.parent(foot_ik_dummy,lowerLeg_ik_dummy)[0]
        cmds.setAttr(f"{upperLeg_ik_dummy}.jointOrient",*(0,0,0),typ="double3")
        cmds.setAttr(f"{upperLeg_ik_dummy}.r",*(0,0,0),typ="double3")
        cmds.setAttr(f"{lowerLeg_ik_dummy}.segmentScaleCompensate",1)

        autorig_utility.matrix_constraint(upperLeg_ik_dummy,upperLeg_ik)
        autorig_utility.matrix_constraint(lowerLeg_ik_dummy,lowerLeg_ik)
        autorig_utility.matrix_constraint(foot_ik_dummy,foot_ik)

        #IKコントローラー
        create_obj_dic |= autorig_utility.create_controller("LegIK",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0),con_shape="cube",con_size=(5,5,5),con_rotate=(90,90,0),
                                                            unity_setting=unity_setting,uniform_scale=True,scale_unable=True)
        hips_joint_matrix = cmds.xform(joint_dic[f"c_hips"],m=True,ws=True,q=True)

        legIK_matrix=[1,0,0,0,0,1,0,0,0,0,1,0]
        legIK_matrix.extend(list(OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(foot_matrix)).translation(OpenMaya.MSpace.kWorld)))
        legIK_matrix.append(1)

        if(clr=="R"):
            cmds.setAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.offsetParentMatrix",*(-1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1),typ="matrix")
            #cmds.setAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.sx",-1)

        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="parent",at="enum",en="Root:LegRoot",k=True)
        blendMatrix = cmds.createNode("blendMatrix")
        cmds.connectAttr(f"{blendMatrix}.outputMatrix",f"{create_obj_dic[('Grp',clr,'LegIK')]}.offsetParentMatrix")
        #Root
        cmds.addAttr(create_obj_dic[('Grp',clr,'LegIK')],ln="Root3Matrix",at="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'LegIK')]}.Root3Matrix",*legIK_matrix,typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'LegIK')]}.Root3Matrix",lock=True, keyable=False)
        root_decomposeMatrix = cmds.createNode("decomposeMatrix")
        root_multmatrix=cmds.createNode("multMatrix")
        root_condition=cmds.createNode("condition")
        cmds.setAttr(f"{root_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{root_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{root_condition}.secondTerm",0)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'LegIK')]}.Root3Matrix",f"{root_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix",f"{root_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{obj_dic[('Drv','C','Root3')]}.worldMatrix",f"{root_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.parent",f"{root_condition}.firstTerm")
        cmds.connectAttr(f"{root_multmatrix}.matrixSum",f"{blendMatrix}.target[0].targetMatrix")
        cmds.connectAttr(f"{root_condition}.outColorR",f"{blendMatrix}.target[0].weight")
        #LegRoot
        cmds.addAttr(create_obj_dic[('Grp',clr,'LegIK')],ln="LegRootMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(legIK_matrix)*OpenMaya.MMatrix(upperLeg_matrix).inverse()
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'LegIK')]}.LegRootMatrix",list(matrix),typ="matrix")
        cmds.setAttr(f"{create_obj_dic[('Grp',clr,'LegIK')]}.LegRootMatrix",lock=True, keyable=False)
        hips_decomposeMatrix = cmds.createNode("decomposeMatrix")
        hips_composeMatrix = cmds.createNode("composeMatrix")
        cmds.setAttr(f"{hips_composeMatrix}.useEulerRotation",0)
        hips_multmatrix=cmds.createNode("multMatrix")
        hips_condition=cmds.createNode("condition")
        cmds.setAttr(f"{hips_condition}.colorIfFalseR",0)
        cmds.setAttr(f"{hips_condition}.colorIfTrueR",1)
        cmds.setAttr(f"{hips_condition}.secondTerm",1)
        cmds.connectAttr(f"{create_obj_dic[('Grp',clr,'LegIK')]}.LegRootMatrix",f"{hips_multmatrix}.matrixIn[0]")
        cmds.connectAttr(f"{hips_composeMatrix}.outputMatrix",f"{hips_multmatrix}.matrixIn[1]")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'LegRoot')]}.worldMatrix",f"{hips_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{hips_decomposeMatrix}.outputQuat",f"{hips_composeMatrix}.inputQuat")
        cmds.connectAttr(f"{hips_decomposeMatrix}.outputTranslate",f"{hips_composeMatrix}.inputTranslate")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{hips_composeMatrix}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{hips_composeMatrix}.inputShear")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.parent",f"{hips_condition}.firstTerm")
        cmds.connectAttr(f"{hips_multmatrix}.matrixSum",f"{blendMatrix}.target[1].targetMatrix")
        cmds.connectAttr(f"{hips_condition}.outColorR",f"{blendMatrix}.target[1].weight")

        #先端回転
        toestip_matrix = cmds.xform(pos_dic[f"{clr_lower}_toestip"],m=True,ws=True,q=True)
        heel_matrix = cmds.xform(pos_dic[f"{clr_lower}_heel"],m=True,ws=True,q=True)
        footinside_matrix = cmds.xform(pos_dic[f"{clr_lower}_footinside"],m=True,ws=True,q=True)
        footoutside_matrix = cmds.xform(pos_dic[f"{clr_lower}_footoutside"],m=True,ws=True,q=True)
        #matrix
        cmds.addAttr(create_obj_dic[('Drv',clr,'LegIK')],ln="ToesTipMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(toestip_matrix)*OpenMaya.MMatrix(legIK_matrix).inverse()
        cmds.setAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.ToesTipMatrix",*matrix,typ="matrix",k=False,l=True)
        cmds.addAttr(create_obj_dic[('Drv',clr,'LegIK')],ln="HeelMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(heel_matrix)*OpenMaya.MMatrix(legIK_matrix).inverse()
        cmds.setAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.HeelMatrix",*matrix,typ="matrix",k=False,l=True)
        cmds.addAttr(create_obj_dic[('Drv',clr,'LegIK')],ln="FootInsideMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(footinside_matrix)*OpenMaya.MMatrix(legIK_matrix).inverse()
        cmds.setAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.FootInsideMatrix",*matrix,typ="matrix",k=False,l=True)
        cmds.addAttr(create_obj_dic[('Drv',clr,'LegIK')],ln="FootOutsideMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(footoutside_matrix)*OpenMaya.MMatrix(legIK_matrix).inverse()
        cmds.setAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.FootOutsideMatrix",*matrix,typ="matrix",k=False,l=True)
        #アトリビュート作成
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="ToeRoll",at="double",dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.ToeRoll",0,k=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="ToeRotate",at="double",dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.ToeRotate",0,k=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="HeelRoll",at="double",dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.HeelRoll",0,k=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="HeelRotate",at="double",dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.HeelRotate",0,k=True)
        cmds.addAttr(create_obj_dic[('Con',clr,'LegIK')],ln="Tilt",at="double",dv=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.Tilt",0,k=True)
        #計算
        composeMatrix1 = cmds.createNode("composeMatrix")
        composeMatrix2 = cmds.createNode("composeMatrix")
        composeMatrix3 = cmds.createNode("composeMatrix")
        composeMatrix4 = cmds.createNode("composeMatrix")
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        condition1 = cmds.createNode("condition")
        condition2 = cmds.createNode("condition")
        multMatrix1 = cmds.createNode("multMatrix")
        inverseMatrix1 = cmds.createNode("inverseMatrix")
        inverseMatrix2 = cmds.createNode("inverseMatrix")
        inverseMatrix3 = cmds.createNode("inverseMatrix")
        inverseMatrix4 = cmds.createNode("inverseMatrix")
        floatMath1 = cmds.createNode("floatMath")
        cmds.setAttr(F"{floatMath1}.operation",2)
        cmds.setAttr(F"{floatMath1}.floatB",-1)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.ToeRoll",f"{composeMatrix2}.inputRotateX")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.ToeRotate",f"{composeMatrix2}.inputRotateY")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.HeelRoll",f"{floatMath1}.floatA")
        cmds.connectAttr(f"{floatMath1}.outFloat",f"{composeMatrix1}.inputRotateX")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.HeelRotate",f"{composeMatrix1}.inputRotateY")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.Tilt",f"{condition1}.firstTerm")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.Tilt",f"{condition2}.firstTerm")
        cmds.setAttr(F"{condition1}.secondTerm",0)
        cmds.setAttr(F"{condition2}.secondTerm",0)
        cmds.setAttr(F"{condition1}.operation",4)
        cmds.setAttr(F"{condition2}.operation",2)
        cmds.setAttr(F"{condition1}.colorIfFalseR",0)
        cmds.setAttr(F"{condition2}.colorIfFalseR",0)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.Tilt",f"{condition1}.colorIfTrueR")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.Tilt",f"{condition2}.colorIfTrueR")
        cmds.connectAttr(f"{condition1}.outColorR",f"{composeMatrix3}.inputRotateZ")
        cmds.connectAttr(f"{condition2}.outColorR",f"{composeMatrix4}.inputRotateZ")
        cmds.connectAttr(F"{decomposeMatrix1}.outputRotate",f"{create_obj_dic[('Drv',clr,'LegIK')]}.r")
        cmds.connectAttr(F"{decomposeMatrix1}.outputTranslate",f"{create_obj_dic[('Drv',clr,'LegIK')]}.t")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'LegIK')]}.rotateOrder",f"{decomposeMatrix1}.inputRotateOrder")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.FootInsideMatrix",f"{inverseMatrix1}.inputMatrix")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.FootOutsideMatrix",f"{inverseMatrix2}.inputMatrix")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.HeelMatrix",f"{inverseMatrix3}.inputMatrix")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.ToesTipMatrix",f"{inverseMatrix4}.inputMatrix")
        #multMatrix
        #inside
        cmds.connectAttr(F"{inverseMatrix1}.outputMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(F"{composeMatrix4}.outputMatrix",f"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.FootInsideMatrix",f"{multMatrix1}.matrixIn[2]")
        #outside
        cmds.connectAttr(F"{inverseMatrix2}.outputMatrix",f"{multMatrix1}.matrixIn[3]")
        cmds.connectAttr(F"{composeMatrix3}.outputMatrix",f"{multMatrix1}.matrixIn[4]")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.FootOutsideMatrix",f"{multMatrix1}.matrixIn[5]")
        #heel
        cmds.connectAttr(F"{inverseMatrix3}.outputMatrix",f"{multMatrix1}.matrixIn[6]")
        cmds.connectAttr(F"{composeMatrix1}.outputMatrix",f"{multMatrix1}.matrixIn[7]")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.HeelMatrix",f"{multMatrix1}.matrixIn[8]")
        #toe
        cmds.connectAttr(F"{inverseMatrix4}.outputMatrix",f"{multMatrix1}.matrixIn[9]")
        cmds.connectAttr(F"{composeMatrix2}.outputMatrix",f"{multMatrix1}.matrixIn[10]")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.ToesTipMatrix",f"{multMatrix1}.matrixIn[11]")
        if(clr=="R"):
            composeMatrix5 = cmds.createNode(f"composeMatrix")
            multMatrix2 = cmds.createNode("multMatrix")
            cmds.setAttr(F"{composeMatrix5}.inputScaleX",-1)
            cmds.connectAttr(F"{multMatrix1}.matrixSum",f"{multMatrix2}.matrixIn[0]")
            cmds.connectAttr(F"{composeMatrix5}.outputMatrix",f"{multMatrix2}.matrixIn[1]")
            cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{decomposeMatrix1}.inputMatrix",f=True)
            cmds.setAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.sx",-1)

        #Foot
        create_obj_dic |= autorig_utility.create_controller("FootIK",root_obj,pos_CLR=clr,con_color=(0.2,0.8,0.2),con_shape="scuare",con_size=(3,3,3),con_rotate=(0,0,90),
                                                        unity_setting=unity_setting,scale_unable=True,pos_unable=True)
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.worldMatrix",f"{create_obj_dic[('Grp',clr,'FootIK')]}.offsetParentMatrix")
        cmds.xform(create_obj_dic[('Grp',clr,'FootIK')],m=toes_matrix,ws=True)
        rot = cmds.xform(orientation_dic[f"{clr_lower}_foot"],ro=True,q=True,ws=True)
        pos = cmds.xform(orientation_dic[f"{clr_lower}_foot"],t=True,q=True,ws=True)
        cmds.xform(create_obj_dic[('Grp',clr,'FootIK')],ro=rot,ws=True)
        cmds.xform(create_obj_dic[('Drv',clr,'FootIK')],t=pos,ws=True)
        if(clr=="R"):
            cmds.setAttr(f"{create_obj_dic[('Grp',clr,'FootIK')]}.sy",-1)
            cmds.setAttr(f"{create_obj_dic[('Drv',clr,'FootIK')]}.sy",-1)

        #IKHandle作成
        ikHandle_parent = cmds.group(em=True,n=f"Grp_{clr}_LegIkHandle",p=create_obj_dic[('Drv',clr,'FootIK')])
        ikHandle = cmds.ikHandle(sj=upperLeg_ik_dummy,ee=foot_ik_dummy)[0]
        ikHandle = cmds.parent(ikHandle,ikHandle_parent)[0]
        cmds.setAttr(f"{ikHandle}.v",0,l=True)
        cmds.setAttr(f"{ikHandle}.t",*(0,0,0),typ="double3",l=True)
        cmds.setAttr(f"{ikHandle}.r",*(0,0,0),typ="double3",l=True)
        cmds.setAttr(f"{ikHandle}.s",*(1,1,1),typ="double3",l=True)

        #poleVector作成
        composeMatrix1 = cmds.createNode("composeMatrix")
        blendColors1 = cmds.createNode("blendColors")
        foot_decomposeMatrix = cmds.createNode("decomposeMatrix")
        legRoot_decomposeMatrix = cmds.createNode("decomposeMatrix")

        inverseMatrix1 = cmds.createNode("inverseMatrix")
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        multMatrix1 = cmds.createNode("multMatrix")
        quatSlerp = cmds.createNode("quatSlerp")

        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.connectAttr(f"{root_decomposeMatrix}.outputScale",f"{composeMatrix1}.inputScale")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputShear",f"{composeMatrix1}.inputShear")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(f"{legRoot_decomposeMatrix}.outputTranslate",f"{blendColors1}.color1")
        cmds.connectAttr(f"{foot_decomposeMatrix }.outputTranslate",f"{blendColors1}.color2")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'FootIK')]}.worldMatrix",f"{foot_decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{create_obj_dic[('Drv',clr,'LegRoot')]}.worldMatrix",f"{legRoot_decomposeMatrix}.inputMatrix")
        cmds.setAttr(f"{blendColors1}.blender",0.5)
        cmds.connectAttr(f"{blendColors1}.output",f"{composeMatrix1}.inputTranslate")
        lowerLeg_pos = cmds.xform(orientation_dic[f"{clr_lower}_lowerLeg"],ws=True,t=True,q=True)
        foot_pos = cmds.xform(orientation_dic[f"{clr_lower}_foot"],ws=True,t=True,q=True)
        upperLeg_pos = cmds.xform(orientation_dic[f"{clr_lower}_upperLeg"],ws=True,t=True,q=True)
        upperLeg_length = math.sqrt((upperLeg_pos[0]-lowerLeg_pos[0])**2+(upperLeg_pos[1]-lowerLeg_pos[1])**2+(upperLeg_pos[2]-lowerLeg_pos[2])**2)
        lowerLeg_length = math.sqrt((foot_pos[0]-lowerLeg_pos[0])**2+(foot_pos[1]-lowerLeg_pos[1])**2+(foot_pos[2]-lowerLeg_pos[2])**2)

        cmds.addAttr(create_obj_dic[('Drv',clr,'FootIK')],ln="WorldBindMatrix",at="matrix")
        matrix = cmds.xform(create_obj_dic[('Grp',clr,'FootIK')],m=True,ws=True,q=True)
        cmds.setAttr(f"{create_obj_dic[('Drv',clr,'FootIK')]}.WorldBindMatrix",*matrix,typ="matrix")

        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'FootIK')]}.WorldBindMatrix",f"{inverseMatrix1}.inputMatrix")
        cmds.connectAttr(F"{inverseMatrix1}.outputMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'FootIK')]}.parentMatrix",f"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(f"{root_decomposeMatrix}.outputQuat",F"{quatSlerp}.input1Quat")
        cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",F"{quatSlerp}.input2Quat")
        cmds.connectAttr(F"{quatSlerp}.outputQuat",f"{composeMatrix1}.inputQuat",f=True)
        
        #lowerLegに一番近いfootとupperLeg結んだ直線状の点特定
        hiritu = upperLeg_length/(upperLeg_length+lowerLeg_length)
        pos = [(foot_pos[i]-upperLeg_pos[i])*hiritu for i in range(3)]
        length = math.sqrt(((pos[0]+upperLeg_pos[0])-lowerLeg_pos[0])**2+((pos[1]+upperLeg_pos[1])-lowerLeg_pos[1])**2+((pos[2]+upperLeg_pos[2])-lowerLeg_pos[2])**2)
        baitiru = ((upperLeg_length+lowerLeg_length)*0.6)/length

        pv_pos = [((lowerLeg_pos[i]-upperLeg_pos[i])-pos[i])*baitiru+(pos[i]+upperLeg_pos[i]) for i in range(3) ]


        create_obj_dic |= autorig_utility.create_controller("LegPV",root_obj,pos_CLR=clr,con_color=(0.8,0.8,0),con_shape="dia1",con_size=(2,2,2),con_position=[pv_pos[i]-(pos[i]+upperLeg_pos[i]) for i in range(3)],
                                                            unity_setting=unity_setting,con_scl_lock=(False,False,False))
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegPV')]}",ln="LayeredRotate",at="float",max=1,min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegPV')]}.LayeredRotate",1,k=True)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegPV')]}.LayeredRotate",F"{quatSlerp}.inputT")
        
        cmds.connectAttr(F"{composeMatrix1}.outputMatrix",f"{create_obj_dic[('Grp',clr,'LegPV')]}.offsetParentMatrix")
        cmds.xform(f"{create_obj_dic[('Grp',clr,'LegPV')]}",t=[pos[i]+upperLeg_pos[i] for i in range(3) ],ws=True)
        cmds.xform(f"{create_obj_dic[('Drv',clr,'LegPV')]}",t=pv_pos,ws=True)
        if(clr=="R"):
            cmds.setAttr(F"{create_obj_dic[('Grp',clr,'LegPV')]}.sx",-1)
        cmds.poleVectorConstraint(create_obj_dic[('Drv',clr,'LegPV')],ikHandle)

        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="twist",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.twist",0,k=True)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.twist",f"{ikHandle}.twist")

        #IKスケーリング
        cmds.addAttr(ik_parent,ln="FootMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(foot_matrix)*OpenMaya.MMatrix(cmds.xform(ik_parent,q=True,ws=True,m=True)).inverse()
        cmds.setAttr(F"{ik_parent}.FootMatrix",*list(matrix),typ="matrix",lock=True, keyable=False)

        cmds.addAttr(ik_parent,ln="LowerLegMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(lowerLeg_matrix)*OpenMaya.MMatrix(cmds.xform(ik_parent,q=True,ws=True,m=True)).inverse()
        cmds.setAttr(F"{ik_parent}.LowerLegMatrix",*list(matrix),typ="matrix",lock=True, keyable=False)
        
        #アトリビュート作成
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="stretch",at="float",max=1,min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.stretch",1,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="addUpperLegStretch",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.addUpperLegStretch",0,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="addLowerLegStretch",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.addLowerLegStretch",0,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="addLegStretch",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.addLegStretch",0,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="legUniformScale",at="float")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.legUniformScale",1,k=True)

        #計算
        multMatrix1 = cmds.createNode("multMatrix")
        multMatrix2 = cmds.createNode("multMatrix")
        distanceBetween1 = cmds.createNode("distanceBetween")
        distanceBetween2 = cmds.createNode("distanceBetween")
        distanceBetween3 = cmds.createNode("distanceBetween")
        blendColors1 = cmds.createNode("blendColors")
        blendColors2 = cmds.createNode("blendColors")
        condition1 = cmds.createNode("condition")
        condition2 = cmds.createNode("condition")
        condition3 = cmds.createNode("condition")
        floatMath1 = cmds.createNode("floatMath")
        floatMath2 = cmds.createNode("floatMath")
        floatMath3 = cmds.createNode("floatMath")
        floatMath4 = cmds.createNode("floatMath")
        floatMath5 = cmds.createNode("floatMath")
        floatMath6 = cmds.createNode("floatMath")
        floatMath7 = cmds.createNode("floatMath")
        floatMath8 = cmds.createNode("floatMath")

        cmds.setAttr(f"{floatMath2}.operation",2)
        cmds.setAttr(f"{floatMath3}.operation",3)
        cmds.setAttr(f"{floatMath4}.operation",2)
        cmds.setAttr(f"{condition1}.operation",2)
        cmds.setAttr(f"{condition2}.operation",0)
        cmds.setAttr(f"{condition3}.operation",0)
        cmds.setAttr(f"{condition2}.secondTerm",1)
        cmds.setAttr(f"{condition3}.secondTerm",1)
        cmds.setAttr(f"{condition2}.colorIfFalseR",1)
        cmds.setAttr(f"{condition2}.colorIfFalseG",1)
        cmds.setAttr(f"{condition2}.colorIfFalseB",1)
        cmds.setAttr(f"{condition3}.colorIfFalseR",1)
        cmds.setAttr(f"{condition3}.colorIfFalseG",1)
        cmds.setAttr(f"{condition3}.colorIfFalseB",1)

        cmds.connectAttr(f"{ik_parent}.FootMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(f"{ik_parent}.LowerLegMatrix",f"{multMatrix2}.matrixIn[0]")
        cmds.connectAttr(f"{ik_parent}.worldMatrix",f"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(f"{ik_parent}.worldMatrix",f"{multMatrix2}.matrixIn[1]")
        cmds.connectAttr(f"{ik_parent}.worldMatrix",f"{distanceBetween2}.inMatrix1")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{distanceBetween2}.inMatrix2")
        cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{distanceBetween1}.inMatrix2")
        cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{distanceBetween1}.inMatrix1")
        cmds.connectAttr(f"{ik_parent}.worldMatrix",f"{distanceBetween3}.inMatrix2")
        cmds.connectAttr(f"{ikHandle_parent}.worldMatrix",f"{distanceBetween3}.inMatrix1")
        cmds.connectAttr(f"{distanceBetween1}.distance",f"{floatMath1}.floatA")
        cmds.connectAttr(f"{distanceBetween2}.distance",f"{floatMath1}.floatB")
        cmds.connectAttr(f"{floatMath1}.outFloat",f"{floatMath2}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.legUniformScale",f"{floatMath2}.floatB")
        cmds.connectAttr(f"{distanceBetween3}.distance",f"{floatMath3}.floatA")
        cmds.connectAttr(f"{floatMath2}.outFloat",f"{floatMath3}.floatB")
        cmds.connectAttr(f"{floatMath3}.outFloat",f"{floatMath4}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.legUniformScale",f"{floatMath4}.floatB")
        cmds.connectAttr(f"{distanceBetween3}.distance",f"{condition1}.firstTerm")
        cmds.connectAttr(f"{floatMath2}.outFloat",f"{condition1}.secondTerm")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.legUniformScale",f"{condition1}.colorIfFalseR")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.legUniformScale",f"{condition1}.colorIfFalseG")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.legUniformScale",f"{condition1}.colorIfFalseB")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.legUniformScale",f"{condition1}.colorIfTrueR")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.legUniformScale",f"{condition1}.colorIfTrueB")
        cmds.connectAttr(f"{floatMath4}.outFloat",f"{condition1}.colorIfTrueG")
        cmds.connectAttr(f"{condition1}.outColor",f"{blendColors1}.color1")
        cmds.connectAttr(f"{condition1}.colorIfFalse",f"{blendColors1}.color2")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.stretch",f"{blendColors1}.blender")
        cmds.connectAttr(f"{condition1}.outColor",f"{blendColors2}.color1")
        cmds.connectAttr(f"{condition1}.colorIfFalse",f"{blendColors2}.color2")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.stretch",f"{blendColors2}.blender")
        cmds.connectAttr(F"{blendColors1}.outputR",f"{condition2}.colorIfTrueR")
        cmds.connectAttr(F"{blendColors1}.outputB",f"{condition2}.colorIfTrueB")
        cmds.connectAttr(F"{blendColors2}.outputR",f"{condition3}.colorIfTrueR")
        cmds.connectAttr(F"{blendColors2}.outputB",f"{condition3}.colorIfTrueB")

        cmds.connectAttr(f"{blendColors1}.outputG",f"{floatMath5}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.addUpperLegStretch",f"{floatMath5}.floatB")
        cmds.connectAttr(F"{floatMath5}.outFloat",f"{floatMath6}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.addLegStretch",f"{floatMath6}.floatB")
        cmds.connectAttr(f"{floatMath6}.outFloat",f"{condition2}.colorIfTrueG")
        cmds.connectAttr(f"{obj_dic[('Con','C','UnitySetting')]}.Scalable",f"{condition2}.firstTerm")

        cmds.connectAttr(f"{blendColors2}.outputG",f"{floatMath7}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.addLowerLegStretch",f"{floatMath7}.floatB")
        cmds.connectAttr(F"{floatMath7}.outFloat",f"{floatMath8}.floatA")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.addLegStretch",f"{floatMath8}.floatB")
        cmds.connectAttr(f"{floatMath8}.outFloat",f"{condition3}.colorIfTrueG")
        cmds.connectAttr(f"{obj_dic[('Con','C','UnitySetting')]}.Scalable",f"{condition3}.firstTerm")

        #方向特定
        x=[1,0,0,0,0,1,0,0,0,0,1,0,1,0,0,1]
        y=[1,0,0,0,0,1,0,0,0,0,1,0,0,1,0,1]
        z=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,1,1]
        lowerLeg_joint_matrix = cmds.xform(lowerLeg_fk,q=True,ws=True,m=True)
        upperLeg_joint_matrix = cmds.xform(upperLeg_fk,q=True,ws=True,m=True)
        hand_pos = cmds.xform(foot_fk,q=True,ws=True,t=True)
        #Lower
        lower_x_pos = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(x)*OpenMaya.MMatrix(lowerLeg_joint_matrix)).translation(OpenMaya.MSpace.kWorld)
        lower_y_pos = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(y)*OpenMaya.MMatrix(lowerLeg_joint_matrix)).translation(OpenMaya.MSpace.kWorld)
        lower_z_pos = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(z)*OpenMaya.MMatrix(lowerLeg_joint_matrix)).translation(OpenMaya.MSpace.kWorld)
        lower_x_distance = [(lower_x_pos[i]-hand_pos[i])**2 for i in range(3)]
        lower_y_distance = [(lower_y_pos[i]-hand_pos[i])**2 for i in range(3)]
        lower_z_distance = [(lower_z_pos[i]-hand_pos[i])**2 for i in range(3)]
        if(lower_x_distance<lower_y_distance and lower_x_distance<lower_z_distance):
            cmds.connectAttr(f"{condition3}.outColorG",f"{lowerLeg_ik_dummy}.sx")
            cmds.connectAttr(f"{condition3}.outColorR",f"{lowerLeg_ik_dummy}.sy")
            cmds.connectAttr(f"{condition3}.outColorR",f"{lowerLeg_ik_dummy}.sz")
        if(lower_y_distance<lower_x_distance and lower_y_distance<lower_z_distance):
            cmds.connectAttr(f"{condition3}.outColorR",f"{lowerLeg_ik_dummy}.sx")
            cmds.connectAttr(f"{condition3}.outColorG",f"{lowerLeg_ik_dummy}.sy")
            cmds.connectAttr(f"{condition3}.outColorR",f"{lowerLeg_ik_dummy}.sz")
        if(lower_z_distance<lower_x_distance and lower_z_distance<lower_y_distance):
            cmds.connectAttr(f"{condition3}.outColorR",f"{lowerLeg_ik_dummy}.sx")
            cmds.connectAttr(f"{condition3}.outColorR",f"{lowerLeg_ik_dummy}.sy")
            cmds.connectAttr(f"{condition3}.outColorG",f"{lowerLeg_ik_dummy}.sz")
        #Upper
        upper_x_pos = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(x)*OpenMaya.MMatrix(upperLeg_joint_matrix)).translation(OpenMaya.MSpace.kWorld)
        upper_y_pos = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(y)*OpenMaya.MMatrix(upperLeg_joint_matrix)).translation(OpenMaya.MSpace.kWorld)
        upper_z_pos = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(z)*OpenMaya.MMatrix(upperLeg_joint_matrix)).translation(OpenMaya.MSpace.kWorld)
        upper_x_distance = [(upper_x_pos[i]-hand_pos[i])**2 for i in range(3)]
        upper_y_distance = [(upper_y_pos[i]-hand_pos[i])**2 for i in range(3)]
        upper_z_distance = [(upper_z_pos[i]-hand_pos[i])**2 for i in range(3)]
        if(upper_x_distance<upper_y_distance and upper_x_distance<upper_z_distance):
            cmds.connectAttr(f"{condition2}.outColorG",f"{upperLeg_ik_dummy}.sx")
            cmds.connectAttr(f"{condition2}.outColorR",f"{upperLeg_ik_dummy}.sy")
            cmds.connectAttr(f"{condition2}.outColorR",f"{upperLeg_ik_dummy}.sz")
        if(upper_y_distance<upper_x_distance and upper_y_distance<upper_z_distance):
            cmds.connectAttr(f"{condition2}.outColorR",f"{upperLeg_ik_dummy}.sx")
            cmds.connectAttr(f"{condition2}.outColorG",f"{upperLeg_ik_dummy}.sy")
            cmds.connectAttr(f"{condition2}.outColorR",f"{upperLeg_ik_dummy}.sz")
        if(upper_z_distance<upper_x_distance and upper_z_distance<upper_y_distance):
            cmds.connectAttr(f"{condition2}.outColorR",f"{upperLeg_ik_dummy}.sx")
            cmds.connectAttr(f"{condition2}.outColorR",f"{upperLeg_ik_dummy}.sy")
            cmds.connectAttr(f"{condition2}.outColorG",f"{upperLeg_ik_dummy}.sz")

        cmds.setAttr(F"{ik_parent}.v",0,k=False,l=True)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'UpperLegFK')]}.v",l=False)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'LowerLegFK')]}.v",l=False)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'FootFK')]}.v",l=False)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'ToesFK')]}.v",l=False)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'LegPV')]}.v",l=False)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'LegIK')]}.v",l=False)
        cmds.setAttr(F"{create_obj_dic[('Grp',clr,'FootIK')]}.v",l=False)

        floatMath1 = cmds.createNode("floatMath")
        floatMath2 = cmds.createNode("floatMath")
        cmds.setAttr(F"{floatMath1}.operation",2)
        cmds.setAttr(F"{floatMath1}.floatB",-1)
        cmds.setAttr(F"{floatMath2}.floatB",1)
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK",F"{create_obj_dic[('Grp',clr,'UpperLegFK')]}.v")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK",F"{create_obj_dic[('Grp',clr,'LowerLegFK')]}.v")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK",F"{create_obj_dic[('Grp',clr,'FootFK')]}.v")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK",F"{create_obj_dic[('Grp',clr,'ToesFK')]}.v")
        cmds.connectAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK",F"{floatMath1}.floatA")
        cmds.connectAttr(F"{floatMath1}.outFloat",F"{floatMath2}.floatA")
        cmds.connectAttr(f"{floatMath2}.outFloat",F"{create_obj_dic[('Grp',clr,'LegPV')]}.v")
        cmds.connectAttr(f"{floatMath2}.outFloat",F"{create_obj_dic[('Grp',clr,'LegIK')]}.v")
        cmds.connectAttr(f"{floatMath2}.outFloat",F"{create_obj_dic[('Grp',clr,'FootIK')]}.v")
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegRoot')]}.IKFK",0)

        #SmoothIK
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="smoothIK",at="float",max=1,min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.smoothIK",0,k=True)
        cmds.addAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}",ln="smoothRange",at="float",min=0)
        cmds.setAttr(f"{create_obj_dic[('Con',clr,'LegIK')]}.smoothRange",5,k=True)
        floatMath1 = cmds.createNode("floatMath")
        floatMath2 = cmds.createNode("floatMath")
        floatMath3 = cmds.createNode("floatMath")
        floatMath4 = cmds.createNode("floatMath")
        floatMath5 = cmds.createNode("floatMath")
        floatMath6 = cmds.createNode("floatMath")
        floatMath7 = cmds.createNode("floatMath")
        floatMath8 = cmds.createNode("floatMath")
        floatMath9 = cmds.createNode("floatMath")
        floatMath10 = cmds.createNode("floatMath")
        floatMath11 = cmds.createNode("floatMath")
        distanceBetween1 = cmds.createNode("distanceBetween")
        distanceBetween2 = cmds.createNode("distanceBetween")
        distanceBetween3 = cmds.createNode("distanceBetween")
        decomposeMatrix1 = cmds.createNode("decomposeMatrix")
        decomposeMatrix2 = cmds.createNode("decomposeMatrix")
        composeMatrix1 = cmds.createNode("composeMatrix")
        composeMatrix2 = cmds.createNode("composeMatrix")
        aimMatrix1 = cmds.createNode("aimMatrix")
        multMatrix1 = cmds.createNode("multMatrix")
        condition1 = cmds.createNode("condition")
        condition2 = cmds.createNode("condition")
        absolute = cmds.createNode("absolute")
        cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
        cmds.setAttr(f"{composeMatrix2}.useEulerRotation",0)
        cmds.setAttr(f"{floatMath1}.operation",2)
        cmds.setAttr(f"{floatMath2}.operation",2)
        cmds.setAttr(f"{floatMath3}.operation",2)
        cmds.setAttr(f"{floatMath4}.operation",1)
        cmds.setAttr(f"{floatMath5}.operation",3)
        cmds.setAttr(f"{floatMath6}.operation",2)
        cmds.setAttr(f"{floatMath7}.operation",0)
        cmds.setAttr(f"{floatMath8}.operation",2)
        cmds.setAttr(f"{floatMath9}.operation",2)
        cmds.setAttr(f"{floatMath10}.operation",2)
        cmds.setAttr(f"{condition1}.operation",2)
        cmds.setAttr(f"{condition2}.operation",2)
        cmds.setAttr(f"{condition1}.colorIfFalseR",0)
        cmds.setAttr(f"{floatMath6}.floatB",0.5)
        cmds.setAttr(f"{floatMath7}.floatB",0.5)
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.legUniformScale",f"{floatMath1}.floatA")
        cmds.connectAttr(F"{ik_parent}.sx",f"{floatMath1}.floatB")
        cmds.connectAttr(F"{floatMath1}.outFloat",f"{floatMath2}.floatA")
        cmds.connectAttr(F"{floatMath1}.outFloat",f"{floatMath3}.floatA")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.smoothRange",f"{floatMath2}.floatB")
        cmds.connectAttr(F"{distanceBetween1}.distance",f"{floatMath11}.floatA")
        cmds.connectAttr(F"{distanceBetween3}.distance",f"{floatMath11}.floatB")
        cmds.connectAttr(F"{floatMath11}.outFloat",f"{floatMath3}.floatB")
        cmds.connectAttr(f"{foot_ik_dummy}.WorldBindMatrix",f"{distanceBetween1}.inMatrix1")
        cmds.connectAttr(f"{lowerLeg_ik_dummy}.WorldBindMatrix",f"{distanceBetween1}.inMatrix2")
        cmds.connectAttr(f"{foot_ik_dummy}.WorldBindMatrix",f"{distanceBetween3}.inMatrix1")
        cmds.connectAttr(f"{lowerLeg_ik_dummy}.WorldBindMatrix",f"{distanceBetween3}.inMatrix2")
        cmds.connectAttr(f"{ik_parent}.worldMatrix",f"{distanceBetween2}.inMatrix1")
        cmds.connectAttr(f"{ikHandle_parent}.parentMatrix",f"{distanceBetween2}.inMatrix2")
        cmds.connectAttr(f"{ik_parent}.worldMatrix",f"{aimMatrix1}.primaryTargetMatrix")
        cmds.connectAttr(f"{ikHandle_parent}.parentMatrix",f"{aimMatrix1}.inputMatrix")
        cmds.connectAttr(f"{aimMatrix1}.outputMatrix",f"{decomposeMatrix1}.inputMatrix")
        cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix1}.matrixIn[0]")
        cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix1}.matrixIn[1]")
        cmds.connectAttr(f"{ikHandle_parent}.parentInverseMatrix",f"{multMatrix1}.matrixIn[2]")
        cmds.connectAttr(F"{decomposeMatrix1}.outputQuat",f"{composeMatrix1}.inputQuat")
        cmds.connectAttr(F"{decomposeMatrix1}.outputShear",f"{composeMatrix1}.inputShear")
        cmds.connectAttr(F"{decomposeMatrix1}.outputTranslate",f"{composeMatrix1}.inputTranslate")
        cmds.connectAttr(F"{multMatrix1}.matrixSum",f"{decomposeMatrix2}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix2}.outputTranslate",f"{ikHandle_parent}.t")
        cmds.connectAttr(F"{floatMath3}.outFloat",f"{floatMath4}.floatB")
        cmds.connectAttr(F"{distanceBetween2}.distance",f"{floatMath4}.floatA")
        cmds.connectAttr(F"{floatMath2}.outFloat",f"{floatMath5}.floatB")
        cmds.connectAttr(F"{floatMath2}.outFloat",f"{floatMath9}.floatB")
        cmds.connectAttr(F"{floatMath2}.outFloat",F"{condition2}.secondTerm")
        cmds.connectAttr(F"{create_obj_dic[('Con',clr,'LegIK')]}.smoothIK",f"{floatMath10}.floatB")
        cmds.connectAttr(F"{floatMath4}.outFloat",f"{floatMath5}.floatA")
        cmds.connectAttr(F"{floatMath4}.outFloat",f"{absolute}.input")
        cmds.connectAttr(F"{floatMath4}.outFloat",f"{condition1}.firstTerm")
        cmds.connectAttr(F"{floatMath4}.outFloat",f"{condition1}.colorIfTrueR")
        cmds.connectAttr(f"{absolute}.output",f"{condition2}.firstTerm")
        cmds.connectAttr(f"{condition1}.outColorR",f"{condition2}.colorIfTrueR")
        cmds.connectAttr(F"{floatMath10}.outFloat",f"{composeMatrix2}.inputTranslateX")
        cmds.connectAttr(F"{condition2}.outColorR",f"{floatMath10}.floatA")
        cmds.connectAttr(f"{floatMath9}.outFloat",f"{condition2}.colorIfFalseR")
        cmds.connectAttr(F"{floatMath5}.outFloat",f"{floatMath6}.floatA")
        cmds.connectAttr(F"{floatMath6}.outFloat",f"{floatMath7}.floatA")
        cmds.connectAttr(F"{floatMath7}.outFloat",f"{floatMath8}.floatA")
        cmds.connectAttr(F"{floatMath7}.outFloat",f"{floatMath8}.floatB")
        cmds.connectAttr(F"{floatMath8}.outFloat",f"{floatMath9}.floatA")

        #アトリビュート作成
        Drv_Obj=ikHandle
        Dvn_Obj=foot_ik
        drv_matrix = cmds.xform(Drv_Obj,q=True,ws=True,m=True)
        dvn_matrix = cmds.xform(Dvn_Obj,q=True,ws=True,m=True)
        if(cmds.objExists(f"{Drv_Obj}.WorldBindMatrix") == True):
            cmds.setAttr(f"{Drv_Obj}.WorldBindMatrix",lock=False)
        else:
            cmds.addAttr(Drv_Obj,ln="WorldBindMatrix",at="matrix")
        if(cmds.objExists(f"{Dvn_Obj}.WorldBindMatrix") == True):
            cmds.setAttr(f"{Dvn_Obj}.WorldBindMatrix",lock=False)
        else:
            cmds.addAttr(Dvn_Obj,ln="WorldBindMatrix",at="matrix")
        cmds.setAttr(f"{Drv_Obj}.WorldBindMatrix",*drv_matrix,typ="matrix")
        cmds.setAttr(f"{Drv_Obj}.WorldBindMatrix",lock=True, keyable=False)
        cmds.setAttr(f"{Dvn_Obj}.WorldBindMatrix",*dvn_matrix,typ="matrix")
        cmds.setAttr(f"{Dvn_Obj}.WorldBindMatrix",lock=True, keyable=False)
        cmds.setAttr(f"{Dvn_Obj}.jointOrient" ,*(0,0,0),typ="double3")
        #計算
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
        #cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{Dvn_Obj}.t",f=True)
        cmds.connectAttr(f"{decomposeMatrix1}.outputRotate",f"{Dvn_Obj}.r",f=True)
        cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{Dvn_Obj}.s",f=True)
        cmds.connectAttr(f"{decomposeMatrix1}.outputShear",f"{Dvn_Obj}.shear",f=True)

        #つま先
        create_obj_dic |= autorig_utility.create_controller("ToesIK",root_obj,pos_CLR=clr,con_color=(0.2,0.8,0.2),con_shape="scuare",con_size=(3,3,3),con_rotate=(0,0,90),
                                                        unity_setting=unity_setting,scale_unable=True,con_pos_lock=(False,False,False))
        cmds.connectAttr(F"{create_obj_dic[('Drv',clr,'LegIK')]}.worldMatrix",f"{create_obj_dic[('Grp',clr,'ToesIK')]}.offsetParentMatrix")
        cmds.xform(create_obj_dic[('Grp',clr,'ToesIK')],m=toes_matrix,ws=True)
        if(clr=="R"):
            cmds.setAttr(F"{create_obj_dic[('Grp',clr,'ToesIK')]}.sy",-1)
            cmds.setAttr(F"{create_obj_dic[('Drv',clr,'ToesIK')]}.sy",-1)
        Drv_Obj=create_obj_dic[('Drv',clr,'ToesIK')]
        Dvn_Obj=toes_ik
        drv_matrix = cmds.xform(Drv_Obj,q=True,ws=True,m=True)
        dvn_matrix = cmds.xform(Dvn_Obj,q=True,ws=True,m=True)
        if(cmds.objExists(f"{Drv_Obj}.WorldBindMatrix") == True):
            cmds.setAttr(f"{Drv_Obj}.WorldBindMatrix",lock=False)
        else:
            cmds.addAttr(Drv_Obj,ln="WorldBindMatrix",at="matrix")
        if(cmds.objExists(f"{Dvn_Obj}.WorldBindMatrix") == True):
            cmds.setAttr(f"{Dvn_Obj}.WorldBindMatrix",lock=False)
        else:
            cmds.addAttr(Dvn_Obj,ln="WorldBindMatrix",at="matrix")
        cmds.setAttr(f"{Drv_Obj}.WorldBindMatrix",*drv_matrix,typ="matrix")
        cmds.setAttr(f"{Drv_Obj}.WorldBindMatrix",lock=True, keyable=False)
        cmds.setAttr(f"{Dvn_Obj}.WorldBindMatrix",*dvn_matrix,typ="matrix")
        cmds.setAttr(f"{Dvn_Obj}.WorldBindMatrix",lock=True, keyable=False)
        cmds.setAttr(f"{Dvn_Obj}.jointOrient" ,*(0,0,0),typ="double3")
        #計算
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
        #cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{Dvn_Obj}.t",f=True)
        cmds.connectAttr(f"{decomposeMatrix1}.outputRotate",f"{Dvn_Obj}.r",f=True)
        cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{Dvn_Obj}.s",f=True)
        cmds.connectAttr(f"{decomposeMatrix1}.outputShear",f"{Dvn_Obj}.shear",f=True)

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
    unity_setting = obj_dic[('Con','C','UnitySetting')]

    #親作成
    root_center_obj = cmds.group(em=True,n=f"Grp_C_Hand",p=parent)
    cmds.setAttr( f"{root_center_obj}.t", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{root_center_obj}.r", lock=True, keyable=False, channelBox=False)
    cmds.setAttr( f"{root_center_obj}.s", lock=True, keyable=False, channelBox=False)
    cmds.setAttr(f"{root_center_obj}.v",keyable=False,channelBox=True)

    #左右繰り返し
    for clr in ("L","R"):
        clr_lower = clr.lower()
        root_obj = cmds.group(em=True,n=f"Grp_{clr}_Hand",p=root_center_obj)


    return create_obj_dic



