from maya import cmds
import importlib
from pathlib import Path
import json

from . import autorig_preparation
importlib.reload(autorig_preparation)

from . import autorig_createRig
importlib.reload(autorig_createRig)

from . import autorig_utility
importlib.reload(autorig_utility)

#json読み込み
with open(f"{Path(__file__).resolve().parent}/joint_name.json", mode="rt", encoding="utf-8") as f:
    joint_name = json.load(f)

def create_rig(textField_dic:dict,character_name:str):
    """
    準備開始

    Parameters
    ----------
        dictionary textfield : Joint名のテキストボックスが入った辞書
        string character_name : 名前を入れるテキストボックス

    Returns
    -------
        無し
    """
    check = autorig_preparation.check_textfield(textField_dic,character_name)
    check_bool = check[0]
    joint_dic=check[1]
    character_name = cmds.textField(character_name,q=True,tx=True)
    
    if not check_bool:
        return
    # Validate the guide set before touching the source skeleton.
    if cmds.objExists(f"{character_name}_Rig"):
        raise ValueError("A rig with this character name already exists")
    for group in (f"Orient_C_{character_name}", f"Position_C_{character_name}"):
        if len(cmds.ls(group,type="transform",long=True)) != 1:
            raise ValueError("A unique orientation and position guide set is required")
    undo_enabled = cmds.undoInfo(q=True,state=True)
    refresh_suspended = cmds.refresh(q=True,suspend=True)
    if not undo_enabled:
        cmds.undoInfo(stateWithoutFlush=True)
    cmds.undoInfo(openChunk=True,chunkName="AutoRigForHumanoid_CreateRig")
    try:
        try:
            cmds.refresh(suspend=True)
            root_grp = cmds.group(em=True,n=f"{character_name}_Rig")
            cmds.setAttr(f"{root_grp}.t",lock=True)
            cmds.setAttr(f"{root_grp}.r",lock=True)
            cmds.setAttr(f"{root_grp}.s",lock=True)
            humanoid_dummy_joint = create_dummyHumanoid(joint_dic,character_name,root_grp)
            orientation_dic = get_orientation(character_name)
            pos_dic = get_pos(character_name)
            autorig_createRig.init_createRig(humanoid_dummy_joint,character_name,root_grp,orientation_dic,pos_dic)
        finally:
            cmds.undoInfo(closeChunk=True)
            cmds.refresh(suspend=refresh_suspended)
    except Exception:
        # Deleting the rig does not undo edits/connections on the source joints.
        cmds.undo()
        raise
    finally:
        if not undo_enabled:
            cmds.undoInfo(stateWithoutFlush=False)
        if not refresh_suspended:
            cmds.refresh()
    return root_grp


