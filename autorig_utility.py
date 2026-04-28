from maya import cmds
from maya.api import OpenMaya
from pathlib import Path
import json
import math


#json読み込み
with open(f"{Path(__file__).resolve().parent}/joint_name.json", mode="rt", encoding="utf-8") as f:
    joint_name = json.load(f)
with open(f"{Path(__file__).resolve().parent}/nurvs_shape.json", mode="rt", encoding="utf-8") as f:
    nurvs_shape = json.load(f)

def create_nurvs(name="", shape="", position=(0,0,0), rotate=(0,0,0), size=(1,1,1), pos_CLR="C"):
    """
    コントローラのナーブスを作成して返す

    Parameters
    ----------
        string name : オブジェクトの名前
        string shape : シェイプの形状 クラスに詳細
        (0,0,0) position : 位置
        (0,0,0) rotate : 回転
        (1,1,1) size : スケール
        string pos_CLR : "C", "L", "R"のどれかを指定して右左中央指定

    Returns
    -------
        string : 生成したナーブスのTransformNode

    コントローラー形状
    -------
        円1:circle, 正方形:scuare, 三角形:triangle, バツ:cross, 太いバツ:fatCross, 五角形:pentagon,
        六角形:hexagon1, ピラミッド:triangular, 立方体:cube, 六角柱:hexagon2, ダイヤ:dia1, 横長ダイヤ:dia2, コーン:cone
        単体矢印:arrorSingle, 双方向矢印:arrorDouble, 四方向矢印:arrorFour, 90回転:rot90, 180回転:rot180 UnityLOgo:unity
    """
    if(shape not in nurvs_shape):
        cmds.warning("存在しないシェイプ名です 代替としてcircleを生成します")
        shape="circle"

    degree=nurvs_shape[shape][0]
    points=nurvs_shape[shape][1]
    nurvs=cmds.curve(name=f"Con_{pos_CLR}_{name}",degree=degree,point=points,knot=[i for i in range(len(points))])

    #トランスフォーム変更
    cmds.setAttr(f"{nurvs}.translate", *position, type="double3")
    cmds.setAttr(f"{nurvs}.rotate", *rotate, type="double3")
    cmds.setAttr(f"{nurvs}.scale", *size, type="double3")
    cmds.makeIdentity(nurvs,apply=True,translate=True,rotate=True,scale=True)
    cmds.setAttr(f"{nurvs}.rotatePivot",*(0,0,0),type="double3")
    cmds.setAttr(f"{nurvs}.scalePivot",*(0,0,0),type="double3")
    cmds.setAttr(f"{nurvs}.v",keyable=False,channelBox=True)

    return nurvs

