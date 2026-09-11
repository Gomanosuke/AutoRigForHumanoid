from maya import cmds
import os
from PySide6 import QtWidgets, QtCore, QtGui, QtUiTools
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
import json
from maya.api import OpenMaya

CURRENT_DIR = os.path.dirname(__file__)
UI_FILE_PATH = os.path.join(CURRENT_DIR, "designer_ui.ui")

#(UIウィジェット名, コントローラー名, 左右中央) : __init__でselect_conボタンを一括接続するための対応表
SELECT_CON_BUTTONS = [
    ("select_c_head", "Head", "C"),
    ("select_c_neck", "Neck", "C"),
    ("select_l_shoulder", "Shoulder", "L"),
    ("select_r_shoulder", "Shoulder", "R"),
    ("select_l_upperarmfk", "UpperArmFK", "L"),
    ("select_l_lowerarmfk", "LowerArmFK", "L"),
    ("select_r_upperarmfk", "UpperArmFK", "R"),
    ("select_r_lowerarmfk", "LowerArmFK", "R"),
    ("select_l_wrist1", "Wrist", "L"),
    ("select_r_wrist1", "Wrist", "R"),
    ("select_l_wrist2", "Wrist", "L"),
    ("select_r_wrist2", "Wrist", "R"),
    ("select_l_eye", "Eye", "L"),
    ("select_r_eye", "Eye", "R"),
    ("select_c_eyeaim", "EyeAim", "C"),
    ("select_l_eyeaim", "EyeAim", "L"),
    ("select_r_eyeaim", "EyeAim", "R"),
    ("select_l_armpv", "ArmPV", "L"),
    ("select_r_armpv", "ArmPV", "R"),
    ("select_l_armik", "HandIK", "L"),
    ("select_r_armik", "HandIK", "R"),
    ("select_c_chestik", "ChestIK", "C"),
    ("select_c_chestfk", "ChestFK", "C"),
    ("select_c_spineik", "SpineIK", "C"),
    ("select_c_spinefk", "SpineFK", "C"),
    ("select_c_upperChest", "UpperChest", "C"),
    ("select_c_waist", "Waist", "C"),
    ("select_c_hips", "Hips", "C"),
    ("select_l_upperlegfk", "UpperLegFK", "L"),
    ("select_l_lowerlegfk", "LowerLegFK", "L"),
    ("select_r_upperlegfk", "UpperLegFK", "R"),
    ("select_r_lowerlegfk", "LowerLegFK", "R"),
    ("select_l_footfk", "FootFK", "L"),
    ("select_l_toesfk", "ToesFK", "L"),
    ("select_r_footfk", "FootFK", "R"),
    ("select_r_toesfk", "ToesFK", "R"),
    ("select_l_legik", "LegIK", "L"),
    ("select_r_legik", "LegIK", "R"),
    ("select_l_footik", "FootIK", "L"),
    ("select_r_footik", "FootIK", "R"),
    ("select_l_toesik", "ToesIK", "L"),
    ("select_r_toesik", "ToesIK", "R"),
    ("select_l_legroot", "LegRoot", "L"),
    ("select_r_legroot", "LegRoot", "R"),
    ("select_l_legpv", "LegPV", "L"),
    ("select_r_legpv", "LegPV", "R"),
    ("select_c_root1", "Root1", "C"),
    ("select_c_root2", "Root2", "C"),
    ("select_c_root3", "Root3", "C"),
    ("select_c_setting", "UnitySetting", "C"),
    ("select_l_fingerbundle", "FingerBundle", "L"),
    ("select_r_fingerbundle", "FingerBundle", "R"),
    ("select_l_thumbproximal", "ThumbProximal", "L"),
    ("select_l_thumbintermediate", "ThumbIntermediate", "L"),
    ("select_l_thumbdistal", "ThumbDistal", "L"),
    ("select_l_indexproximal", "IndexProximal", "L"),
    ("select_l_indexintermediate", "IndexIntermediate", "L"),
    ("select_l_indexdistal", "IndexDistal", "L"),
    ("select_l_middleproximal", "MiddleProximal", "L"),
    ("select_l_middleintermediate", "MiddleIntermediate", "L"),
    ("select_l_middledistal", "MiddleDistal", "L"),
    ("select_l_ringproximal", "RingProximal", "L"),
    ("select_l_ringintermediate", "RingIntermediate", "L"),
    ("select_l_ringdistal", "RingDistal", "L"),
    ("select_l_littleproximal", "LittleProximal", "L"),
    ("select_l_littleintermediate", "LittleIntermediate", "L"),
    ("select_l_littledistal", "LittleDistal", "L"),
    ("select_r_thumbproximal", "ThumbProximal", "R"),
    ("select_r_thumbintermediate", "ThumbIntermediate", "R"),
    ("select_r_thumbdistal", "ThumbDistal", "R"),
    ("select_r_indexproximal", "IndexProximal", "R"),
    ("select_r_indexintermediate", "IndexIntermediate", "R"),
    ("select_r_indexdistal", "IndexDistal", "R"),
    ("select_r_middleproximal", "MiddleProximal", "R"),
    ("select_r_middleintermediate", "MiddleIntermediate", "R"),
    ("select_r_middledistal", "MiddleDistal", "R"),
    ("select_r_ringproximal", "RingProximal", "R"),
    ("select_r_ringintermediate", "RingIntermediate", "R"),
    ("select_r_ringdistal", "RingDistal", "R"),
    ("select_r_littleproximal", "LittleProximal", "R"),
    ("select_r_littleintermediate", "LittleIntermediate", "R"),
    ("select_r_littledistal", "LittleDistal", "R"),
]