def create_dummyHumanoid(joint_dic:dict,character_name:str,parent:str):
    """
    リグでいじるダミーのジョイント作成

    Parameters
    ----------
        dictionary textfield : Joint名のテキストボックスが入った辞書
        string character_name : 名前を入れるテキストボックス
        string parent : 親になるオブジェクト

    Returns
    -------
        dict 複製したjointのフルパス辞書
    """
    root_grp = cmds.group(em=True,n=f"Grp_C_{character_name}DummyHumanoid")
    cmds.parent(root_grp,parent)
    cmds.setAttr(f"{root_grp}.t",lock=True)
    cmds.setAttr(f"{root_grp}.r",lock=True)
    cmds.setAttr(f"{root_grp}.s",lock=True)
    cmds.setAttr(f"{root_grp}.v",0,lock=False,k=False)

    # Preserve the evaluated pose while folding jointOrient into rotate.
    # xform respects each joint's rotateOrder and avoids temporary quaternion nodes.
    for key in joint_dic:
        joint = joint_dic[key]
        world_matrix = cmds.xform(joint,q=True,ws=True,m=True)
        cmds.setAttr(f"{joint}.jointOrient",0,0,0,type="double3")
        cmds.xform(joint,ws=True,m=world_matrix)
        #アトリビュート作成
        cmds.addAttr(joint,ln="name",dt="string")
        cmds.setAttr(f"{joint}.name",key,typ="string")

    #以下、hipsを起点に階層ごとduplicateしてHumanoid以外を削除する現行方式に置き換え済み
    hips = cmds.ls(joint_dic["c_hips"],l=True)[0]
    hips_name = cmds.ls(hips,l=False)[0]
    hips_parent = cmds.listRelatives(hips,p=True,f=True)
    if(hips_parent==None):
        matrix = [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
    else:
        matrix = cmds.xform(hips_parent[0],q=True,ws=True,m=True)
    cmds.xform(root_grp,ws=True,m=matrix)
    joint_list = cmds.duplicate(hips,smartTransform=True,f=True,rc=False,n=f"{hips_name}_Dummy")
    for joint in joint_list:
        if(len(cmds.ls(joint))!=0):
            children = cmds.listRelatives(joint,ad=True,f=True)
            if(children==None):
                children = [joint]
            else:
                children.append(joint)
            humanoid=False
            for child in children:
                if(cmds.objExists(f"{child}.name") == True):
                    humanoid=True
            if(humanoid==False):
                cmds.delete(joint)

    duplicate_hips=cmds.parent(joint_list[0],root_grp,r=False)[0]
    duplicate_joint = cmds.listRelatives(duplicate_hips,ad=True,f=True)

    for joint in duplicate_joint:
        name = cmds.ls(joint,l=False)[0]
        name=name.split("|")[-1]
        joint = cmds.rename(joint,f"{name}_Dummy")

    duplicate_joint = cmds.listRelatives(duplicate_hips,ad=True,f=True)
    duplicate_joint.append(duplicate_hips)
    duplicate_joint_dic = {}
    for joint in duplicate_joint:
        if(cmds.objExists(f"{joint}.name") == True):
            name = cmds.getAttr(f"{joint}.name")
            duplicate_joint_dic[name] = cmds.ls(joint,l=True)[0]
    

    for k in duplicate_joint_dic:
        #トランスフォームの一致
        multMatrix = cmds.shadingNode("multMatrix",asUtility=True)
        cmds.connectAttr(f"{joint_dic[k]}.parentInverseMatrix[0]",f"{multMatrix}.matrixIn[1]")
        cmds.connectAttr(f"{duplicate_joint_dic[k]}.worldMatrix[0]",f"{multMatrix}.matrixIn[0]")
        decomposeMatrix = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{multMatrix}.matrixSum",f"{decomposeMatrix}.inputMatrix")
        cmds.connectAttr(f"{decomposeMatrix}.outputTranslate",f"{joint_dic[k]}.t")
        cmds.connectAttr(f"{decomposeMatrix}.outputScale",f"{joint_dic[k]}.s")
        cmds.connectAttr(f"{joint_dic[k]}.rotateOrder",f"{decomposeMatrix}.inputRotateOrder")
        quatProd = cmds.createNode("quatProd")
        cmds.connectAttr(f"{decomposeMatrix}.outputQuat",f"{quatProd}.input1Quat")
        quatToEuler = cmds.createNode("quatToEuler")
        cmds.connectAttr(f"{quatProd}.outputQuat",f"{quatToEuler}.inputQuat")
        cmds.connectAttr(f"{joint_dic[k]}.rotateOrder",f"{quatToEuler}.inputRotateOrder")
        eulerToQuat = cmds.createNode("eulerToQuat")
        cmds.connectAttr(f"{joint_dic[k]}.rotateOrder",f"{eulerToQuat}.inputRotateOrder")
        cmds.connectAttr(f"{joint_dic[k]}.jointOrient",f"{eulerToQuat}.inputRotate")
        quatInvert = cmds.createNode("quatInvert")
        cmds.connectAttr(f"{eulerToQuat}.outputQuat",f"{quatInvert}.inputQuat")
        cmds.connectAttr(f"{quatInvert}.outputQuat",f"{quatProd}.input2Quat")
        cmds.connectAttr(f"{quatToEuler}.outputRotate",f"{joint_dic[k]}.r")

        cmds.setAttr(f"{duplicate_joint_dic[k]}.segmentScaleCompensate",0)

        #設定の共有
        cmds.connectAttr(f"{duplicate_joint_dic[k]}.inheritsTransform",f"{joint_dic[k]}.inheritsTransform")
        cmds.connectAttr(f"{duplicate_joint_dic[k]}.rotateOrder",f"{joint_dic[k]}.rotateOrder")
        cmds.connectAttr(f"{duplicate_joint_dic[k]}.rotateAxis",f"{joint_dic[k]}.rotateAxis")
        cmds.connectAttr(f"{duplicate_joint_dic[k]}.rotatePivot",f"{joint_dic[k]}.rotatePivot")
        cmds.connectAttr(f"{duplicate_joint_dic[k]}.rotatePivotTranslate",f"{joint_dic[k]}.rotatePivotTranslate")
        cmds.connectAttr(f"{duplicate_joint_dic[k]}.rotateQuaternion",f"{joint_dic[k]}.rotateQuaternion")
        cmds.connectAttr(f"{duplicate_joint_dic[k]}.jointOrient",f"{joint_dic[k]}.jointOrient")
        cmds.connectAttr(f"{joint_dic[k]}.bindPose",f"{duplicate_joint_dic[k]}.bindPose")
        cmds.connectAttr(f"{duplicate_joint_dic[k]}.segmentScaleCompensate",f"{joint_dic[k]}.segmentScaleCompensate")

        cmds.connectAttr(f"{decomposeMatrix}.outputShear",f"{joint_dic[k]}.shear")

    return duplicate_joint_dic

def get_orientation(character_name:str):
    """
    回転軸決定用のオブジェクト取得

    Parameters
    ----------
        string character_name : 名前

    Returns
        なし
    """
    orientation_dic = {}
    root_grp = cmds.ls(f"Orient_C_{character_name}",typ="transform",l=True)[0]
    orient_obj_list = cmds.listRelatives(root_grp,f=False,c=True,ad=True)
    for k in joint_name:
        k_split=k.split("_")
        target_name=f"Orient_{k_split[0].upper()}_{joint_name[k][0]}"
        for i in orient_obj_list:
            if(i == target_name):
                orientation_dic[k]=cmds.ls(i,l=True)[0]
    
    
    cmds.setAttr(f"{root_grp}.v",0,lock=False,k=False)

    return orientation_dic

def get_pos(character_name:str):
    """
    位置決定用のオブジェクト取得

    Parameters
    ----------
        string character_name : 名前

    Returns
        なし
    """
    pos_dic = {}
    root_grp = cmds.ls(f"Position_C_{character_name}",typ="transform",l=True)[0]
    pos_obj_list = cmds.listRelatives(root_grp,f=False,c=True,ad=True)
    for i in pos_obj_list:
        fullpass=cmds.ls(i,l=True)[0]
        for clr in ["L","R"]:
            for name in ["ToesTip","Heel","FootInside","FootOutside","Sole"]:
                if(i==f"Position_{clr}_{name}"):
                    pos_dic[f"{clr.lower()}_{name.lower()}"]=fullpass

    cmds.setAttr(f"{root_grp}.v",0,lock=False,k=False)

    return pos_dic