def create_controller(  con_name="",
                        parent_name="",
                        pos=(0,0,0),rot=(0,0,0),scl=(1,1,1),
                        pos_CLR="C",
                        con_shape="circle",
                        con_color=(0.5,0.5,0.5),
                        con_pos=(0,0,0),
                        con_rot=(0,0,0),
                        con_scl=(1,1,1),
                        con_pos_lock=(False,False,False), con_rot_lock=(False,False,False), con_scl_lock=(False,False,False),
                        uniform_scale=False,
                        con_advance_pos=(False,False,False), con_advance_rot=(False,False,False), con_advance_scl=(False,False,False),
                        drv_scale_offset=(1,1,1),setting="",connect_drv=True):
    """
    [Grp↳Con
        ↳Drv]構成のコントローラーの生成

    Parameters
    ----------
        string con_name : コントローラーの名前
        string parent_name : 親にするDAGオブジェのフルパス
        (x, y, z) pos : Grpのローカル位置
        (x, y, z) rot: Grpのローカル回転
        (x, y, z) scl : Grpのローカルスケール
        string pos_CLR : "C", "L", "R"のどれかを指定して右左中央指定
        string con_shape : コントローラーの形
        (r, g, b) con_color : 0~1でRGB
        (x, y, z) con_pos : コントローラーの位置
        (x, y, z) con_rot : コントローラーの回転
        (x, y, z) con_scl : コントローラーのスケール
        (bool,bool,bool) con_pos_lock : TrueになったTransLateをLock and Hideする
        (bool,bool,bool) con_rot_lock : TrueになったRotateをLock and Hideする
        (bool,bool,bool) con_scl_lock : TrueになったScaleをLock and Hideする
        bool uniform_scale : XでYZも操作する均一スケールにする
        (bool,bool,bool) con_advance_pos : TrueになったTransLateはadvance時のみ有効
        (bool,bool,bool) con_advance_rot : TrueになったRotateはadvance時のみ有効
        (bool,bool,bool) con_advance_scl : TrueになったScaleはadvance時のみ有効
        str setting : SettingObject
        bool connect_drv : FalseにするとDrvに何も接続しない

    Returns
    -------
        dict : keyが[("type","CLR","name")],valueがobjのフルパスの辞書

    コントローラー形状
    -------
        円1:circle, 正方形:scuare, 三角形:triangle, バツ:cross, 太いバツ:fatCross, 五角形:pentagon,
        六角形:hexagon1, ピラミッド:triangular, 立方体:cube, 六角柱:hexagon2, ダイヤ:dia1, 横長ダイヤ:dia2, コーン:cone
        単体矢印:arrorSingle, 双方向矢印:arrorDouble, 四方向矢印:arrorFour, 90回転:rot90, 180回転:rot180
    """

    obj_dic={}
    #名前の共通部分
    name=f"{pos_CLR}_{con_name}"
    #グループオブジェの作成
    GrpObj=cmds.group(em=True, name=f"Grp_{name}", parent=parent_name)
    cmds.setAttr(f"{GrpObj}.translate", *pos, type="double3")
    cmds.setAttr(f"{GrpObj}.rotate", *rot, type="double3")
    cmds.setAttr(f"{GrpObj}.scale", *scl, type="double3")
    obj_dic[("Grp",pos_CLR,con_name)]=cmds.ls(GrpObj,l=True)[0]
    cmds.setAttr( f"{GrpObj}.v", lock=True, keyable=False, channelBox=True)
    
    #コントローラ作成
    parent = GrpObj
    ConObj = create_nurvs(con_name,con_shape,con_pos,con_rot,con_scl,pos_CLR)
    ConObj = cmds.parent(ConObj,parent,r=True)[0]
    obj_dic[("Con",pos_CLR,con_name)]=cmds.ls(ConObj,l=True)[0]
    #color
    cmds.setAttr(f"{ConObj}.overrideEnabled", 1)
    cmds.setAttr(f"{ConObj}.overrideRGBColors", 1)  # RGBを有効に
    cmds.setAttr(f"{ConObj}.overrideColorRGB", con_color[0],con_color[1],con_color[2])  # R, G, B
    #コントローラーのアトリビュートのロックと非表示
    if(con_pos_lock[0]==True):cmds.setAttr( f"{ConObj}.tx", lock=True, keyable=False, channelBox=False)
    if(con_pos_lock[1]==True):cmds.setAttr( f"{ConObj}.ty", lock=True, keyable=False, channelBox=False)
    if(con_pos_lock[2]==True):cmds.setAttr( f"{ConObj}.tz", lock=True, keyable=False, channelBox=False)
    if(con_rot_lock[0]==True):cmds.setAttr( f"{ConObj}.rx", lock=True, keyable=False, channelBox=False)
    if(con_rot_lock[1]==True):cmds.setAttr( f"{ConObj}.ry", lock=True, keyable=False, channelBox=False)
    if(con_rot_lock[2]==True):cmds.setAttr( f"{ConObj}.rz", lock=True, keyable=False, channelBox=False)
    #回転順序のAttr必要か調べる
    if(con_rot_lock.count(True)<2):cmds.setAttr( f"{ConObj}.rotateOrder", keyable=True)

    if(uniform_scale == True):
        cmds.connectAttr(f"{ConObj}.sx",f"{ConObj}.sy")
        cmds.connectAttr(f"{ConObj}.sx",f"{ConObj}.sz")
        cmds.setAttr( f"{ConObj}.sy", lock=True, keyable=False, channelBox=False)
        cmds.setAttr( f"{ConObj}.sz", lock=True, keyable=False, channelBox=False)
    else:
        if(con_scl_lock[0]==True):cmds.setAttr( f"{ConObj}.sx", lock=True, keyable=False, channelBox=False)
        if(con_scl_lock[1]==True):cmds.setAttr( f"{ConObj}.sy", lock=True, keyable=False, channelBox=False)
        if(con_scl_lock[2]==True):cmds.setAttr( f"{ConObj}.sz", lock=True, keyable=False, channelBox=False)

    #Drv追加
    DrvObj=cmds.group(em=True, name=f"Drv_{name}", parent=GrpObj)
    obj_dic[("Drv",pos_CLR,con_name)]=DrvObj
    cmds.setAttr( f"{DrvObj}.v", lock=True, keyable=False, channelBox=True)
    cmds.connectAttr(f"{ConObj}.rotateOrder",f"{DrvObj}.rotateOrder")

    if(connect_drv==True):
        if(setting==""):
            cmds.connectAttr(f"{ConObj}.t",f"{DrvObj}.t")
            cmds.connectAttr(f"{ConObj}.r",f"{DrvObj}.r")
            cmds.connectAttr(f"{ConObj}.s",f"{DrvObj}.s")
        else:
            if(con_advance_pos[0]==True):
                floatComposite = cmds.createNode("floatComposite")
                cmds.setAttr(f"{floatComposite}.operation",2)
                cmds.setAttr(f"{floatComposite}.floatA",0)
                cmds.connectAttr(f"{ConObj}.tx",f"{floatComposite}.floatB")
                cmds.connectAttr(f"{setting}.advance",f"{floatComposite}.factor")
                cmds.connectAttr(f"{floatComposite}.outFloat",f"{DrvObj}.tx")
            else:cmds.connectAttr(f"{ConObj}.tx",f"{DrvObj}.tx")
            if(con_advance_pos[1]==True):
                floatComposite = cmds.createNode("floatComposite")
                cmds.setAttr(f"{floatComposite}.operation",2)
                cmds.setAttr(f"{floatComposite}.floatA",0)
                cmds.connectAttr(f"{ConObj}.ty",f"{floatComposite}.floatB")
                cmds.connectAttr(f"{setting}.advance",f"{floatComposite}.factor")
                cmds.connectAttr(f"{floatComposite}.outFloat",f"{DrvObj}.ty")
            else:cmds.connectAttr(f"{ConObj}.ty",f"{DrvObj}.ty")
            if(con_advance_pos[2]==True):
                floatComposite = cmds.createNode("floatComposite")
                cmds.setAttr(f"{floatComposite}.operation",2)
                cmds.setAttr(f"{floatComposite}.floatA",0)
                cmds.connectAttr(f"{ConObj}.tz",f"{floatComposite}.floatB")
                cmds.connectAttr(f"{setting}.advance",f"{floatComposite}.factor")
                cmds.connectAttr(f"{floatComposite}.outFloat",f"{DrvObj}.tz")
            else:cmds.connectAttr(f"{ConObj}.tz",f"{DrvObj}.tz")

            if(con_advance_rot[0]==True):
                floatComposite = cmds.createNode("floatComposite")
                cmds.setAttr(f"{floatComposite}.operation",2)
                cmds.setAttr(f"{floatComposite}.floatA",0)
                cmds.connectAttr(f"{ConObj}.rx",f"{floatComposite}.floatB")
                cmds.connectAttr(f"{setting}.advance",f"{floatComposite}.factor")
                cmds.connectAttr(f"{floatComposite}.outFloat",f"{DrvObj}.rx")
            else:cmds.connectAttr(f"{ConObj}.rx",f"{DrvObj}.rx")
            if(con_advance_rot[1]==True):
                floatComposite = cmds.createNode("floatComposite")
                cmds.setAttr(f"{floatComposite}.operation",2)
                cmds.setAttr(f"{floatComposite}.floatA",0)
                cmds.connectAttr(f"{ConObj}.ry",f"{floatComposite}.floatB")
                cmds.connectAttr(f"{setting}.advance",f"{floatComposite}.factor")
                cmds.connectAttr(f"{floatComposite}.outFloat",f"{DrvObj}.ry")
            else:cmds.connectAttr(f"{ConObj}.ry",f"{DrvObj}.ry")
            if(con_advance_rot[2]==True):
                floatComposite = cmds.createNode("floatComposite")
                cmds.setAttr(f"{floatComposite}.operation",2)
                cmds.setAttr(f"{floatComposite}.floatA",0)
                cmds.connectAttr(f"{ConObj}.rz",f"{floatComposite}.floatB")
                cmds.connectAttr(f"{setting}.advance",f"{floatComposite}.factor")
                cmds.connectAttr(f"{floatComposite}.outFloat",f"{DrvObj}.rz")
            else:cmds.connectAttr(f"{ConObj}.rz",f"{DrvObj}.rz")

            if(con_advance_scl[0]==True):
                floatComposite = cmds.createNode("floatComposite")
                cmds.setAttr(f"{floatComposite}.operation",2)
                cmds.setAttr(f"{floatComposite}.floatA",1)
                cmds.connectAttr(f"{ConObj}.sx",f"{floatComposite}.floatB")
                cmds.connectAttr(f"{setting}.advance",f"{floatComposite}.factor")
                if(drv_scale_offset[0]==1):
                    cmds.connectAttr(f"{floatComposite}.outFloat",f"{DrvObj}.sx")
                else:
                    floatMath = cmds.createNode("floatMath")
                    cmds.setAttr(F"{floatMath}.operation",2)
                    cmds.connectAttr(f"{floatComposite}.outFloat",f"{floatMath}.floatA")
                    cmds.setAttr(F"{floatMath}.floatB",drv_scale_offset[0])
                    cmds.connectAttr(f"{floatMath}.outFloat",f"{DrvObj}.sx")
            else:
                if(drv_scale_offset[0]==1):
                    cmds.connectAttr(f"{ConObj}.sx",f"{DrvObj}.sx")
                else:
                    floatMath = cmds.createNode("floatMath")
                    cmds.setAttr(F"{floatMath}.operation",2)
                    cmds.connectAttr(f"{ConObj}.sx",f"{floatMath}.floatA")
                    cmds.setAttr(F"{floatMath}.floatB",drv_scale_offset[1])
                    cmds.connectAttr(f"{floatMath}.outFloat",f"{DrvObj}.sy")
            if(con_advance_scl[1]==True):
                floatComposite = cmds.createNode("floatComposite")
                cmds.setAttr(f"{floatComposite}.operation",2)
                cmds.setAttr(f"{floatComposite}.floatA",1)
                cmds.connectAttr(f"{ConObj}.sy",f"{floatComposite}.floatB")
                cmds.connectAttr(f"{setting}.advance",f"{floatComposite}.factor")
                if(drv_scale_offset[1]==1):
                    cmds.connectAttr(f"{floatComposite}.outFloat",f"{DrvObj}.sy")
                else:
                    floatMath = cmds.createNode("floatMath")
                    cmds.setAttr(F"{floatMath}.operation",2)
                    cmds.connectAttr(f"{floatComposite}.outFloat",f"{floatMath}.floatA")
                    cmds.setAttr(F"{floatMath}.floatB",drv_scale_offset[1])
                    cmds.connectAttr(f"{floatMath}.outFloat",f"{DrvObj}.sy")
            else:
                if(drv_scale_offset[1]==1):
                    cmds.connectAttr(f"{ConObj}.sy",f"{DrvObj}.sy")
                else:
                    floatMath = cmds.createNode("floatMath")
                    cmds.setAttr(F"{floatMath}.operation",2)
                    cmds.connectAttr(f"{ConObj}.sy",f"{floatMath}.floatA")
                    cmds.setAttr(F"{floatMath}.floatB",drv_scale_offset[1])
                    cmds.connectAttr(f"{floatMath}.outFloat",f"{DrvObj}.sy")
            if(con_advance_scl[2]==True):
                floatComposite = cmds.createNode("floatComposite")
                cmds.setAttr(f"{floatComposite}.operation",2)
                cmds.setAttr(f"{floatComposite}.floatA",1)
                cmds.connectAttr(f"{ConObj}.sz",f"{floatComposite}.floatB")
                cmds.connectAttr(f"{setting}.advance",f"{floatComposite}.factor")
                if(drv_scale_offset[2]==1):
                    cmds.connectAttr(f"{floatComposite}.outFloat",f"{DrvObj}.sz")
                else:
                    floatMath = cmds.createNode("floatMath")
                    cmds.setAttr(F"{floatMath}.operation",2)
                    cmds.connectAttr(f"{floatComposite}.outFloat",f"{floatMath}.floatA")
                    cmds.setAttr(F"{floatMath}.floatB",drv_scale_offset[2])
                    cmds.connectAttr(f"{floatMath}.outFloat",f"{DrvObj}.sz")
            else:
                if(drv_scale_offset[2]==1):
                    cmds.connectAttr(f"{ConObj}.sz",f"{DrvObj}.sz")
                else:
                    floatMath = cmds.createNode("floatMath")
                    cmds.setAttr(F"{floatMath}.operation",2)
                    cmds.connectAttr(f"{ConObj}.sz",f"{floatMath}.floatA")
                    cmds.setAttr(F"{floatMath}.floatB",drv_scale_offset[2])
                    cmds.connectAttr(f"{floatMath}.outFloat",f"{DrvObj}.sz")

    return obj_dic



