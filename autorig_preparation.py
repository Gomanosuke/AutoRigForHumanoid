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
        joint_pos(joint_dic,character_name)

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
    回転軸決定用のオブジェクト作成

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

def rotate_90(axis:str):
    """
    選択90°回転

    Parameters
    ----------
        str axis : "X""Y""Z"でそれぞれの軸回転

    Returns
    -------
        無し
    """
    if(axis=="X"):
        rotate_matrix = [1,0,0,0,0,0,1,0,0,-1,0,0,0,0,0,1]
    elif(axis=="Y"):
        rotate_matrix = [0,0,-1,0,0,1,0,0,1,0,0,0,0,0,0,1]
    elif(axis=="Z"):
        rotate_matrix = [0,1,0,0,-1,0,0,0,0,0,1,0,0,0,0,1]

    select_obj = cmds.ls(sl=True)
    for i in select_obj:
        matrix = cmds.xform(i, q=True, m=True, ws=False)
        matrix=list(OpenMaya.MMatrix(rotate_matrix)*OpenMaya.MMatrix(matrix))
        matrix = cmds.xform(i, m=matrix, ws=False)

def joint_pos(joint_dic:dict,character_name:str):
    """
    回転軸決定用のオブジェクト作成

    Parameters
    ----------
        dictionary joint_dic: Jointのフルパス
        string character_name : 名前

    Returns
        なし
    """
    if("l_foot" in joint_dic or "r_foot" in joint_dic):
        #親グループ
        root_grp = cmds.group(em=True,n=f"Position_C_{character_name}")
        cmds.setAttr(f"{root_grp}.t",lock=True)
        cmds.setAttr(f"{root_grp}.r",lock=True)
        cmds.setAttr(f"{root_grp}.s",lock=True)
        l_grp = cmds.group(em=True,n=f"FeetPosition_L_{character_name}")
        cmds.setAttr(f"{l_grp}.t",lock=True)
        cmds.setAttr(f"{l_grp}.r",lock=True)
        cmds.setAttr(f"{l_grp}.s",lock=True)
        cmds.parent(l_grp,root_grp,r=True)
        r_grp = cmds.group(em=True,n=f"FeetPosition_R_{character_name}")
        cmds.setAttr(f"{r_grp}.t",lock=True)
        cmds.setAttr(f"{r_grp}.r",lock=True)
        cmds.setAttr(f"{r_grp}.sx",-1)
        cmds.setAttr(f"{r_grp}.s",lock=True)
        cmds.parent(r_grp,root_grp,r=True)
        if("l_foot" in joint_dic):
            foot_pos(l_grp,"L",cmds.xform(joint_dic["l_foot"],q=True,ws=True,t=True))
        if("r_foot" in joint_dic):
            foot_pos(r_grp,"R",cmds.xform(joint_dic["r_foot"],q=True,ws=True,t=True))

def foot_pos(parent_grp:str,clr,translation):
    if(clr=="L"):
        scl=1
    elif(clr=="R"):
        scl=-1
        print(scl)
    nurvs_list = []
    for n in range(5):
        nurvs = cmds.curve(degree=1,point=[(0,3,0),(0,0,0),(3,0,0),(2,0,0),(1.827091,0.813473,0),(1.338261,1.48629,0),(0.618034,1.902113,0),(0,2,0)],knot=[0,1,2,3,4,5,6,7])
        nurvs_list.append(nurvs)
        cmds.setAttr(f"{nurvs}.overrideEnabled", 1)
        cmds.setAttr(f"{nurvs}.overrideRGBColors", 1)  # RGBを有効に
        cmds.setAttr(f"{nurvs}.overrideColorRGB", 0,1,1)  # R, G, B
        cmds.parent(nurvs,parent_grp,r=True)

    #つま先
    nurvs_list[0]=cmds.rename(nurvs_list[0],f"Position_{clr}_ToesTip")
    cmds.xform(nurvs_list[0],ws=True,t=(translation[0],0,translation[2]+10))
    cmds.setAttr(f"{nurvs_list[0]}.ry",90)
    cmds.makeIdentity(nurvs_list[0],a=True,t=False,r=True,s=False,n=False,pn=True)
    #つま先
    nurvs_list[1]=cmds.rename(nurvs_list[1],f"Position_{clr}_Heel")
    cmds.xform(nurvs_list[1],ws=True,t=(translation[0],0,translation[2]-5))
    cmds.setAttr(f"{nurvs_list[1]}.ry",-90)
    cmds.makeIdentity(nurvs_list[1],a=True,t=False,r=True,s=False,n=False,pn=True)
    #内側
    nurvs_list[2]=cmds.rename(nurvs_list[2],f"Position_{clr}_FootInside")
    cmds.xform(nurvs_list[2],ws=True,t=(translation[0],0,translation[2]+4))
    cmds.setAttr(f"{nurvs_list[2]}.tx",cmds.getAttr(f"{nurvs_list[2]}.tx")-4)
    cmds.makeIdentity(nurvs_list[2],a=True,t=False,r=True,s=False,n=False,pn=True)
    #外側
    nurvs_list[3]=cmds.rename(nurvs_list[3],f"Position_{clr}_FootOutside")
    cmds.xform(nurvs_list[3],ws=True,t=(translation[0],0,translation[2]+5))
    cmds.setAttr(f"{nurvs_list[3]}.tx",cmds.getAttr(f"{nurvs_list[3]}.tx")+4)
    cmds.setAttr(f"{nurvs_list[3]}.ry",180)
    cmds.makeIdentity(nurvs_list[3],a=True,t=False,r=True,s=False,n=False,pn=True)
    #裏側
    nurvs_list[4]=cmds.rename(nurvs_list[4],f"Position_{clr}_Sole")
    cmds.xform(nurvs_list[4],ws=True,t=(translation[0],0,translation[2]+7))
    cmds.setAttr(f"{nurvs_list[4]}.ry",90)
    cmds.makeIdentity(nurvs_list[4],a=True,t=False,r=True,s=False,n=False,pn=True)


