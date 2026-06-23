from maya import cmds
from maya.api import OpenMaya
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
    
    if(check_bool==True):
        #親グループ
        root_grp = cmds.group(em=True,n=f"{character_name}_Rig")
        cmds.setAttr(f"{root_grp}.t",lock=True)
        cmds.setAttr(f"{root_grp}.r",lock=True)
        cmds.setAttr(f"{root_grp}.s",lock=True)
        humanoid_dummy_joint = create_dummyHumanoid(joint_dic,character_name,root_grp)
        orientation_dic = get_orientation(character_name)
        pos_dic=get_pos(character_name)
        autorig_createRig.init_createRig(humanoid_dummy_joint,character_name,root_grp,orientation_dic,pos_dic)

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

    #元のジョイントの正規化
    for key in joint_dic:
        joint = joint_dic[key]
        eulerToQuat01 = cmds.createNode("eulerToQuat")
        eulerToQuat02 = cmds.createNode("eulerToQuat")
        quatProd = cmds.createNode("quatProd")
        quatToEuler = cmds.createNode("quatToEuler")
        cmds.connectAttr(f"{joint}.r",f"{eulerToQuat01}.inputRotate")
        cmds.connectAttr(f"{joint}.rotateOrder",f"{eulerToQuat01}.inputRotateOrder")
        cmds.connectAttr(f"{joint}.jointOrient",f"{eulerToQuat02}.inputRotate")
        cmds.connectAttr(f"{eulerToQuat01}.outputQuat",f"{quatProd}.input1Quat")
        cmds.connectAttr(f"{eulerToQuat02}.outputQuat",f"{quatProd}.input2Quat")
        cmds.connectAttr(f"{quatProd}.outputQuat",f"{quatToEuler}.inputQuat")
        cmds.disconnectAttr(f"{quatProd}.outputQuat",f"{quatToEuler}.inputQuat")
        cmds.connectAttr(f"{quatToEuler}.outputRotate",f"{joint}.r")
        cmds.setAttr(f"{joint}.jointOrientX",0)
        cmds.setAttr(f"{joint}.jointOrientY",0)
        cmds.setAttr(f"{joint}.jointOrientZ",0)
        cmds.delete(eulerToQuat01)
        cmds.delete(eulerToQuat02)
        cmds.delete(quatToEuler)
        #アトリビュート作成
        cmds.addAttr(joint,ln="name",dt="string")
        cmds.setAttr(f"{joint}.name",key,typ="string")


    """
    #親にほかのjointないjoint取得
    joint_dic_parent = {}
    for k in joint_dic:
        exist_parent = False
        parent_obj = cmds.listRelatives(joint_dic[k],f=True,p=True)
        for i in parent_obj:
            if(i in joint_dic.values()):
                exist_parent=True
        if(exist_parent==False):
            joint_dic_parent[k]=joint_dic[k]
    
    #複製
    for k in joint_dic_parent:
        k_split=k.split("_")
        parent_obj = cmds.group(em=True,n=f"Grp_{k_split[0].upper()}_{joint_name[k][0]}_DummyParent")
        cmds.parent(parent_obj,root_grp)
        matrix = cmds.xform(joint_dic_parent[k],q=True,ws=False,m=True)
        cmds.xform(joint_dic_parent[k],ws=False,m=(1.0,0.0,0.0,0.0, 0.0,1.0,0.0,0.0, 0.0,0.0,1.0,0.0, 0.0,0.0,0.0,1.0))
        cmds.xform(parent_obj,ws=True,m=cmds.xform(joint_dic_parent[k],q=True,ws=True,m=True))
        cmds.xform(joint_dic_parent[k],ws=False,m=matrix)
        joint_list = cmds.duplicate(joint_dic_parent[k],smartTransform=True,f=True)
        duplicate_joint_dic = {}
        #Humanoid以外削除
        for i in joint_list:
            if(i!=joint_list[0]):
                old_path = f"{joint_dic_parent[k]}|{i.lstrip(joint_list[0])}"
                if(old_path not in list(joint_dic.values())):
                    #子供になかったら
                    child_obj = cmds.listRelatives(joint_dic[k],f=True,c=True,ad=True)
                    for c in child_obj:
                        child_old_path = f"{joint_dic_parent[k]}|{c.lstrip(joint_dic_parent[k])}"
                        if(child_old_path not in joint_dic.values()):
                            if(cmds.ls(i)!=[]):
                                cmds.delete(i)
                elif(cmds.ls(i,uid=True)!=[]):
                    #HumanoidJointだったら
                    duplicate_joint_dic[[k for k, v in joint_dic.items() if v == old_path][0]]=cmds.ls(i,uid=True)[0]
            else:
                duplicate_joint_dic[k]=cmds.ls(i,uid=True)[0]

        k_shortname = cmds.ls(joint_dic_parent[k],l=False)[0]
        duplicate_path=cmds.ls(duplicate_joint_dic[k],l=True)
        duplicate_joint_dic[k]=cmds.parent(joint_list[0],parent_obj,r=False)
        duplicate_joint_dic[k]=cmds.rename(duplicate_joint_dic[k],f"{k_shortname}_Dummy")
        duplicate_joint_dic[k]=cmds.ls(duplicate_joint_dic[k],l=True)[0]
        
        #辞書修正
        for j in duplicate_joint_dic:
            if(j!=k):
                name=cmds.ls(duplicate_joint_dic[j])[0]
                duplicate_joint_dic[j]=cmds.rename(name,f"{name.split('|')[-1]}_Dummy")
    """

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
    
    print(duplicate_joint_dic)

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