def layerd_scale(parent_grp:str, parent_drv:str, obj_grp:str, obj_con:str):
    """
    親のスケールを引き継ぐか選べるようにする

    Parameters
    ----------
        string parent_grp : 親のGrp
        string parent_drv : 親のDrv
        string obj_grp : コントローラーのGrp
        string obj_con : コントローラーのCon
        string obj_drv : コントローラーのDrv

    Returns
    -------
        (multMatrix1, multMatrix2, multMatrix3, multMatrix4, decomposeMatrix1, decomposeMatrix2, decomposeMatrix3, decomposeMatrix4, composeMatrix1, composeMatrix2, composeMatrix3, blendColor)
    """
    #スケーリング
    multMatrix1 = cmds.createNode("multMatrix")
    multMatrix2 = cmds.createNode("multMatrix")
    multMatrix3 = cmds.createNode("multMatrix")
    multMatrix4 = cmds.createNode("multMatrix")
    decomposeMatrix1 = cmds.createNode("decomposeMatrix")
    decomposeMatrix2 = cmds.createNode("decomposeMatrix")
    decomposeMatrix3 = cmds.createNode("decomposeMatrix")
    decomposeMatrix4 = cmds.createNode("decomposeMatrix")
    composeMatrix1 = cmds.createNode("composeMatrix")
    composeMatrix2 = cmds.createNode("composeMatrix")
    composeMatrix3 = cmds.createNode("composeMatrix")
    blendColor = cmds.createNode("blendColors")
    #アトリビュート作成
    cmds.addAttr(obj_con,ln="LayeredScale",at="double",min=0,max=1,dv=0)
    cmds.setAttr(f"{obj_con}.LayeredScale",1,k=True)
    cmds.connectAttr(f"{obj_con}.LayeredScale",f"{blendColor}.blender",f=True)
    #計算
    cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
    cmds.setAttr(f"{composeMatrix2}.useEulerRotation",0)
    cmds.setAttr(f"{composeMatrix3}.useEulerRotation",0)
    cmds.connectAttr(f"{parent_drv}.worldMatrix[0]",f"{decomposeMatrix1}.inputMatrix",f=True)
    cmds.connectAttr(f"{parent_grp}.worldMatrix[0]",f"{decomposeMatrix2}.inputMatrix",f=True)
    cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{blendColor}.color1",f=True)
    cmds.connectAttr(f"{decomposeMatrix2}.outputScale",f"{blendColor}.color2",f=True)
    cmds.connectAttr(f"{blendColor}.output",f"{composeMatrix1}.inputScale",f=True)
    cmds.connectAttr(f"{obj_con}.inverseMatrix",f"{multMatrix1}.matrixIn[0]",f=True)
    cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix1}.matrixIn[1]",f=True)
    cmds.connectAttr(f"{obj_con}.matrix",f"{multMatrix1}.matrixIn[2]",f=True)
    cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{obj_con}.offsetParentMatrix",f=True)
    cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{composeMatrix2}.inputQuat",f=True)
    cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{composeMatrix2}.inputTranslate",f=True)
    cmds.connectAttr(f"{obj_grp}.matrix",f"{multMatrix2}.matrixIn[0]",f=True)
    cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix2}.matrixIn[1]",f=True)
    cmds.connectAttr(f"{obj_grp}.matrix",f"{multMatrix3}.matrixIn[0]",f=True)
    cmds.connectAttr(f"{parent_drv}.worldMatrix[0]",f"{multMatrix3}.matrixIn[1]",f=True)
    cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{decomposeMatrix3}.inputMatrix",f=True)
    cmds.connectAttr(f"{multMatrix3}.matrixSum",f"{decomposeMatrix4}.inputMatrix",f=True)
    cmds.connectAttr(f"{decomposeMatrix3}.outputQuat",f"{composeMatrix3}.inputQuat",f=True)
    cmds.connectAttr(f"{decomposeMatrix4}.outputTranslate",f"{composeMatrix3}.inputTranslate",f=True)
    cmds.connectAttr(f"{obj_grp}.inverseMatrix",f"{multMatrix4}.matrixIn[0]",f=True)
    cmds.connectAttr(f"{composeMatrix3}.outputMatrix",f"{multMatrix4}.matrixIn[1]",f=True)
    cmds.connectAttr(f"{multMatrix4}.matrixSum",f"{obj_grp}.offsetParentMatrix",f=True)

