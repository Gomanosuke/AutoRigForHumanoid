from maya import cmds
from maya.api import OpenMaya
import importlib
from pathlib import Path
import json

#json読み込み
with open(f"{Path(__file__).resolve().parent}/joint_name.json", mode="rt", encoding="utf-8") as f:
    joint_name = json.load(f)

def do(textField_dic:dict,character_name:str,primary_axis:str):
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
    if(primary_axis==1):
        primary_axis_str = "X"
    elif(primary_axis==2):
        primary_axis_str = "Y"
    elif(primary_axis==3):
        primary_axis_str = "Z"
    check = check_textfield(textField_dic,character_name)
    check_bool = check[0]
    joint_dic=check[1]
    character_name = cmds.textField(character_name,q=True,tx=True)
    if(check_bool==True):
        joint_orientation(joint_dic,character_name,primary_axis_str)

def check_textfield(textField_dic:dict,character_name:str):
    """
    テキストフィールドのチェック

    Parameters
    ----------
        dictionary textfield : Joint名のテキストボックスが入った辞書
        string character_name : 名前を入れるテキストボックス

    Returns
    -------
        bool 続行していいか
        dict jointのフルパス辞書
    """
    bool = True
    joint_dic={}
    #名前
    name = cmds.textField(character_name,q=True,tx=True)
    if(name==""):
        cmds.warning("キャラクター名を入力してください")
        bool=False
    if("|" in name):
        cmds.warning("'|'は名前に利用できません")
        bool=False

    #joint
    for j in textField_dic:
        #複数オブジェないか
        name=cmds.textField(textField_dic[j],q=True,tx=True)
        joint_list=cmds.ls(name,typ="joint",l=True)
        if(len(joint_list)>1):
            cmds.warning(f"{j}が複数のオブジェクトに名前が一致します")
            bool=False
        if(len(joint_list)==0 and name!=""):
            cmds.warning(f"{name}は名前と一致するオブジェクトがありません")
            bool=False
        if(name!=""):
            joint_dic[j]=name

    return bool,joint_dic

def joint_orientation(joint_dic:dict,character_name:str,primary_axis:str):
    """
    回転軸決定

    Parameters
    ----------
        dictionary joint_dic: Jointのフルパス
        string character_name : 名前
        string primary_axis : 主軸

    Returns
        なし
    """
    #親グループ
    root_grp = cmds.group(em=True,n=f"Orient_C_{character_name}")
    cmds.setAttr(f"{root_grp}.t",lock=True)
    cmds.setAttr(f"{root_grp}.r",lock=True)
    cmds.setAttr(f"{root_grp}.s",lock=True)
    for k in joint_dic:
        k_split=k.split("_")
        name=f"Orient_{k_split[0].upper()}_{joint_name[k][0]}"
        matrix = cmds.xform(joint_dic[k] ,ws=True, matrix=True, q=True)
        nurvs=cmds.curve(name=name,degree=1,point=[(0, 0, 6), (0, 0, 0), (6, 0, 0), (4.5, 0, 1), (4.5, 0, 0)],knot=[0, 1, 2, 3, 4])
        cmds.parent(nurvs,root_grp,r=True)

        #color
        if(k_split[0]=="c"):
            color=[0,1,0]
        elif(k_split[0]=="l"):
            color=[0,0,1]
        elif(k_split[0]=="r"):
            color=[1,0,0]
        cmds.setAttr(f"{nurvs}.overrideEnabled", 1)
        cmds.setAttr(f"{nurvs}.overrideRGBColors", 1)  # RGBを有効に
        cmds.setAttr(f"{nurvs}.overrideColorRGB", color[0],color[1],color[2])  # R, G, B

        #主軸に回転
        rotate_matrix = [1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1]
        if(primary_axis=="Y"):
            rotate_matrix = [0,1,0,0,-1,0,0,0,0,0,1,0,0,0,0,1]
        if(primary_axis=="Z"):
            rotate_matrix = [0,0,1,0,0,1,0,0,-1,0,0,0,0,0,0,1]
        matrix=list(OpenMaya.MMatrix(rotate_matrix)*OpenMaya.MMatrix(matrix))
        cmds.xform(nurvs,ws=True,m=matrix)

        #回転とスケールロック
        cmds.setAttr(f"{nurvs}.s",*(1,1,1), type="double3")
        cmds.setAttr(f"{nurvs}.t",lock=True)
        cmds.setAttr(f"{nurvs}.s",lock=True)