#(UIウィジェット名, Settingオブジェクトの可視性アトリビュート名) : switch_visボタンを一括接続するための対応表
SWITCH_VIS_BUTTONS = [
    ("vis_body", "BodyV"),
    ("vis_head", "HeadV"),
    ("vis_arm", "ArmV"),
    ("vis_leg", "LegV"),
    ("vis_hand", "HandV"),
    ("vis_l_arm", "ArmLeftV"),
    ("vis_r_arm", "ArmRightV"),
    ("vis_l_leg", "LegLeftV"),
    ("vis_r_leg", "LegRightV"),
    ("vis_l_hand", "HandLeftV"),
    ("vis_r_hand", "HandRightV"),
]

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
        #選択(コントローラー選択ボタン)。(UIウィジェット名, コントローラー名, 左右中央)の対応表から機械的に接続する。
        for widget_name,con_name,pos in SELECT_CON_BUTTONS:
            getattr(self.ui_content,widget_name).clicked.connect(
                lambda checked=False,n=con_name,p=pos: self.select_con(n,p))

        self.ui_content.select_l_allfinger.clicked.connect(lambda: self.select_allfinger("L"))
        self.ui_content.select_r_allfinger.clicked.connect(lambda: self.select_allfinger("R"))

        #表示切替。(UIウィジェット名, Settingオブジェクトの可視性アトリビュート名)の対応表から機械的に接続する。
        for widget_name,attr in SWITCH_VIS_BUTTONS:
            getattr(self.ui_content,widget_name).clicked.connect(
                lambda checked=False,a=attr: self.switch_vis(a))

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

        #シェーダー
        self.ui_content.flat_shade.clicked.connect(lambda: self.flat_shade())

    def _load_obj_dic(self):
        """
        現在のキャラクターの{("Con","L","Head")等: オブジェクトのフルパス}相当の対応辞書を読み込む。
        リグ作成時にシーンの"ARFH_information.<characterName>"アトリビュートへJSON文字列として保存されている。
        (各ボタン処理の先頭で必ず読み込むため共通処理として切り出している)

        Returns
        -------
            dict : {"('Con', 'C', 'Head')"のような文字列キー : オブジェクトのフルパス}
        """
        character_name = cmds.getAttr("ARFH_information.characterName")
        obj_dic_text = cmds.getAttr(f"ARFH_information.{character_name}")
        return json.loads(obj_dic_text)

    def _parse_obj_keys(self, obj_dic:dict):
        """
        obj_dicの各キー("('Con', 'C', 'Head')"のようなタプルのrepr文字列)を
        ["Con","C","Head"]の3要素リストへ変換したものを列挙する。
        (obj_dicのキーはPythonのタプルをそのままrepr文字列化してシーンへ保存しているため、
        ここで文字列から["type","pos","name"]を復元している)

        Parameters
        ----------
            dict obj_dic : self._load_obj_dic()で得られる対応辞書

        Returns
        -------
            list[list[str]] : [[type,pos,name], ...]
        """
        return [[part[1:-1].replace("'", "") for part in key[1:-1].split(",")] for key in obj_dic]

    def select_con(self, name:str,pos:str):
        obj_dic = self._load_obj_dic()

        select_obj = f"('Con', '{pos}', '{name}')"
        obj=cmds.ls(obj_dic[select_obj])
        if(len(obj)==0):
            cmds.error(f"{pos}_{name}が見つかりません")
        else:
            print(f"Select {obj[0]}")

            modifiers = QtWidgets.QApplication.keyboardModifiers()

            if modifiers == QtCore.Qt.ShiftModifier:
                cmds.select(obj[0],r=False,add=True)
            else:
                cmds.select(obj[0],r=True,add=False)

    def select_allfinger(self,pos:str):
        obj_dic = self._load_obj_dic()

        modifiers = QtWidgets.QApplication.keyboardModifiers()

        if modifiers != QtCore.Qt.ShiftModifier:
            cmds.select(cl=True)

        fingers = ["ThumbProximal","ThumbIntermediate","ThumbDistal","IndexProximal","IndexIntermediate","IndexDistal","IndexDistal","MiddleProximal","MiddleIntermediate","MiddleDistal","RingProximal","RingIntermediate","RingDistal","LittleProximal","LittleIntermediate","LittleDistal"]
        for finger in fingers:
            select_obj = f"('Con', '{pos}', '{finger}')"
            obj=cmds.ls(obj_dic[select_obj])
            if(len(obj)==0):
                cmds.error(f"{pos}_{finger}が見つかりません スキップします")
            else:
                print(f"Select {obj[0]}")
                cmds.select(obj[0],r=False,add=True)

    def switch_vis(self,attr):
        obj_dic = self._load_obj_dic()

        setting = cmds.ls(obj_dic["('Con', 'C', 'Setting')"])[0]

        vis = cmds.getAttr(f"{setting}.{attr}")

        if(vis==False):
            cmds.setAttr(f"{setting}.{attr}",1)
        else:
            cmds.setAttr(f"{setting}.{attr}",0)

    def select_all(self):
        obj_dic = self._load_obj_dic()
        convert_obj_dic = self._parse_obj_keys(obj_dic)

        cmds.select(cl=True)

        for obj in convert_obj_dic:
            if(obj[0]=="Con"):
                key=f"('Con', '{obj[1]}', '{obj[2]}')"
                obj=cmds.ls(obj_dic[key])[0]
                cmds.select(obj,tgl=True)

    def reset_pose(self):
        obj_dic = self._load_obj_dic()
        convert_obj_dic = self._parse_obj_keys(obj_dic)

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
                        if(keyable==1 and data_type == "long"):
                            data=cmds.getAttr(F"{obj}.{attr}")
                            cmds.setAttr(F"{obj}.{attr[0:-8]}",data)

                cmds.xform(obj,ws=False,m=[1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1])

    #"C"のコントローラーのうちワールド反転の対象にしないもの
    #  EyeAim : 左右のEyeAimコントローラー自体は左右スワップされるため中央側は据え置きにする(元々の挙動を維持)
    #  Setting : 全アトリビュートがロックされたUI用オブジェクトで、姿勢を持たないため対象外
    _MIRROR_CENTER_SKIP = ("EyeAim","Setting")

    @staticmethod
    def _reflect_local_matrix(matrix, axis):
        """
        ローカル行列(親からの相対値)を、ローカル軸axis(0=X,1=Y,2=Z)を法線とする平面で反転する。
        共役変換(Reflect*M*Reflect)そのものなので、matrixが単位行列(レスト、無ポーズ)なら
        結果も必ず単位行列になる=レスト状態のコントローラーは絶対に動かない。

        Parameters
        ----------
            list matrix : 反転前のローカル行列(16要素)
            int axis : 反転する軸(0=X, 1=Y, 2=Z)

        Returns
        -------
            list : 反転後のローカル行列(16要素)
        """
        sign = [1.0,1.0,1.0]
        sign[axis] = -1.0
        out = list(matrix)
        for i in range(3):
            for j in range(3):
                out[i*4+j] = matrix[i*4+j] * sign[i] * sign[j]
        for j in range(3):
            out[12+j] = matrix[12+j] * sign[j]
        return out

    @staticmethod
    def _mirror_axis_of(obj):
        """
        objの親(Grp)のワールド姿勢から、「キャラクターの左右(ワールドX)」に一番近い
        ローカル軸を求める。スパイン系はprimary_axisの選択やジョイントのロール角次第で
        ローカルXが必ずしも左右方向を向いているとは限らない(例: ローカルXがボーンの
        長手方向=ワールドYに近く、ローカルYの方が左右に近いことがある)ため、決め打ちせず
        親の姿勢から実測する。親(Grp)はmirror_poseで一切書き換えないため、この軸判定は
        呼び出し順序に依存せず安定する。

        Parameters
        ----------
            string obj : 対象のCon(親がGrp)

        Returns
        -------
            int : 0=X, 1=Y, 2=Zのいずれか
        """
        parent = cmds.listRelatives(obj,parent=True,fullPath=True)[0]
        parent_world = cmds.xform(parent,ws=True,q=True,m=True)
        #各ローカル軸(行0,1,2)のワールドX成分の絶対値が最大のものを選ぶ
        rows_x = [abs(parent_world[0]),abs(parent_world[4]),abs(parent_world[8])]
        return rows_x.index(max(rows_x))

    def mirror_pose(self):
        """
        現在のポーズを左右反転する。

        左右(L/R)のコントローラーは、リグ作成時に左右のGrpへ互いに鏡像になるよう
        ローカル軸の反転(autorig_createRig.pyの各部位で"clr=='R'のときGrp.sx/sy=-1"となっている箇所)が
        仕込まれているため、ローカル行列をそのまま入れ替えるだけで正しい鏡映ポーズになる。
        ローカル行列は自分の直接の親からの相対値でしかないため、他のコントローラーを
        どんな順序で処理しても影響を受けない。

        中央(C)のコントローラーは左右のペアが無いため、自分自身のローカル行列を
        (親を固定したまま)反転する。以前はワールド空間でキャラクターの左右軸(ワールドX)を
        直接反転していたが、これだと「親(Grp)の姿勢がわずかでもワールドXに対して非対称
        (ガイド配置の誤差等で厳密な左右対称からずれている)」場合に、無ポーズ(ローカル単位行列)の
        コントローラーまでズレた位置へ再配置されてしまう不具合があった
        (親を固定して子だけ動かす都合上、親の非対称分を子が肩代わりする形で補正されてしまうため)。
        親からの相対値であるローカル行列を、ローカル軸を法線とする平面で反転(共役変換)する形に
        変更したことで、無ポーズなら単位行列は単位行列のまま=レスト状態は必ずレストのまま保たれる。

        ただし反転に使うローカル軸(X/Y/Z)は、ボーンごとにバラバラ(スパイン等は
        primary_axisの選択やジョイントのロール角に依存する)なため決め打ちできず、
        `_mirror_axis_of`で親(Grp)の姿勢から実測して選ぶ。

        Cのワールド行列は、Hips→Waist→SpineFK→ChestFK→Neck→Headのようにswitch_parent経由で
        祖先のワールド行列に連動しているが、ここで扱うのはローカル行列(親のワールド状態に
        依存しない)なので、処理順によって祖先の反転が子孫に二重に乗ることもない
        (以前ワールド行列で反転していた頃はこの問題があり、2段階構成で対処していたが、
        ローカル行列化した今は本質的に発生しなくなっている。読み取りと書き込みを分ける
        2段階構成自体は安全側として残している)。

        Returns
        -------
            無し
        """
        obj_dic = self._load_obj_dic()
        convert_obj_dic = self._parse_obj_keys(obj_dic)

        cmds.select(cl=True)

        #1段階目: 書き込みを一切行わず、反転前の値だけを全コントローラーぶん読み切る
        pending=[]
        for obj_kay in convert_obj_dic:
            if(obj_kay[0]!="Con"):
                continue
            key=f"('Con', '{obj_kay[1]}', '{obj_kay[2]}')"
            obj=cmds.ls(obj_dic[key])[0]

            if(obj_kay[1]=="L"):
                key_r=f"('Con', 'R', '{obj_kay[2]}')"
                r_obj=cmds.ls(obj_dic[key_r])[0]
                l_matrix = cmds.xform(obj,ws=False,q=True,m=True)
                r_matrix = cmds.xform(r_obj,ws=False,q=True,m=True)
                pending.append(("LR",obj,r_obj,l_matrix,r_matrix))

            elif(obj_kay[1]=="C" and obj_kay[2] not in self._MIRROR_CENTER_SKIP):
                axis = self._mirror_axis_of(obj)
                matrix = cmds.xform(obj,ws=False,q=True,m=True)
                pending.append(("C",obj,matrix,axis))

        #2段階目: 1段階目で読み取った(まだ誰も反転していない時点の)値をもとに書き込む
        for entry in pending:
            if(entry[0]=="LR"):
                _,obj,r_obj,l_matrix,r_matrix = entry
                cmds.xform(obj,ws=False,m=r_matrix)
                cmds.xform(r_obj,ws=False,m=l_matrix)
            else:
                _,obj,matrix,axis = entry
                newMatrix = self._reflect_local_matrix(matrix,axis)
                cmds.xform(obj,ws=False,m=newMatrix)

    def arm_iktofk_l(self):
        obj_dic = self._load_obj_dic()

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
        obj_dic = self._load_obj_dic()

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

        obj_dic = self._load_obj_dic()

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
        obj_dic = self._load_obj_dic()

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
        obj_dic = self._load_obj_dic()

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
        obj_dic = self._load_obj_dic()


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
        obj_dic = self._load_obj_dic()


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

    def flat_shade(self):
        viewport_panels = cmds.getPanel(type="modelPanel")
        for panel in viewport_panels:
            cmds.modelEditor(panel, edit=True, displayTextures=True, dl="flat", displayAppearance="smoothShaded")

    def wheelEvent(self, event: QtGui.QWheelEvent):

        modifiers = QtWidgets.QApplication.keyboardModifiers()
        
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