from maya import cmds
from maya.api import OpenMaya
from pathlib import Path
import json
import importlib

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
                                                        create_drv=False)
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
    autorig_utility.layerd_scale(create_obj_dic[('Grp','C','SpineFK')],create_obj_dic[('Drv','C','SpineFK')],
                                create_obj_dic[('Grp','C','ChestFK')],create_obj_dic[('Con','C','ChestFK')])
    #UpperChestFK
    if("c_upperChestFK" in orientation_dic):
        create_obj_dic |= autorig_utility.create_controller("UpperChestFK",root_obj,pos_CLR="C",con_color=(0.2,0,1),con_shape="circle",con_size=(9,9,9),con_rotate=(0,0,90),
                                                            unity_setting=unity_setting,scale_unable=True,pos_unable=True)
        cmds.connectAttr(f"{create_obj_dic[('Drv','C','ChestFK')]}.worldMatrix[0]",f"{create_obj_dic[('Grp','C','UpperChestFK')]}.offsetParentMatrix")
        cmds.xform(create_obj_dic[('Grp','C','UpperChestFK')],m=upperChest_matrix,ws=True)
        autorig_utility.layerd_scale(create_obj_dic[('Grp','C','SpineFK')],create_obj_dic[('Drv','C','ChestFK')],
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
        cmds.setAttr(f"{create_obj_dic[('Con','C','SpineIK')]}.FollowTwist",1,k=True)
        cmds.connectAttr(f"{create_obj_dic[('Con','C','SpineIK')]}.FollowTwist",f"{quatSlerp}.inputT",f=True)
        cmds.setAttr(f"{create_obj_dic[('Con','C','SpineIK')]}.FollowTwist",0.4)
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
        autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','SpineIK')]}",joint_dic["c_spine"])
        autorig_utility.matrix_constraint(f"{create_obj_dic[('Drv','C','ChestIK')]}",joint_dic["c_chest"])

    return create_obj_dic