def layerd_scale_rotate(parent_grp:str, parent_drv:str, obj_grp:str, obj_con:str):
    """
    親のスケールと回転を引き継ぐか選べるようにする

    Parameters
    ----------
        string parent_grp : 親のGrp
        string parent_drv : 親のDrv
        string obj_grp : コントローラーのGrp
        string obj_con : コントローラーのCon
        string obj_drv : コントローラーのDrv

    Returns
    -------
        (multMatrix1, multMatrix2, multMatrix3, multMatrix4, decomposeMatrix1, decomposeMatrix2, decomposeMatrix3, decomposeMatrix4, composeMatrix1, composeMatrix2, composeMatrix3, blendColor)
    """
    #スケーリング
    multMatrix1 = cmds.createNode("multMatrix")
    multMatrix2 = cmds.createNode("multMatrix")
    multMatrix3 = cmds.createNode("multMatrix")
    multMatrix4 = cmds.createNode("multMatrix")
    decomposeMatrix1 = cmds.createNode("decomposeMatrix")
    decomposeMatrix2 = cmds.createNode("decomposeMatrix")
    decomposeMatrix3 = cmds.createNode("decomposeMatrix")
    decomposeMatrix4 = cmds.createNode("decomposeMatrix")
    composeMatrix1 = cmds.createNode("composeMatrix")
    composeMatrix2 = cmds.createNode("composeMatrix")
    composeMatrix3 = cmds.createNode("composeMatrix")
    blendColor = cmds.createNode("blendColors")
    quatSlerp = cmds.createNode("quatSlerp")
    #アトリビュート作成
    cmds.addAttr(obj_con,ln="LayeredRotate",at="double",min=0,max=1,dv=0)
    cmds.setAttr(f"{obj_con}.LayeredRotate",1,k=True)
    cmds.connectAttr(f"{obj_con}.LayeredRotate",f"{quatSlerp}.inputT",f=True)
    cmds.addAttr(obj_con,ln="LayeredScale",at="double",min=0,max=1,dv=0)
    cmds.setAttr(f"{obj_con}.LayeredScale",1,k=True)
    cmds.connectAttr(f"{obj_con}.LayeredScale",f"{blendColor}.blender",f=True)
    #計算
    cmds.setAttr(f"{composeMatrix1}.useEulerRotation",0)
    cmds.setAttr(f"{composeMatrix2}.useEulerRotation",0)
    cmds.setAttr(f"{composeMatrix3}.useEulerRotation",0)
    cmds.connectAttr(f"{parent_drv}.worldMatrix[0]",f"{decomposeMatrix1}.inputMatrix",f=True)
    cmds.connectAttr(f"{parent_grp}.worldMatrix[0]",f"{decomposeMatrix2}.inputMatrix",f=True)
    cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{blendColor}.color1",f=True)
    cmds.connectAttr(f"{decomposeMatrix2}.outputScale",f"{blendColor}.color2",f=True)
    cmds.connectAttr(f"{blendColor}.output",f"{composeMatrix1}.inputScale",f=True)
    cmds.connectAttr(f"{obj_con}.inverseMatrix",f"{multMatrix1}.matrixIn[0]",f=True)
    cmds.connectAttr(f"{composeMatrix1}.outputMatrix",f"{multMatrix1}.matrixIn[1]",f=True)
    cmds.connectAttr(f"{obj_con}.matrix",f"{multMatrix1}.matrixIn[2]",f=True)
    cmds.connectAttr(f"{multMatrix1}.matrixSum",f"{obj_con}.offsetParentMatrix",f=True)
    cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{composeMatrix2}.inputTranslate",f=True)
    cmds.connectAttr(f"{obj_grp}.matrix",f"{multMatrix2}.matrixIn[0]",f=True)
    cmds.connectAttr(f"{composeMatrix2}.outputMatrix",f"{multMatrix2}.matrixIn[1]",f=True)
    cmds.connectAttr(f"{obj_grp}.matrix",f"{multMatrix3}.matrixIn[0]",f=True)
    cmds.connectAttr(f"{parent_drv}.worldMatrix[0]",f"{multMatrix3}.matrixIn[1]",f=True)
    cmds.connectAttr(f"{multMatrix2}.matrixSum",f"{decomposeMatrix3}.inputMatrix",f=True)
    cmds.connectAttr(f"{multMatrix3}.matrixSum",f"{decomposeMatrix4}.inputMatrix",f=True)
    cmds.connectAttr(f"{decomposeMatrix3}.outputQuat",f"{composeMatrix3}.inputQuat",f=True)
    cmds.connectAttr(f"{decomposeMatrix4}.outputTranslate",f"{composeMatrix3}.inputTranslate",f=True)
    cmds.connectAttr(f"{obj_grp}.inverseMatrix",f"{multMatrix4}.matrixIn[0]",f=True)
    cmds.connectAttr(f"{composeMatrix3}.outputMatrix",f"{multMatrix4}.matrixIn[1]",f=True)
    cmds.connectAttr(f"{multMatrix4}.matrixSum",f"{obj_grp}.offsetParentMatrix",f=True)

    cmds.connectAttr(f"{decomposeMatrix1}.outputQuat",f"{quatSlerp}.input2Quat")
    cmds.connectAttr(f"{decomposeMatrix2}.outputQuat",f"{quatSlerp}.input1Quat")
    cmds.connectAttr(f"{quatSlerp}.outputQuat",f"{composeMatrix2}.inputQuat",f=True)

