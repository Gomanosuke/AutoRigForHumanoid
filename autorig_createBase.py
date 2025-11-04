from maya import cmds
from maya.api import OpenMaya
import importlib
from pathlib import Path
import json

from . import autorig_preparation
importlib.reload(autorig_preparation)

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
        create_dummyHumanoid(joint_dic,character_name,root_grp)



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
        無し
    """
    root_grp = cmds.group(em=True,n=f"Grp_C_{character_name}DummyHumanoid")
    cmds.parent(root_grp,parent)
    cmds.setAttr(f"{root_grp}.t",lock=True)
    cmds.setAttr(f"{root_grp}.r",lock=True)
    cmds.setAttr(f"{root_grp}.s",lock=True)

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
        parent_obj = cmds.group(em=True,n=f"Grp_{k_split[0].upper()}_{joint_name[k][0]}Parent")
        cmds.parent(parent_obj,root_grp)
        matrix = cmds.xform(joint_dic_parent[k],q=True,ws=False,m=True)
        cmds.xform(joint_dic_parent[k],ws=False,m=(1.0,0.0,0.0,0.0, 0.0,1.0,0.0,0.0, 0.0,0.0,1.0,0.0, 0.0,0.0,0.0,1.0))
        cmds.xform(parent_obj,ws=True,m=cmds.xform(joint_dic_parent[k],q=True,ws=True,m=True))
        cmds.xform(joint_dic_parent[k],ws=False,m=matrix)
        joint_list = cmds.duplicate(joint_dic_parent[k],smartTransform=True,f=True)
        joint_list[0] = cmds.parent(joint_list[0],parent_obj)[0]
        joint_list[0] = cmds.ls(joint_list[0],l=True)[0]
        #Humanoid以外削除
        for i in joint_list:
            oldpath = f"{joint_dic_parent[k]}{i.split(joint_list[0])[-1]}"
            if(oldpath not in joint_dic.values()):
                #子供になかったら
                child_obj = cmds.listRelatives(joint_dic[k],f=True,c=True)
                for c in child_obj:
                    child_oldpath = f"{joint_dic_parent[k]}{c.split(joint_list[0])[-1]}"
                    if(child_oldpath not in joint_dic.values()):
                        cmds.delete(i)




