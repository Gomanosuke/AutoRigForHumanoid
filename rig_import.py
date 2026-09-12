from maya import cmds
from maya.api import OpenMaya
import json

"""
別ファイルで作成済みのrig(ARFH_informationを含む)を現在のシーンへインポートし、
Picker(picker.py)がそのまま使えるよう各ノードのUUIDを元の値へ復元する機能。

Mayaのインポート(cmds.file(...,i=True))は、名前の衝突が無くてもノードのUUIDを
維持しない(インポートの度に新しいUUIDが振られる)。Picker等はARFH_informationの
JSON(obj_dic)にUUIDで対象を記録しているため、単純にインポートしただけではPickerが
対象を見つけられなくなる。

そのためautorig_createRig.pyのリグ作成時に、UUIDと対応するノードのフルパス名を
併せてARFH_informationへ記録しておき、ここではインポート直後にそのフルパス名で
対象ノードを特定して、MFnDependencyNode.setUuid()で元のUUIDへ書き戻す。

対応するノード名の記録(<characterName>_names属性)が無い、古い形式でビルドされた
rigファイルはUUID復元の対象外(インポート自体は行われるが、Pickerの対象特定は
シーンを開き直すか、リグを作り直すまで機能しない可能性がある)。

読み込み先のシーンに既に"ARFH_information"がある場合(別キャラクターのrigが既に
存在する場合)、Mayaのインポートは名前の衝突により、読み込んだファイル側の
ARFH_informationを"<読み込んだファイル名>_ARFH_information"のように自動的に
リネームする(統合はしない)。これを放置すると1シーンに複数のARFH_information系
ノードが並存してしまい、
「ARFH_information.characterNameを書き換えるだけでPickerの対象キャラクターを
切り替えられる」という仕様(autorig_createRig.py参照)が崩れる。そのため、
UUID復元後にこの重複ノードぶんの属性を既存のARFH_informationへ統合し、
重複ノード自体は削除する。
"""

def import_rig(path:str):
    """
    別ファイルで作成したrigを現在のシーンへインポートし、記録されている元のUUIDへ復元する。

    Parameters
    ----------
        string path : 読み込むrigファイル(.ma/.mb)のパス

    Returns
    -------
        (int,int) : (UUIDを復元できたノード数, 復元できなかった数)
    """
    if(not path):
        cmds.warning("読み込むrigファイルが指定されていません")
        return (0,0)

    #importで名前が衝突するのは、この時点で既に"ARFH_information"というノードが
    #存在する場合だけ(無ければ読み込んだファイル側がそのままの名前で入る)。
    existing_info = "ARFH_information" if cmds.objExists("ARFH_information") else None

    new_nodes = cmds.file(path,i=True,returnNewNodes=True,ignoreVersion=True) or []
    new_nodes_set = set(new_nodes)
    print(f"{len(new_nodes)}個のノードをインポートしました : {path}")

    #名前衝突時、Mayaは"ARFH_information1"のような数字連番ではなく、
    #"<読み込んだファイル名>_ARFH_information"のように読み込んだファイル名を
    #前置してリネームする(mayapy standaloneで実測確認)。そのため前方一致ではなく
    #部分一致で探す。
    info_candidates = [n for n in new_nodes if "ARFH_information" in n.split("|")[-1]]
    if(not info_candidates):
        cmds.warning(f"{path} : ARFH_informationが見つからないため、UUIDの復元をスキップしました(このファイルはAutoRigForHumanoidで作成されたrigではない可能性があります)")
        return (0,0)

    restored=0
    failed=0
    for info_obj in info_candidates:
        r,f = _restore_uuids(info_obj,new_nodes_set)
        restored+=r
        failed+=f
        if(existing_info and info_obj!=existing_info and cmds.objExists(existing_info)):
            _merge_into_existing_info(info_obj,existing_info)

    print(f"{restored}個のノードのUUIDを復元しました({failed}個失敗) : {path}")
    return (restored,failed)

