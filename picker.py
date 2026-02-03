from maya import cmds
import os
from PySide6 import QtWidgets, QtCore, QtGui, QtUiTools
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
import json
from maya.api import OpenMaya

CURRENT_DIR = os.path.dirname(__file__)
UI_FILE_PATH = os.path.join(CURRENT_DIR, "designer_ui.ui")

class TRSConnectorWindow(MayaQWidgetBaseMixin, QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super(TRSConnectorWindow, self).__init__(*args, **kwargs)

        # 1. ベースとなるViewとSceneを作成
        self.view = QtWidgets.QGraphicsView()
        self.scene = QtWidgets.QGraphicsScene(self)
        self.view.setScene(self.scene)
        # 背景を透明にしたり枠を消す設定
        self.view.setFrameShape(QtWidgets.QFrame.NoFrame)
        self.setCentralWidget(self.view)
        # 2. DesignerのUIをロードしてProxyWidgetに埋め込む
        loader = QtUiTools.QUiLoader()
        self.ui_content = loader.load(UI_FILE_PATH)
        # ProxyにUIをセットすることで、QWidgetがGraphicsItemとして扱えるようになる
        self.proxy = self.scene.addWidget(self.ui_content)
        self.setWindowTitle(self.ui_content.windowTitle())
        # ズーム倍率の初期値
        self.zoom_level = 1.0

        #ボタンの設定
        #選択
        self.ui_content.select_c_head.clicked.connect(lambda: self.select_con("Head", "C"))
        self.ui_content.select_c_neck.clicked.connect(lambda: self.select_con("Neck", "C"))
        self.ui_content.select_l_shoulder.clicked.connect(lambda: self.select_con("Shoulder", "L"))
        self.ui_content.select_r_shoulder.clicked.connect(lambda: self.select_con("Shoulder", "R"))
        self.ui_content.select_l_upperarmfk.clicked.connect(lambda: self.select_con("UpperArmFK", "L"))
        self.ui_content.select_l_lowerarmfk.clicked.connect(lambda: self.select_con("LowerArmFK", "L"))
        self.ui_content.select_r_upperarmfk.clicked.connect(lambda: self.select_con("UpperArmFK", "R"))
        self.ui_content.select_r_lowerarmfk.clicked.connect(lambda: self.select_con("LowerArmFK", "R"))
        self.ui_content.select_l_wrist1.clicked.connect(lambda: self.select_con("Wrist", "L"))
        self.ui_content.select_r_wrist1.clicked.connect(lambda: self.select_con("Wrist", "R"))
        self.ui_content.select_l_wrist2.clicked.connect(lambda: self.select_con("Wrist", "L"))
        self.ui_content.select_r_wrist2.clicked.connect(lambda: self.select_con("Wrist", "R"))
        self.ui_content.select_l_eye.clicked.connect(lambda: self.select_con("Eye", "L"))
        self.ui_content.select_r_eye.clicked.connect(lambda: self.select_con("Eye", "R"))
        self.ui_content.select_c_eyeaim.clicked.connect(lambda: self.select_con("EyeAim", "C"))
        self.ui_content.select_l_eyeaim.clicked.connect(lambda: self.select_con("EyeAim", "L"))
        self.ui_content.select_r_eyeaim.clicked.connect(lambda: self.select_con("EyeAim", "R"))
        self.ui_content.select_l_armpv.clicked.connect(lambda: self.select_con("ArmPV", "L"))
        self.ui_content.select_r_armpv.clicked.connect(lambda: self.select_con("ArmPV", "R"))
        self.ui_content.select_l_armik.clicked.connect(lambda: self.select_con("HandIK", "L"))
        self.ui_content.select_r_armik.clicked.connect(lambda: self.select_con("HandIK", "R"))
        self.ui_content.select_c_chestik.clicked.connect(lambda: self.select_con("ChestIK", "C"))
        self.ui_content.select_c_chestfk.clicked.connect(lambda: self.select_con("ChestFK", "C"))
        self.ui_content.select_c_spineik.clicked.connect(lambda: self.select_con("SpineIK", "C"))
        self.ui_content.select_c_spinefk.clicked.connect(lambda: self.select_con("SpineFK", "C"))
        self.ui_content.select_c_waist.clicked.connect(lambda: self.select_con("Waist", "C"))
        self.ui_content.select_c_hips.clicked.connect(lambda: self.select_con("Hips", "C"))
        self.ui_content.select_l_upperlegfk.clicked.connect(lambda: self.select_con("UpperLegFK", "L"))
        self.ui_content.select_l_lowerlegfk.clicked.connect(lambda: self.select_con("LowerLegFK", "L"))
        self.ui_content.select_r_upperlegfk.clicked.connect(lambda: self.select_con("UpperLegFK", "R"))
        self.ui_content.select_r_lowerlegfk.clicked.connect(lambda: self.select_con("LowerLegFK", "R"))
        self.ui_content.select_l_footfk.clicked.connect(lambda: self.select_con("FootFK", "L"))
        self.ui_content.select_l_toesfk.clicked.connect(lambda: self.select_con("ToesFK", "L"))
        self.ui_content.select_r_footfk.clicked.connect(lambda: self.select_con("FootFK", "R"))
        self.ui_content.select_r_toesfk.clicked.connect(lambda: self.select_con("ToesFK", "R"))
        self.ui_content.select_l_legik.clicked.connect(lambda: self.select_con("LegIK", "L"))
        self.ui_content.select_r_legik.clicked.connect(lambda: self.select_con("LegIK", "R"))
        self.ui_content.select_l_footik.clicked.connect(lambda: self.select_con("FootIK", "L"))
        self.ui_content.select_r_footik.clicked.connect(lambda: self.select_con("FootIK", "R"))
        self.ui_content.select_l_toesik.clicked.connect(lambda: self.select_con("ToesIK", "L"))
        self.ui_content.select_r_toesik.clicked.connect(lambda: self.select_con("ToesIK", "R"))
        self.ui_content.select_l_legroot.clicked.connect(lambda: self.select_con("LegRoot", "L"))
        self.ui_content.select_r_legroot.clicked.connect(lambda: self.select_con("LegRoot", "R"))
        self.ui_content.select_l_legpv.clicked.connect(lambda: self.select_con("LegPV", "L"))
        self.ui_content.select_r_legpv.clicked.connect(lambda: self.select_con("LegPV", "R"))
        self.ui_content.select_c_root1.clicked.connect(lambda: self.select_con("Root1", "C"))
        self.ui_content.select_c_root2.clicked.connect(lambda: self.select_con("Root2", "C"))
        self.ui_content.select_c_root3.clicked.connect(lambda: self.select_con("Root3", "C"))
        self.ui_content.select_c_setting.clicked.connect(lambda: self.select_con("UnitySetting", "C"))
        self.ui_content.select_l_fingerbundle.clicked.connect(lambda: self.select_con("FingerBundle", "L"))
        self.ui_content.select_r_fingerbundle.clicked.connect(lambda: self.select_con("FingerBundle", "R"))

        self.ui_content.select_l_thumbproximal.clicked.connect(lambda: self.select_con("ThumbProximal", "L"))
        self.ui_content.select_l_thumbintermediate.clicked.connect(lambda: self.select_con("ThumbIntermediate", "L"))
        self.ui_content.select_l_thumbdistal.clicked.connect(lambda: self.select_con("ThumbDistal", "L"))
        self.ui_content.select_l_indexproximal.clicked.connect(lambda: self.select_con("IndexProximal", "L"))
        self.ui_content.select_l_indexintermediate.clicked.connect(lambda: self.select_con("IndexIntermediate", "L"))
        self.ui_content.select_l_indexdistal.clicked.connect(lambda: self.select_con("IndexDistal", "L"))
        self.ui_content.select_l_middleproximal.clicked.connect(lambda: self.select_con("MiddleProximal", "L"))
        self.ui_content.select_l_middleintermediate.clicked.connect(lambda: self.select_con("MiddleIntermediate", "L"))
        self.ui_content.select_l_middledistal.clicked.connect(lambda: self.select_con("MiddleDistal", "L"))
        self.ui_content.select_l_ringproximal.clicked.connect(lambda: self.select_con("RingProximal", "L"))
        self.ui_content.select_l_ringintermediate.clicked.connect(lambda: self.select_con("RingIntermediate", "L"))
        self.ui_content.select_l_ringdistal.clicked.connect(lambda: self.select_con("RingDistal", "L"))
        self.ui_content.select_l_littleproximal.clicked.connect(lambda: self.select_con("LittleProximal", "L"))
        self.ui_content.select_l_littleintermediate.clicked.connect(lambda: self.select_con("LittleIntermediate", "L"))
        self.ui_content.select_l_littledistal.clicked.connect(lambda: self.select_con("LittleDistal", "L"))

        self.ui_content.select_r_thumbproximal.clicked.connect(lambda: self.select_con("ThumbProximal", "R"))
        self.ui_content.select_r_thumbintermediate.clicked.connect(lambda: self.select_con("ThumbIntermediate", "R"))
        self.ui_content.select_r_thumbdistal.clicked.connect(lambda: self.select_con("ThumbDistal", "R"))
        self.ui_content.select_r_indexproximal.clicked.connect(lambda: self.select_con("IndexProximal", "R"))
        self.ui_content.select_r_indexintermediate.clicked.connect(lambda: self.select_con("IndexIntermediate", "R"))
        self.ui_content.select_r_indexdistal.clicked.connect(lambda: self.select_con("IndexDistal", "R"))
        self.ui_content.select_r_middleproximal.clicked.connect(lambda: self.select_con("MiddleProximal", "R"))
        self.ui_content.select_r_middleintermediate.clicked.connect(lambda: self.select_con("MiddleIntermediate", "R"))
        self.ui_content.select_r_middledistal.clicked.connect(lambda: self.select_con("MiddleDistal", "R"))
        self.ui_content.select_r_ringproximal.clicked.connect(lambda: self.select_con("RingProximal", "R"))
        self.ui_content.select_r_ringintermediate.clicked.connect(lambda: self.select_con("RingIntermediate", "R"))
        self.ui_content.select_r_ringdistal.clicked.connect(lambda: self.select_con("RingDistal", "R"))
        self.ui_content.select_r_littleproximal.clicked.connect(lambda: self.select_con("LittleProximal", "R"))
        self.ui_content.select_r_littleintermediate.clicked.connect(lambda: self.select_con("LittleIntermediate", "R"))
        self.ui_content.select_r_littledistal.clicked.connect(lambda: self.select_con("LittleDistal", "R"))

        #表示切替
        self.ui_content.vis_body.clicked.connect(lambda: self.switch_vis("BodyV"))
        self.ui_content.vis_head.clicked.connect(lambda: self.switch_vis("HeadV"))
        self.ui_content.vis_arm.clicked.connect(lambda: self.switch_vis("ArmV"))
        self.ui_content.vis_leg.clicked.connect(lambda: self.switch_vis("LegV"))
        self.ui_content.vis_hand.clicked.connect(lambda: self.switch_vis("HandV"))
        self.ui_content.vis_l_arm.clicked.connect(lambda: self.switch_vis("ArmLeftV"))
        self.ui_content.vis_r_arm.clicked.connect(lambda: self.switch_vis("ArmRightV"))
        self.ui_content.vis_l_leg.clicked.connect(lambda: self.switch_vis("LegLeftV"))
        self.ui_content.vis_r_leg.clicked.connect(lambda: self.switch_vis("LegRightV"))
        self.ui_content.vis_l_hand.clicked.connect(lambda: self.switch_vis("HandLeftV"))
        self.ui_content.vis_r_hand.clicked.connect(lambda: self.switch_vis("HandRightV"))

        #オレンジ 特殊機能
        self.ui_content.select_all.clicked.connect(lambda: self.select_all())
        self.ui_content.reset_pose.clicked.connect(lambda: self.reset_pose())
        self.ui_content.mirror_pose.clicked.connect(lambda: self.mirror_pose())

        #IKFKきりかえ
        self.ui_content.iktofk_l_arm.clicked.connect(lambda: self.arm_iktofk_l())
        self.ui_content.iktofk_r_arm.clicked.connect(lambda: self.arm_iktofk_r())
        self.ui_content.fktoik_l_arm.clicked.connect(lambda: self.arm_fktoik("L"))
        self.ui_content.fktoik_r_arm.clicked.connect(lambda: self.arm_fktoik("R"))
        self.ui_content.iktofk_l_leg.clicked.connect(lambda: self.leg_iktofk_l())
        self.ui_content.iktofk_r_leg.clicked.connect(lambda: self.leg_iktofk_r())
        self.ui_content.fktoik_l_leg.clicked.connect(lambda: self.leg_fktoik_l())
        self.ui_content.fktoik_r_leg.clicked.connect(lambda: self.leg_fktoik_r())




    def select_con(self, name:str,pos:str):
        character_name=cmds.getAttr(F"ARFH_information.characterName")
        obj_dic_text=cmds.getAttr(F"ARFH_information.{character_name}")
        obj_dic=json.loads(obj_dic_text)

        select_obj = f"('Con', '{pos}', '{name}')"
        obj=cmds.ls(obj_dic[select_obj])
        if(len(obj)==0):
            cmds.error(f"{pos}_{name}が見つかりません")
        else:
            modifiers = QtWidgets.QApplication.keyboardModifiers()

            if modifiers == QtCore.Qt.ShiftModifier:
                cmds.select(obj[0],r=False,add=True)
            else:
                cmds.select(obj[0],r=True,add=False)

    def switch_vis(self,attr):
        character_name=cmds.getAttr(F"ARFH_information.characterName")
        obj_dic_text=cmds.getAttr(F"ARFH_information.{character_name}")
        obj_dic=json.loads(obj_dic_text)

        root_con = cmds.ls(obj_dic["('Con', 'C', 'Root1')"])[0]

        vis = cmds.getAttr(f"{root_con}.{attr}")

        if(vis==False):
            cmds.setAttr(f"{root_con}.{attr}",1)
        else:
            cmds.setAttr(f"{root_con}.{attr}",0)

    def select_all(self):
        character_name=cmds.getAttr(F"ARFH_information.characterName")
        obj_dic_text=cmds.getAttr(F"ARFH_information.{character_name}")
        obj_dic=json.loads(obj_dic_text)
        convert_obj_dic = [[x[1:-1].replace("'", '') for x in i[1:-1].split(',')] for i in obj_dic]

        cmds.select(cl=True)

        for obj in convert_obj_dic:
            if(obj[0]=="Con"):
                key=f"('Con', '{obj[1]}', '{obj[2]}')"
                obj=cmds.ls(obj_dic[key])[0]
                cmds.select(obj,tgl=True)

    def reset_pose(self):
        from maya import cmds
        import json
        character_name=cmds.getAttr(F"ARFH_information.characterName")
        obj_dic_text=cmds.getAttr(F"ARFH_information.{character_name}")
        obj_dic=json.loads(obj_dic_text)
        convert_obj_dic = [[x[1:-1].replace("'", '') for x in i[1:-1].split(',')] for i in obj_dic]

        for obj in convert_obj_dic:
            if(obj[0]=="Con"):
                key=f"('Con', '{obj[1]}', '{obj[2]}')"
                obj=cmds.ls(obj_dic[key])[0]
                attr_list=cmds.listAttr(obj)
                for attr in attr_list:
                    if('.' not in attr and '_Default' in attr):
                        keyable=cmds.getAttr(F"{obj}.{attr[0:-8]}",k=True)
                        data_type=cmds.getAttr(F"{obj}.{attr}",typ=True)
                        if(keyable==1 and data_type == "double"):
                            data=cmds.getAttr(F"{obj}.{attr}")
                            cmds.setAttr(F"{obj}.{attr[0:-8]}",data)
                        if(keyable==1 and data_type == "float"):
                            data=cmds.getAttr(F"{obj}.{attr}")
                            cmds.setAttr(F"{obj}.{attr[0:-8]}",data)

                cmds.xform(obj,ws=False,m=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])

    def mirror_pose(self):
        character_name=cmds.getAttr(F"ARFH_information.characterName")
        obj_dic_text=cmds.getAttr(F"ARFH_information.{character_name}")
        obj_dic=json.loads(obj_dic_text)
        convert_obj_dic = [[x[1:-1].replace("'", '') for x in i[1:-1].split(',')] for i in obj_dic]

        cmds.select(cl=True)

        for obj_kay in convert_obj_dic:
            if(obj_kay[0]=="Con"):
                key=f"('Con', '{obj_kay[1]}', '{obj_kay[2]}')"
                obj=cmds.ls(obj_dic[key])[0]
                if(obj_kay[1]=="L"):
                    key_r=f"('Con', 'R', '{obj_kay[2]}')"
                    r_obj=cmds.ls(obj_dic[key_r])[0]
                    l_matrix = cmds.xform(obj,ws=False,q=True,m=True)
                    r_matrix = cmds.xform(r_obj,ws=False,q=True,m=True)

                    cmds.xform(obj,ws=False,m=r_matrix)
                    cmds.xform(r_obj,ws=False,m=l_matrix)

                if(obj_kay[1]=="C" and obj_kay[2]!="EyeAim"):
                    if(obj[2]!="EyeAim" and obj[2]!="Root1" and obj_kay[2]!="Root2" and obj_kay[2]!="Root3"):
                        matrix = cmds.xform(obj,ws=False,q=True,m=True)
                        newMatrix = [matrix[0],-matrix[1],matrix[2],matrix[3]
                                    ,-matrix[4],matrix[5],matrix[6],matrix[7]
                                    ,matrix[8],-matrix[9],matrix[10],matrix[11]
                                    ,matrix[12],-matrix[13],matrix[14],matrix[15]]
                        cmds.xform(obj,ws=False,m=newMatrix)
                    else:
                        matrix = cmds.xform(obj,ws=False,q=True,m=True)
                        newMatrix = [matrix[0],matrix[1],-matrix[2],matrix[3]
                                    ,-matrix[4],matrix[5],matrix[6],matrix[7]
                                    ,matrix[8],-matrix[9],matrix[10],matrix[11]
                                    ,-matrix[12],matrix[13],matrix[14],matrix[15]]
                        cmds.xform(obj,ws=False,m=newMatrix)

    def arm_iktofk_l(self):
        character_name=cmds.getAttr(F"ARFH_information.characterName")
        obj_dic_text=cmds.getAttr(F"ARFH_information.{character_name}")
        obj_dic=json.loads(obj_dic_text)

        upperArmFK_con=cmds.ls(obj_dic["('Con', 'L', 'UpperArmFK')"])[0]
        upperArmFK_drv=cmds.ls(obj_dic["('Drv', 'L', 'UpperArmFK')"])[0]
        lowerArmFK_con=cmds.ls(obj_dic["('Con', 'L', 'LowerArmFK')"])[0]
        lowerArmFK_drv=cmds.ls(obj_dic["('Drv', 'L', 'LowerArmFK')"])[0]
        upperArmIK_joint=cmds.ls(obj_dic["('Joint', 'L', 'UpperArmIK')"])[0]
        lowerArmIK_joint=cmds.ls(obj_dic["('Joint', 'L', 'LowerArmIK')"])[0]
        shoulder_con=cmds.ls(obj_dic["('Con', 'L', 'Shoulder')"])[0]

        upperArm_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{upperArmFK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{upperArmIK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(upperArmIK_joint,q=True,ws=True,m=True))
        cmds.xform(upperArmFK_con,m=list(upperArm_matrix),ws=True)

        lowerArm_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{lowerArmFK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{lowerArmIK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(lowerArmIK_joint,q=True,ws=True,m=True))
        cmds.xform(lowerArmFK_con,m=list(lowerArm_matrix),ws=True)

        cmds.setAttr(F"{lowerArmFK_con}.sx",abs(cmds.getAttr(F"{lowerArmFK_con}.sx")))
        cmds.setAttr(F"{lowerArmFK_con}.sy",abs(cmds.getAttr(F"{lowerArmFK_con}.sy")))
        cmds.setAttr(F"{lowerArmFK_con}.sz",abs(cmds.getAttr(F"{lowerArmFK_con}.sz")))
        cmds.setAttr(F"{upperArmFK_con}.sx",abs(cmds.getAttr(F"{upperArmFK_con}.sx")))
        cmds.setAttr(F"{upperArmFK_con}.sy",abs(cmds.getAttr(F"{upperArmFK_con}.sy")))
        cmds.setAttr(F"{upperArmFK_con}.sz",abs(cmds.getAttr(F"{upperArmFK_con}.sz")))
        cmds.setAttr(F"{shoulder_con}.IKFK",1)

    def arm_iktofk_r(self):
        character_name=cmds.getAttr(F"ARFH_information.characterName")
        obj_dic_text=cmds.getAttr(F"ARFH_information.{character_name}")
        obj_dic=json.loads(obj_dic_text)

        upperArmFK_con=cmds.ls(obj_dic["('Con', 'R', 'UpperArmFK')"])[0]
        upperArmFK_drv=cmds.ls(obj_dic["('Drv', 'R', 'UpperArmFK')"])[0]
        lowerArmFK_con=cmds.ls(obj_dic["('Con', 'R', 'LowerArmFK')"])[0]
        lowerArmFK_drv=cmds.ls(obj_dic["('Drv', 'R', 'LowerArmFK')"])[0]
        upperArmIK_joint=cmds.ls(obj_dic["('Joint', 'R', 'UpperArmIK')"])[0]
        lowerArmIK_joint=cmds.ls(obj_dic["('Joint', 'R', 'LowerArmIK')"])[0]
        shoulder_con=cmds.ls(obj_dic["('Con', 'R', 'Shoulder')"])[0]

        upperArm_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{upperArmFK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{upperArmIK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(upperArmIK_joint,q=True,ws=True,m=True))
        cmds.xform(upperArmFK_con,m=list(upperArm_matrix),ws=True)

        cmds.setAttr(F"{upperArmFK_con}.sx",abs(cmds.getAttr(F"{upperArmFK_con}.sx")))
        cmds.setAttr(F"{upperArmFK_con}.sy",abs(cmds.getAttr(F"{upperArmFK_con}.sy")))
        cmds.setAttr(F"{upperArmFK_con}.sz",abs(cmds.getAttr(F"{upperArmFK_con}.sz")))
        cmds.xform(upperArmFK_con,ro=(180,0,0),r=True,eu=True)

        lowerArm_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{lowerArmFK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{lowerArmIK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(lowerArmIK_joint,q=True,ws=True,m=True))
        cmds.xform(lowerArmFK_con,m=list(lowerArm_matrix),ws=True)

        cmds.setAttr(F"{lowerArmFK_con}.sx",abs(cmds.getAttr(F"{lowerArmFK_con}.sx")))
        cmds.setAttr(F"{lowerArmFK_con}.sy",abs(cmds.getAttr(F"{lowerArmFK_con}.sy")))
        cmds.setAttr(F"{lowerArmFK_con}.sz",abs(cmds.getAttr(F"{lowerArmFK_con}.sz")))
        cmds.xform(lowerArmFK_con,ro=(180,0,0),r=True,eu=True)

        cmds.setAttr(F"{shoulder_con}.IKFK",1)

    def arm_fktoik(self,pos):
        if pos=="L": factor=1
        else: factor=-1

        character_name=cmds.getAttr(F"ARFH_information.characterName")
        obj_dic_text=cmds.getAttr(F"ARFH_information.{character_name}")
        obj_dic=json.loads(obj_dic_text)

        handIK_con=cmds.ls(obj_dic[f"('Con', '{pos}', 'HandIK')"])[0]
        handIK_drv=cmds.ls(obj_dic[f"('Drv', '{pos}', 'HandIK')"])[0]
        armPV_con=cmds.ls(obj_dic[f"('Con', '{pos}', 'ArmPV')"])[0]
        upperArmFK_joint=cmds.ls(obj_dic[f"('Joint', '{pos}', 'UpperArmFK')"])[0]
        lowerArmFK_joint=cmds.ls(obj_dic[f"('Joint', '{pos}', 'LowerArmFK')"])[0]
        handFK_joint=cmds.ls(obj_dic[f"('Joint', '{pos}', 'HandFK')"])[0]
        shoulder_con=cmds.ls(obj_dic[f"('Con', '{pos}', 'Shoulder')"])[0]

        #handIK
        hand_matrix=cmds.xform(handFK_joint,q=True,m=True,ws=True)
        cmds.xform(handIK_con,m=hand_matrix,ws=True)

        cmds.setAttr(F"{armPV_con}.t",*(0,0,0),typ="double3")
        cmds.setAttr(F"{armPV_con}.r",*(0,0,0),typ="double3")
        origin=OpenMaya.MVector(cmds.xform(armPV_con,ws=True,q=True,t=True))
        target=OpenMaya.MVector(cmds.xform(lowerArmFK_joint,ws=True,q=True,t=True))
        up=OpenMaya.MVector((0,1,0))
        aim=((target - origin)*factor).normalize()
        side = aim ^ up
        side.normalize()
        up = side ^ aim
        up.normalize()
        m=[side.x,side.y,side.z,0,
        up.x,up.y,up.z,0,
        aim.x,aim.y,aim.z,0,
        target.x,target.y,target.z,1]
        cmds.xform(armPV_con,m=m,ws=True)

        cmds.setAttr(F"{shoulder_con}.IKFK",0)
        cmds.setAttr(F"{handIK_con}.stretch",1)
        cmds.setAttr(F"{handIK_con}.smoothIK",0)

    def leg_iktofk_l(self):
        character_name=cmds.getAttr(F"ARFH_information.characterName")
        obj_dic_text=cmds.getAttr(F"ARFH_information.{character_name}")
        obj_dic=json.loads(obj_dic_text)

        upperLegFK_con=cmds.ls(obj_dic["('Con', 'L', 'UpperLegFK')"])[0]
        upperLegFK_drv=cmds.ls(obj_dic["('Drv', 'L', 'UpperLegFK')"])[0]
        lowerLegFK_con=cmds.ls(obj_dic["('Con', 'L', 'LowerLegFK')"])[0]
        lowerLegFK_drv=cmds.ls(obj_dic["('Drv', 'L', 'LowerLegFK')"])[0]
        footFK_con=cmds.ls(obj_dic["('Con', 'L', 'FootFK')"])[0]
        footFK_drv=cmds.ls(obj_dic["('Drv', 'L', 'FootFK')"])[0]
        toesFK_con=cmds.ls(obj_dic["('Con', 'L', 'ToesFK')"])[0]
        toesFK_drv=cmds.ls(obj_dic["('Drv', 'L', 'ToesFK')"])[0]
        root_con=cmds.ls(obj_dic["('Con', 'L', 'LegRoot')"])[0]

        upperLegIK_joint=cmds.ls(obj_dic["('Joint', 'L', 'UpperLegIK')"])[0]
        lowerLegIK_joint=cmds.ls(obj_dic["('Joint', 'L', 'LowerLegIK')"])[0]
        footIK_joint=cmds.ls(obj_dic["('Joint', 'L', 'FootIK')"])[0]
        toesIK_joint=cmds.ls(obj_dic["('Joint', 'L', 'ToesIK')"])[0]

        upperLeg_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{upperLegFK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{upperLegIK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(upperLegIK_joint,q=True,ws=True,m=True))
        cmds.xform(upperLegFK_con,m=list(upperLeg_matrix),ws=True)

        lowerLeg_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{lowerLegFK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{lowerLegIK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(lowerLegIK_joint,q=True,ws=True,m=True))
        cmds.xform(lowerLegFK_con,m=list(lowerLeg_matrix),ws=True)

        foot_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{footFK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{footIK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(footIK_joint,q=True,ws=True,m=True))
        cmds.xform(footFK_con,m=list(foot_matrix),ws=True)

        toes_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{toesFK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{toesIK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(toesIK_joint,q=True,ws=True,m=True))
        cmds.xform(toesFK_con,m=list(toes_matrix),ws=True)


        cmds.setAttr(F"{lowerLegFK_con}.sx",abs(cmds.getAttr(F"{lowerLegFK_con}.sx")))
        cmds.setAttr(F"{lowerLegFK_con}.sy",abs(cmds.getAttr(F"{lowerLegFK_con}.sy")))
        cmds.setAttr(F"{lowerLegFK_con}.sz",abs(cmds.getAttr(F"{lowerLegFK_con}.sz")))
        cmds.setAttr(F"{upperLegFK_con}.sx",abs(cmds.getAttr(F"{upperLegFK_con}.sx")))
        cmds.setAttr(F"{upperLegFK_con}.sy",abs(cmds.getAttr(F"{upperLegFK_con}.sy")))
        cmds.setAttr(F"{upperLegFK_con}.sz",abs(cmds.getAttr(F"{upperLegFK_con}.sz")))
        cmds.setAttr(F"{footFK_con}.sx",abs(cmds.getAttr(F"{footFK_con}.sx")))
        cmds.setAttr(F"{footFK_con}.sy",abs(cmds.getAttr(F"{footFK_con}.sy")))
        cmds.setAttr(F"{footFK_con}.sz",abs(cmds.getAttr(F"{footFK_con}.sz")))
        cmds.setAttr(F"{toesFK_con}.sx",abs(cmds.getAttr(F"{toesFK_con}.sx")))
        cmds.setAttr(F"{toesFK_con}.sy",abs(cmds.getAttr(F"{toesFK_con}.sy")))
        cmds.setAttr(F"{toesFK_con}.sz",abs(cmds.getAttr(F"{toesFK_con}.sz")))
        cmds.setAttr(F"{root_con}.IKFK",1)

    def leg_iktofk_r(self):
        character_name=cmds.getAttr(F"ARFH_information.characterName")
        obj_dic_text=cmds.getAttr(F"ARFH_information.{character_name}")
        obj_dic=json.loads(obj_dic_text)

        upperLegFK_con=cmds.ls(obj_dic["('Con', 'R', 'UpperLegFK')"])[0]
        upperLegFK_drv=cmds.ls(obj_dic["('Drv', 'R', 'UpperLegFK')"])[0]
        lowerLegFK_con=cmds.ls(obj_dic["('Con', 'R', 'LowerLegFK')"])[0]
        lowerLegFK_drv=cmds.ls(obj_dic["('Drv', 'R', 'LowerLegFK')"])[0]
        footFK_con=cmds.ls(obj_dic["('Con', 'R', 'FootFK')"])[0]
        footFK_drv=cmds.ls(obj_dic["('Drv', 'R', 'FootFK')"])[0]
        toesFK_con=cmds.ls(obj_dic["('Con', 'R', 'ToesFK')"])[0]
        toesFK_drv=cmds.ls(obj_dic["('Drv', 'R', 'ToesFK')"])[0]
        root_con=cmds.ls(obj_dic["('Con', 'R', 'LegRoot')"])[0]

        upperLegIK_joint=cmds.ls(obj_dic["('Joint', 'R', 'UpperLegIK')"])[0]
        lowerLegIK_joint=cmds.ls(obj_dic["('Joint', 'R', 'LowerLegIK')"])[0]
        footIK_joint=cmds.ls(obj_dic["('Joint', 'R', 'FootIK')"])[0]
        toesIK_joint=cmds.ls(obj_dic["('Joint', 'R', 'ToesIK')"])[0]

        upperLeg_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{upperLegFK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{upperLegIK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(upperLegIK_joint,q=True,ws=True,m=True))
        cmds.xform(upperLegFK_con,m=list(upperLeg_matrix),ws=True)
        cmds.setAttr(F"{upperLegFK_con}.sx",abs(cmds.getAttr(F"{upperLegFK_con}.sx")))
        cmds.setAttr(F"{upperLegFK_con}.sy",abs(cmds.getAttr(F"{upperLegFK_con}.sy")))
        cmds.setAttr(F"{upperLegFK_con}.sz",abs(cmds.getAttr(F"{upperLegFK_con}.sz")))
        cmds.xform(upperLegFK_con,ro=(180,0,0),r=True,eu=True)

        lowerLeg_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{lowerLegFK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{lowerLegIK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(lowerLegIK_joint,q=True,ws=True,m=True))
        cmds.xform(lowerLegFK_con,m=list(lowerLeg_matrix),ws=True)
        cmds.setAttr(F"{lowerLegFK_con}.sx",abs(cmds.getAttr(F"{lowerLegFK_con}.sx")))
        cmds.setAttr(F"{lowerLegFK_con}.sy",abs(cmds.getAttr(F"{lowerLegFK_con}.sy")))
        cmds.setAttr(F"{lowerLegFK_con}.sz",abs(cmds.getAttr(F"{lowerLegFK_con}.sz")))
        cmds.xform(lowerLegFK_con,ro=(180,0,0),r=True,eu=True)

        foot_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{footFK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{footIK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(footIK_joint,q=True,ws=True,m=True))
        cmds.xform(footFK_con,m=list(foot_matrix),ws=True)
        cmds.setAttr(F"{footFK_con}.sx",abs(cmds.getAttr(F"{footFK_con}.sx")))
        cmds.setAttr(F"{footFK_con}.sy",abs(cmds.getAttr(F"{footFK_con}.sy")))
        cmds.setAttr(F"{footFK_con}.sz",abs(cmds.getAttr(F"{footFK_con}.sz")))
        cmds.xform(footFK_con,ro=(180,0,0),r=True,eu=True)

        toes_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{toesFK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{toesIK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(toesIK_joint,q=True,ws=True,m=True))
        cmds.xform(toesFK_con,m=list(toes_matrix),ws=True)
        cmds.setAttr(F"{toesFK_con}.sx",abs(cmds.getAttr(F"{toesFK_con}.sx")))
        cmds.setAttr(F"{toesFK_con}.sy",abs(cmds.getAttr(F"{toesFK_con}.sy")))
        cmds.setAttr(F"{toesFK_con}.sz",abs(cmds.getAttr(F"{toesFK_con}.sz")))
        cmds.xform(toesFK_con,ro=(180,0,0),r=True,eu=True)

        cmds.setAttr(F"{root_con}.IKFK",1)

    def leg_fktoik_l(self):
        character_name=cmds.getAttr(F"ARFH_information.characterName")
        obj_dic_text=cmds.getAttr(F"ARFH_information.{character_name}")
        obj_dic=json.loads(obj_dic_text)


        legIK_con=cmds.ls(obj_dic["('Con', 'L', 'LegIK')"])[0]
        legIK_grp=cmds.ls(obj_dic["('Grp', 'L', 'LegIK')"])[0]
        toesIK_con=cmds.ls(obj_dic["('Con', 'L', 'ToesIK')"])[0]
        toesIK_drv=cmds.ls(obj_dic["('Drv', 'L', 'ToesIK')"])[0]
        legPV_con=cmds.ls(obj_dic["('Con', 'L', 'LegPV')"])[0]
        upperLegFK_joint=cmds.ls(obj_dic["('Joint', 'L', 'UpperLegFK')"])[0]
        lowerLegFK_joint=cmds.ls(obj_dic["('Joint', 'L', 'LowerLegFK')"])[0]
        footFK_joint=cmds.ls(obj_dic["('Joint', 'L', 'FootFK')"])[0]
        toesFK_joint=cmds.ls(obj_dic["('Joint', 'L', 'ToesFK')"])[0]
        root_con=cmds.ls(obj_dic["('Con', 'L', 'LegRoot')"])[0]

        #legIK
        upperLeg_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{legIK_grp}.Root3Matrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{footFK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(footFK_joint,q=True,ws=True,m=True))
        cmds.xform(legIK_con,m=list(upperLeg_matrix),ws=True)

        cmds.setAttr(F"{legPV_con}.t",*(0,0,0),typ="double3")
        cmds.setAttr(F"{legPV_con}.r",*(0,0,0),typ="double3")
        origin=OpenMaya.MVector(cmds.xform(legPV_con,ws=True,q=True,t=True))
        target=OpenMaya.MVector(cmds.xform(lowerLegFK_joint,ws=True,q=True,t=True))
        up=OpenMaya.MVector((0,1,0))
        aim=(origin-target).normalize()
        side = aim ^ up
        side.normalize()
        up = side ^ aim
        up.normalize()
        m=[side.x,side.y,side.z,0,
        up.x,up.y,up.z,0,
        aim.x,aim.y,aim.z,0,
        target.x,target.y,target.z,1]
        cmds.xform(legPV_con,m=m,ws=True)

        cmds.setAttr(F"{root_con}.IKFK",0)
        cmds.setAttr(F"{legIK_con}.stretch",1)
        cmds.setAttr(F"{legIK_con}.smoothIK",0)
        cmds.setAttr(F"{legIK_con}.HeelRoll",0)
        cmds.setAttr(F"{legIK_con}.HeelRotate",0)
        cmds.setAttr(F"{legIK_con}.Tilt",0)
        cmds.setAttr(F"{legIK_con}.ToeRoll",0)
        cmds.setAttr(F"{legIK_con}.ToeRotate",0)
        cmds.setAttr(F"{legIK_con}.twist",0)

        #toeIK
        toes_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{toesIK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{toesFK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(toesFK_joint,q=True,ws=True,m=True))
        cmds.xform(toesIK_con,m=list(toes_matrix),ws=True)

    def leg_fktoik_r(self):
        character_name=cmds.getAttr(F"ARFH_information.characterName")
        obj_dic_text=cmds.getAttr(F"ARFH_information.{character_name}")
        obj_dic=json.loads(obj_dic_text)


        legIK_con=cmds.ls(obj_dic["('Con', 'R', 'LegIK')"])[0]
        legIK_grp=cmds.ls(obj_dic["('Grp', 'R', 'LegIK')"])[0]
        toesIK_con=cmds.ls(obj_dic["('Con', 'R', 'ToesIK')"])[0]
        toesIK_drv=cmds.ls(obj_dic["('Drv', 'R', 'ToesIK')"])[0]
        legPV_con=cmds.ls(obj_dic["('Con', 'R', 'LegPV')"])[0]
        upperLegFK_joint=cmds.ls(obj_dic["('Joint', 'R', 'UpperLegFK')"])[0]
        lowerLegFK_joint=cmds.ls(obj_dic["('Joint', 'R', 'LowerLegFK')"])[0]
        footFK_joint=cmds.ls(obj_dic["('Joint', 'R', 'FootFK')"])[0]
        toesFK_joint=cmds.ls(obj_dic["('Joint', 'R', 'ToesFK')"])[0]
        root_con=cmds.ls(obj_dic["('Con', 'R', 'LegRoot')"])[0]

        #legIK
        upperLeg_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{legIK_grp}.Root3Matrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{footFK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(footFK_joint,q=True,ws=True,m=True))
        cmds.xform(legIK_con,m=list(upperLeg_matrix),ws=True)
        cmds.xform(legIK_con,ro=(0,180,0),r=True,eu=True)

        cmds.setAttr(F"{legPV_con}.t",*(0,0,0),typ="double3")
        cmds.setAttr(F"{legPV_con}.r",*(0,0,0),typ="double3")
        origin=OpenMaya.MVector(cmds.xform(legPV_con,ws=True,q=True,t=True))
        target=OpenMaya.MVector(cmds.xform(lowerLegFK_joint,ws=True,q=True,t=True))
        up=OpenMaya.MVector((0,1,0))
        aim=(target-origin).normalize()
        side = aim ^ up
        side.normalize()
        up = side ^ aim
        up.normalize()
        m=[side.x,side.y,side.z,0,
        up.x,up.y,up.z,0,
        aim.x,aim.y,aim.z,0,
        target.x,target.y,target.z,1]
        cmds.xform(legPV_con,m=m,ws=True)

        cmds.setAttr(F"{root_con}.IKFK",0)
        cmds.setAttr(F"{legIK_con}.stretch",1)
        cmds.setAttr(F"{legIK_con}.smoothIK",0)
        cmds.setAttr(F"{legIK_con}.HeelRoll",0)
        cmds.setAttr(F"{legIK_con}.HeelRotate",0)
        cmds.setAttr(F"{legIK_con}.Tilt",0)
        cmds.setAttr(F"{legIK_con}.ToeRoll",0)
        cmds.setAttr(F"{legIK_con}.ToeRotate",0)
        cmds.setAttr(F"{legIK_con}.twist",0)

        #toeIK
        toes_matrix = OpenMaya.MMatrix(cmds.getAttr(f"{toesIK_drv}.WorldBindMatrix"))*OpenMaya.MMatrix(cmds.getAttr(f"{toesFK_joint}.WorldBindMatrix")).inverse()*OpenMaya.MMatrix(cmds.xform(toesFK_joint,q=True,ws=True,m=True))
        cmds.xform(toesIK_con,m=list(toes_matrix),ws=True)
        cmds.setAttr(F"{toesIK_con}.sx",abs(cmds.getAttr(F"{toesIK_con}.sx")))
        cmds.setAttr(F"{toesIK_con}.sy",abs(cmds.getAttr(F"{toesIK_con}.sy")))
        cmds.setAttr(F"{toesIK_con}.sz",abs(cmds.getAttr(F"{toesIK_con}.sz")))
        cmds.xform(toesIK_con,ro=(180,0,0),r=True,eu=True)


    def wheelEvent(self, event: QtGui.QWheelEvent):
        zoom_in_factor = 1.1
        zoom_out_factor = 0.9

        if event.angleDelta().y() > 0:
            scale_factor = zoom_in_factor
            self.zoom_level *= zoom_in_factor
        else:
            scale_factor = zoom_out_factor
            self.zoom_level *= zoom_out_factor

        # Viewをスケーリング（中心を基準に拡縮）
        self.view.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.view.scale(scale_factor, scale_factor)

        event.accept()


def show_ui():
    global my_tool_instance
    try:
        my_tool_instance.close()
        my_tool_instance.deleteLater()
    except:
        pass
        
    my_tool_instance = TRSConnectorWindow()
    my_tool_instance.show()