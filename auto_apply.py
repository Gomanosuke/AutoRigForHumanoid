from maya import cmds
from maya import OpenMaya
from pathlib import Path
import importlib
import json

#json読み込み
with open(f"{Path(__file__).resolve().parent}/joint_name.json", mode="rt", encoding="utf-8") as f:
    joint_name = json.load(f)

def auto(fullpath:bool, textfield:dict):
    """
    入力欄に自動入力

    Parameters
    ----------
        bool fullpath : Jointをフルパスで入れるかどうか
        dictionary textfield : Joint名のテキストボックスが入った辞書

    Returns
    -------
        無し
    """
    joint_list = cmds.ls(typ="joint",long=True)

    #各テキストフィールド毎
    for k in textfield:
        k_split = k.split("_")

        #名前から
        match_name = []
        match_condition = []
        for j in joint_list:
            for n in joint_name[k]:
                if(n.lower() in j.rsplit("|",maxsplit=1)[-1].lower()):
                    match_name.append(j)
        #名前が合うのが一つだけ
        if(len(match_name)==1):
            match_condition.append(match_name)
        #複数の時は合う座標だけ見てみる
        elif(len(match_name)>1):
            for j in match_name:
                pos = cmds.xform(j,ws=True,q=True,t=True)[0]
                if(k_split[0]=="c" and abs(round(pos,2))<0.01):
                    match_condition.append(j)
                if(k_split[0]=="l" and pos>0):
                    match_condition.append(j)
                if(k_split[0]=="r" and pos<0):
                    match_condition.append(j)
            #まだ複数ある時は一番親採用
            if(len(match_condition)>1):
                for j in match_condition:
                    parents = cmds.listRelatives(j,ap=True,f=True)
                    for p in parents:
                        for c in match_condition:
                            if(p==c):
                                match_condition.remove(j)
            #まだ複数ある時は一番名前が短いジョイント採用(Twistとかついてるやつ省く)
            if(len(match_condition)>1):
                joint = match_condition[0]
                for j in match_condition:
                    if(len(j)<len(joint)):
                        joint=j
                match_condition=[joint]

        if(len(match_condition)==1):
            fillTextfield(fullpath, textfield[k], match_condition[0])

def fillTextfield(fullpath:bool, textfield:str, joint:str):
    """
    入力欄に入力

    Parameters
    ----------
        bool fullpath : Jointをフルパスで入れるかどうか
        string textfield : Joint名のテキストボックス

    Returns
    -------
        無し
    """
    #correspond_jointをテキストフィールドに入れる
    if(fullpath==True):
        joint=cmds.ls(joint,l=True)[0]
    else:
        joint=cmds.ls(joint,l=False)[0].split("|")[-1]
    cmds.textField(textfield,edit=True,tx=joint)

def select(textfield:str):
    """
    jointを選択

    Parameters
    ----------
        string textfield : Joint名のテキストボックス

    Returns
    -------
        無し
    """
    object = cmds.textField(textfield,q=True,tx=True)
    object = cmds.ls(object)
    if(len(object)==0):
        cmds.warning("名前と一致するオブジェクトがありません")
    elif(len(object)>1):
        cmds.warning("複数のオブジェクトが名前と一致します")
    else:
        cmds.select(object[0],r=True)

def attach(textfield:str):
    """
    選択jointをテキストボックスにいれる

    Parameters
    ----------
        string textfield : Joint名のテキストボックス

    Returns
    -------
        無し
    """
    object = cmds.ls(selection=True,typ="joint",l=True)
    if(object==[]):
        cmds.warning("Jointを選択してください")
    else:
        cmds.textField(textfield,e=True,tx=object[0])
    cmds.select(cl=True)