def _restore_uuids(info_obj:str, new_nodes_set:set):
    """
    1つのARFH_informationノードぶんの記録から、対応するノードのUUIDを元の値へ復元する。

    Parameters
    ----------
        string info_obj : インポートで新規に出来たARFH_informationノード
        set new_nodes_set : 今回のインポートで新規に出来た全ノード(フルパス名)の集合

    Returns
    -------
        (int,int) : (復元できた数, 復元できなかった数)
    """
    if(not cmds.attributeQuery("characterName",node=info_obj,exists=True)):
        cmds.warning(f"{info_obj} : characterNameが見つからないため、UUIDの復元をスキップしました")
        return (0,0)
    character_name = cmds.getAttr(f"{info_obj}.characterName")

    names_attr = f"{character_name}_names"
    if(not cmds.attributeQuery(names_attr,node=info_obj,exists=True)):
        cmds.warning(f"{info_obj}({character_name}) : {names_attr}が見つからないため、UUIDの復元をスキップしました(古い形式でビルドされたrigの可能性があります。リグを作り直すとこの機能が使えるようになります)")
        return (0,0)

    uuid_dic = json.loads(cmds.getAttr(f"{info_obj}.{character_name}"))
    name_dic = json.loads(cmds.getAttr(f"{info_obj}.{names_attr}"))

    restored=0
    failed=0
    for key,original_name in name_dic.items():
        original_uuid = uuid_dic.get(key)
        if(not original_uuid):
            continue
        if(original_name not in new_nodes_set):
            cmds.warning(f"{original_name} : 今回のインポートで作成されたノードとして見つからないため、UUIDの復元をスキップしました(名前の衝突により変名された可能性があります)")
            failed+=1
            continue
        try:
            sel = OpenMaya.MSelectionList()
            sel.add(original_name)
            fn = OpenMaya.MFnDependencyNode(sel.getDependNode(0))
            fn.setUuid(OpenMaya.MUuid(original_uuid))
            restored+=1
        except Exception as e:
            cmds.warning(f"{original_name} : UUIDの復元に失敗しました({e})")
            failed+=1

    return (restored,failed)

def _merge_into_existing_info(src_info:str, dst_info:str):
    """
    importで名前の衝突により新規に出来た重複ARFH_informationノード(src_info)が持つ
    キャラクターぶんの属性を、シーンに元からあったARFH_information(dst_info)へ
    統合し、src_infoを削除する。dst_info.characterName(現在Pickerが対象にしている
    キャラクター)は書き換えない——切り替えたい場合はdst_info.characterNameを
    手動で書き換える(仕様どおり)。

    Parameters
    ----------
        string src_info : インポートで名前の衝突により新規に出来たARFH_information系ノード
        string dst_info : シーンに元からあったARFH_information

    Returns
    -------
        無し
    """
    if(not cmds.attributeQuery("characterName",node=src_info,exists=True)):
        cmds.delete(src_info)
        return
    character_name = cmds.getAttr(f"{src_info}.characterName")

    for attr in (character_name, f"{character_name}_names"):
        if(not cmds.attributeQuery(attr,node=src_info,exists=True)):
            continue
        value = cmds.getAttr(f"{src_info}.{attr}")
        if(not cmds.attributeQuery(attr,node=dst_info,exists=True)):
            cmds.addAttr(f"{dst_info}",ln=attr,dt="string")
        cmds.setAttr(f"{dst_info}.{attr}",value,typ="string")

    cmds.delete(src_info)
    print(f"{src_info} の{character_name}ぶんの記録を{dst_info}へ統合しました(現在Pickerが対象にしているキャラクターは変更していません)")

def browse_import_rig_path(path_field:str):
    """
    読み込むrigファイルの選択ダイアログを開き、結果をtextFieldへ書き込む。

    Parameters
    ----------
        string path_field : 書き込み先のtextField

    Returns
    -------
        無し
    """
    path = cmds.fileDialog2(fileMode=1,caption="Import Rig",fileFilter="Maya Files (*.ma *.mb)")
    if(path):
        cmds.textField(path_field,edit=True,tx=path[0])