def switch_parent(dvn_grp:str, dvn_con:str, posA="",posB="",rotA="",rotB="",sclA="",sclB="",postScl=False):
    """
    移動回転スケール、親をそれぞれ２つのオブジェからスイッチする
    スイッチしない場合はAのみ入力

    Parameters
    ----------
        string posA : 位置の親A
        string posB : 位置の親B
        string rotA : 回転の親A
        string rotB : 回転の親B
        string sclA : スケールの親A
        string sclB : スケールの親B
        string dvn_grp : コントローラーのGrp
        string dvn_con : コントローラーのCon
        bool postScl : スケールをポスト処理にしてシアが発生しないようにする

    Returns
    -------
        string grpのoffsetParentMatrixに接続されるもの
    """

    dvn_matrix = cmds.xform(dvn_con,q=True,ws=True,m=True)
    outputComposeMatrix = cmds.createNode("composeMatrix")
    cmds.setAttr(f"{outputComposeMatrix}.useEulerRotation",0)

    #位置
    posA_matrix = cmds.xform(posA,q=True,ws=True,m=True)
    cmds.addAttr(dvn_con,ln="posAMatrix",at="matrix")
    matrix = OpenMaya.MMatrix(dvn_matrix)*OpenMaya.MMatrix(posA_matrix).inverse()
    matrix = list(matrix)
    cmds.setAttr(f"{dvn_con}.posAMatrix",matrix,typ="matrix",l=True)
    multMatrixA = cmds.createNode("multMatrix")
    decomposeMatrixA = cmds.createNode("decomposeMatrix")
    cmds.connectAttr(f"{dvn_con}.posAMatrix",f"{multMatrixA}.matrixIn[0]")
    cmds.connectAttr(f"{posA}.worldMatrix[0]",f"{multMatrixA}.matrixIn[1]")
    cmds.connectAttr(f"{multMatrixA}.matrixSum",f"{decomposeMatrixA}.inputMatrix")
    if(posB==""):
        cmds.connectAttr(f"{decomposeMatrixA}.outputTranslate",f"{outputComposeMatrix}.inputTranslate")
    else:
        posB_matrix = cmds.xform(posB,q=True,ws=True,m=True)
        cmds.addAttr(dvn_con,ln="posBMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(dvn_matrix)*OpenMaya.MMatrix(posB_matrix).inverse()
        matrix = list(matrix)
        cmds.setAttr(f"{dvn_con}.posBMatrix",matrix,typ="matrix",l=True)
        multMatrixB = cmds.createNode("multMatrix")
        decomposeMatrixB = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{dvn_con}.posBMatrix",f"{multMatrixB}.matrixIn[0]")
        cmds.connectAttr(f"{posB}.worldMatrix[0]",f"{multMatrixB}.matrixIn[1]")
        cmds.connectAttr(f"{multMatrixB}.matrixSum",f"{decomposeMatrixB}.inputMatrix")

        blendColors = cmds.createNode("blendColors")
        cmds.connectAttr(f"{decomposeMatrixA}.outputTranslate",f"{blendColors}.color2")
        cmds.connectAttr(f"{decomposeMatrixB}.outputTranslate",f"{blendColors}.color1")

        cmds.addAttr(dvn_con,ln="posParent",at="float",max=1,min=0,k=True)
        cmds.connectAttr(f"{dvn_con}.posParent",f"{blendColors}.blender")
        cmds.connectAttr(f"{blendColors}.output",f"{outputComposeMatrix}.inputTranslate")
    cmds.setAttr(f"{dvn_grp}.t",0,0,0)

    #回転
    rotA_matrix = cmds.xform(rotA,q=True,ws=True,m=True)
    cmds.addAttr(dvn_con,ln="rotAMatrix",at="matrix")
    matrix = OpenMaya.MMatrix(dvn_matrix)*OpenMaya.MMatrix(rotA_matrix).inverse()
    matrix = list(matrix)
    cmds.setAttr(f"{dvn_con}.rotAMatrix",matrix,typ="matrix",l=True)
    multMatrixA = cmds.createNode("multMatrix")
    decomposeMatrixA = cmds.createNode("decomposeMatrix")
    cmds.connectAttr(f"{dvn_con}.rotAMatrix",f"{multMatrixA}.matrixIn[0]")
    cmds.connectAttr(f"{rotA}.worldMatrix[0]",f"{multMatrixA}.matrixIn[1]")
    cmds.connectAttr(f"{multMatrixA}.matrixSum",f"{decomposeMatrixA}.inputMatrix")
    if(rotB==""):
        cmds.connectAttr(f"{decomposeMatrixA}.outputQuat",f"{outputComposeMatrix}.inputQuat")
    else:
        rotB_matrix = cmds.xform(rotB,q=True,ws=True,m=True)
        cmds.addAttr(dvn_con,ln="rotBMatrix",at="matrix")
        matrix = OpenMaya.MMatrix(dvn_matrix)*OpenMaya.MMatrix(rotB_matrix).inverse()
        matrix = list(matrix)
        cmds.setAttr(f"{dvn_con}.rotBMatrix",matrix,typ="matrix",l=True)
        multMatrixB = cmds.createNode("multMatrix")
        decomposeMatrixB = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{dvn_con}.rotBMatrix",f"{multMatrixB}.matrixIn[0]")
        cmds.connectAttr(f"{rotB}.worldMatrix[0]",f"{multMatrixB}.matrixIn[1]")
        cmds.connectAttr(f"{multMatrixB}.matrixSum",f"{decomposeMatrixB}.inputMatrix")

        quatSlerp=cmds.createNode("quatSlerp")
        cmds.connectAttr(f"{decomposeMatrixA}.outputQuat",f"{quatSlerp}.input1Quat")
        cmds.connectAttr(f"{decomposeMatrixB}.outputQuat",f"{quatSlerp}.input2Quat")

        cmds.addAttr(dvn_con,ln="rotParent",at="float",max=1,min=0,k=True)
        cmds.connectAttr(f"{dvn_con}.rotParent",f"{quatSlerp}.inputT")
        cmds.connectAttr(f"{quatSlerp}.outputQuat",f"{outputComposeMatrix}.inputQuat")
    cmds.setAttr(f"{dvn_grp}.r",0,0,0)

    #スケール
    decomposeMatrixA = cmds.createNode("decomposeMatrix")
    cmds.connectAttr(f"{sclA}.worldMatrix[0]",f"{decomposeMatrixA}.inputMatrix")
    outputScale=""
    if(sclB==""):
        outputScale = f"{decomposeMatrixA}.outputScale"
    else:
        decomposeMatrixB = cmds.createNode("decomposeMatrix")
        cmds.connectAttr(f"{sclB}.worldMatrix[0]",f"{decomposeMatrixB}.inputMatrix")

        blendColors = cmds.createNode("blendColors")
        cmds.connectAttr(f"{decomposeMatrixA}.outputScale",f"{blendColors}.color2")
        cmds.connectAttr(f"{decomposeMatrixB}.outputScale",f"{blendColors}.color1")

        cmds.addAttr(dvn_con,ln="sclParent",at="float",max=1,min=0,k=True)
        cmds.connectAttr(f"{dvn_con}.sclParent",f"{blendColors}.blender")
        outputScale = f"{blendColors}.output"
    cmds.setAttr(f"{dvn_grp}.s",1,1,1)

    if(postScl==False):
        cmds.connectAttr(outputScale,f"{outputComposeMatrix}.inputScale")
        cmds.connectAttr(f"{outputComposeMatrix}.outputMatrix",f"{dvn_grp}.offsetParentMatrix",f=True)

    else:
        scaleComposeMatrix = cmds.createNode("composeMatrix")
        cmds.connectAttr(outputScale,f"{scaleComposeMatrix}.inputScale")
        multMatrix = cmds.createNode("multMatrix")
        cmds.connectAttr(f"{dvn_con}.inverseMatrix",f"{multMatrix}.matrixIn[0]")
        cmds.connectAttr(f"{scaleComposeMatrix}.outputMatrix",f"{multMatrix}.matrixIn[1]")
        cmds.connectAttr(f"{dvn_con}.matrix",f"{multMatrix}.matrixIn[2]")
        cmds.connectAttr(f"{outputComposeMatrix}.outputMatrix",f"{multMatrix}.matrixIn[3]")
        cmds.connectAttr(f"{multMatrix}.matrixSum",f"{dvn_grp}.offsetParentMatrix",f=True)

    

def postScale_parent(dvn_grp:str, dvn_con:str ,drv_drv:str):
    """
    シアの発生しない親子関係を作成

    Parameters
    ----------
        string dvn_grp : コントローラーのGrp
        string dvn_con : コントローラーのCon
        string drv_drv : 親ののDrv

    Returns
    -------
        無し
    """
    decomposeMatrix = cmds.createNode("decomposeMatrix")
    scaleComposeMatrix = cmds.createNode("composeMatrix")
    posRotComposeMatrix = cmds.createNode("composeMatrix")
    cmds.connectAttr(f"{drv_drv}.worldMatrix[0]",f"{decomposeMatrix}.inputMatrix")
    cmds.setAttr(f"{scaleComposeMatrix}.useEulerRotation",0)
    cmds.setAttr(f"{posRotComposeMatrix}.useEulerRotation",0)
    cmds.connectAttr(f"{decomposeMatrix}.outputScale",f"{scaleComposeMatrix}.inputScale")
    cmds.connectAttr(f"{decomposeMatrix}.outputQuat",f"{posRotComposeMatrix}.inputQuat")
    cmds.connectAttr(f"{decomposeMatrix}.outputTranslate",f"{posRotComposeMatrix}.inputTranslate")

    multMatrix = cmds.createNode("multMatrix")
    cmds.connectAttr(f"{dvn_con}.inverseMatrix",f"{multMatrix}.matrixIn[0]")
    cmds.connectAttr(f"{scaleComposeMatrix}.outputMatrix",f"{multMatrix}.matrixIn[1]")
    cmds.connectAttr(f"{dvn_con}.matrix",f"{multMatrix}.matrixIn[2]")
    cmds.connectAttr(f"{posRotComposeMatrix}.outputMatrix",f"{multMatrix}.matrixIn[3]")
    cmds.connectAttr(f"{multMatrix}.matrixSum",f"{dvn_grp}.offsetParentMatrix",f=True)

def matrix_constraint(Drv_Obj:str,Dvn_Obj:str):
    """
    オフセット付きで行列コンストレイン WorldBindMatrixアトリビュート作成

    Parameters
    ----------
    string Drv_Obj : 接続元
    string Dvn_Obj : 接続先

    Returns
    -------
        無し
    """
    #アトリビュート作成
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
    cmds.connectAttr(f"{decomposeMatrix1}.outputTranslate",f"{Dvn_Obj}.t",f=True)
    cmds.connectAttr(f"{decomposeMatrix1}.outputRotate",f"{Dvn_Obj}.r",f=True)
    cmds.connectAttr(f"{decomposeMatrix1}.outputScale",f"{Dvn_Obj}.s",f=True)
    cmds.connectAttr(f"{decomposeMatrix1}.outputShear",f"{Dvn_Obj}.shear",f=True)
    

def create_controller_legacy(  con_name="",
                        parent_name="",
                        pos=(0,0,0),rot=(0,0,0),scl=(1,1,1),
                        pos_CLR="C",
                        con_shape="circle",
                        con_color=(0.5,0.5,0.5),
                        con_position=(0,0,0),
                        con_rotate=(0,0,0),
                        con_size=(1,1,1),
                        con_pos_lock=(True,True,True), con_rot_lock=(True,True,True), con_scl_lock=(True,True,True), uniform_scale=False,
                        create_drv = True,
                        dvn_count = 0,
                        scale_unable=False,
                        pos_unable=False,
                        rot_unable=(False,False,False),
                        unity_setting="",
                        keyable_rotateOrder=True):
    """
    [グループ-コントローラー-ドライバー]構成のコントローラーの生成

    Parameters
    ----------
        string con_name : コントローラーの名前
        string parent_name : 親にするDAGオブジェのフルパス
        (x, y, z) pos : Grpのローカル位置
        (x, y, z) rot: Grpのローカル回転
        (x, y, z) scl : Grpのローカルスケール
        string pos_CLR : "C", "L", "R"のどれかを指定して右左中央指定
        string con_shape : コントローラーの形
        (r, g, b) con_color : 0~1でRGB
        (x, y, z) con_position : コントローラーの位置
        (x, y, z) con_rotate : コントローラーの回転
        (x, y, z) con_size : コントローラーのスケール
        (bool,bool,bool) con_pos_lock : FalseになったTransLateをLock and Hideする
        (bool,bool,bool) con_rot_lock : FalseになったRotateをLock and Hideする
        (bool,bool,bool) con_scl_lock : FalseになったScaleをLock and Hideする
        bool uniform_scale : XでYZも操作する均一スケールにする
        bool create_drv : DriverObjectを作成するかどうか
        int dvn_count : DvnObjの数
        bool scale_unable : Unity用にスケールをロックする
        bool pos_unable : Unity用に移動をロックする
        str unity_setting : UnitySettingObject

    Returns
    -------
        dict : keyが[("type","CLR","name",count(Dvnのみ);int)],valueがobjのフルパスの辞書


    コントローラー形状
    -------
        円1:circle, 正方形:scuare, 三角形:triangle, バツ:cross, 太いバツ:fatCross, 五角形:pentagon,
        六角形:hexagon1, ピラミッド:triangular, 立方体:cube, 六角柱:hexagon2, ダイヤ:dia1, 横長ダイヤ:dia2, コーン:cone
        単体矢印:arrorSingle, 双方向矢印:arrorDouble, 四方向矢印:arrorFour, 90回転:rot90, 180回転:rot180
    """
    obj_dic={}
    #名前の共通部分
    name=f"{pos_CLR}_{con_name}"
    #グループオブジェの作成
    GrpObj=cmds.group(em=True, name=f"Grp_{name}", parent=parent_name)
    cmds.setAttr(f"{GrpObj}.translate", *pos, type="double3")
    cmds.setAttr(f"{GrpObj}.rotate", *rot, type="double3")
    cmds.setAttr(f"{GrpObj}.scale", *scl, type="double3")
    obj_dic[("Grp",pos_CLR,con_name)]=cmds.ls(GrpObj,l=True)[0]
    cmds.setAttr( f"{GrpObj}.v", lock=True, keyable=False, channelBox=True)
    
    #Dvn追加
    for n in range(dvn_count):
        parent=GrpObj
        if(n!=0):
            parent=obj_dic[("Dvn",pos_CLR,con_name,n)]
        DvnObj=cmds.group(em=True, name=f"Dvn_{name}_{n+1}", parent=parent)
        obj_dic[("Dvn",pos_CLR,con_name,n+1)]=cmds.ls(DvnObj,l=True)[0]
        cmds.setAttr( f"{DvnObj}.v", lock=True, keyable=False, channelBox=True)
    
    #コントローラ作成
    parent = GrpObj
    if(dvn_count!=0):
        parent = obj_dic[("Dvn",pos_CLR,con_name,dvn_count)]
    nurvs = create_nurvs(con_name,con_shape,con_position,con_rotate,con_size,pos_CLR)
    nurvs = cmds.parent(nurvs,parent,r=True)[0]
    obj_dic[("Con",pos_CLR,con_name)]=cmds.ls(nurvs,l=True)[0]
    #color
    cmds.setAttr(f"{nurvs}.overrideEnabled", 1)
    cmds.setAttr(f"{nurvs}.overrideRGBColors", 1)  # RGBを有効に
    cmds.setAttr(f"{nurvs}.overrideColorRGB", con_color[0],con_color[1],con_color[2])  # R, G, B
    #コントローラーのアトリビュートのロックと非表示
    if(keyable_rotateOrder==True):cmds.setAttr( f"{nurvs}.rotateOrder", keyable=True)
    if(con_pos_lock[0]==False):cmds.setAttr( f"{nurvs}.tx", lock=True, keyable=False, channelBox=False)
    if(con_pos_lock[1]==False):cmds.setAttr( f"{nurvs}.ty", lock=True, keyable=False, channelBox=False)
    if(con_pos_lock[2]==False):cmds.setAttr( f"{nurvs}.tz", lock=True, keyable=False, channelBox=False)
    if(con_rot_lock[0]==False):cmds.setAttr( f"{nurvs}.rx", lock=True, keyable=False, channelBox=False)
    if(con_rot_lock[1]==False):cmds.setAttr( f"{nurvs}.ry", lock=True, keyable=False, channelBox=False)
    if(con_rot_lock[2]==False):cmds.setAttr( f"{nurvs}.rz", lock=True, keyable=False, channelBox=False)

    if(uniform_scale == True):
        cmds.connectAttr(f"{nurvs}.sx",f"{nurvs}.sy")
        cmds.connectAttr(f"{nurvs}.sx",f"{nurvs}.sz")
        cmds.setAttr( f"{nurvs}.sy", lock=True, keyable=False, channelBox=False)
        cmds.setAttr( f"{nurvs}.sz", lock=True, keyable=False, channelBox=False)
    else:
        if(con_scl_lock[0]==False):cmds.setAttr( f"{nurvs}.sx", lock=True, keyable=False, channelBox=False)
        if(con_scl_lock[1]==False):cmds.setAttr( f"{nurvs}.sy", lock=True, keyable=False, channelBox=False)
        if(con_scl_lock[2]==False):cmds.setAttr( f"{nurvs}.sz", lock=True, keyable=False, channelBox=False)

    #Drv追加
    if(create_drv==True):
        DrvObj=cmds.group(em=True, name=f"Drv_{name}", parent=nurvs)
        obj_dic[("Drv",pos_CLR,con_name)]=DrvObj
        cmds.setAttr( f"{DrvObj}.v", lock=True, keyable=False, channelBox=True)

    #Unityのコントローラー無効化
    if(scale_unable == True or pos_unable == True and create_drv==True):
        if(pos_unable == True):
            move_blendColor = cmds.shadingNode("blendColors",asUtility=True)
            cmds.setAttr(f"{move_blendColor}.color2",*(0,0,0),typ="double3")
        if(scale_unable == True):
            scale_blendColor = cmds.shadingNode("blendColors",asUtility=True)
            cmds.setAttr(f"{scale_blendColor}.color2",*(1,1,1),typ="double3")
        if(True in rot_unable):
            rot_blendColor = cmds.shadingNode("blendColors",asUtility=True)
            cmds.setAttr(f"{rot_blendColor}.color2",*(0,0,0),typ="double3")
        composeMatrix = cmds.createNode("composeMatrix")
        multMatrix = cmds.shadingNode("multMatrix",asUtility=True)

        if(pos_unable == True):
            cmds.connectAttr(f"{unity_setting}.Moveable",f"{move_blendColor}.blender")
            cmds.connectAttr(F"{nurvs}.translate",f"{move_blendColor}.color1")
            cmds.connectAttr(f"{move_blendColor}.output",f"{composeMatrix}.inputTranslate")
        else:
            cmds.connectAttr(f"{nurvs}.t",f"{composeMatrix}.inputTranslate")
        if(scale_unable == True):
            cmds.connectAttr(f"{unity_setting}.Scalable",f"{scale_blendColor}.blender")
            cmds.connectAttr(F"{nurvs}.scale",f"{scale_blendColor}.color1")
            cmds.connectAttr(f"{scale_blendColor}.output",f"{composeMatrix}.inputScale")
        else:
            cmds.connectAttr(f"{nurvs}.s",f"{composeMatrix}.inputScale")
        if(True in rot_unable):
            cmds.connectAttr(f"{unity_setting}.Moveable",f"{rot_blendColor}.blender")
            cmds.connectAttr(F"{nurvs}.rotate",f"{rot_blendColor}.color1")
            cmds.connectAttr(f"{rot_blendColor}.output",f"{composeMatrix}.inputRotate")
            if(rot_unable[0]==False):
                cmds.connectAttr(F"{nurvs}.rx",f"{rot_blendColor}.color2R")
            if(rot_unable[1]==False):
                cmds.connectAttr(F"{nurvs}.ry",f"{rot_blendColor}.color2G")
            if(rot_unable[2]==False):
                cmds.connectAttr(F"{nurvs}.rz",f"{rot_blendColor}.color2B")
        else:
            cmds.connectAttr(f"{nurvs}.r",f"{composeMatrix}.inputRotate")

        cmds.connectAttr(f"{composeMatrix}.outputMatrix",f"{multMatrix}.matrixIn[0]")
        cmds.connectAttr(f"{nurvs}.inverseMatrix",f"{multMatrix}.matrixIn[1]")
        cmds.connectAttr(f"{nurvs}.rotateOrder",f"{composeMatrix}.inputRotateOrder")
        cmds.connectAttr(f"{multMatrix}.matrixSum",f"{DrvObj}.offsetParentMatrix")

    return obj_dic