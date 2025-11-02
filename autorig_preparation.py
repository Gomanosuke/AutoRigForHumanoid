from maya import cmds
from maya import OpenMaya
import importlib

def do(textField_dic:dict,character_name:str):
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
    check = check_textfield(textField_dic,character_name)
    check_bool = check[0]
    joint_dic=check[1]

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
        joint_dic[j]=name

    return bool,joint_dic