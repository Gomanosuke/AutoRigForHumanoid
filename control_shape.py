from maya import cmds
from maya.api import OpenMaya
import json

"""
コントローラー(Con_*)のカーブ形状(CVのローカル座標)をjsonへ書き出し/読み込みする機能。

想定用途: ビューポートでコントローラーのシェイプをCV単位で手直しした後に、
バグ修正やノード構成の変更でリグを作り直す必要が出た場合、シェイプ出力→リグ作り直し→
同じ名前のコントローラーへシェイプ読み込み、とすることで手直ししたシェイプを再度
作り直さずに済ませられるようにする。

対象はcreate_nurvs()が作る、構築履歴の無い静的なnurbsCurve(create_controller参照)。
CVの数さえ保存時と一致していれば、テンプレート形状やCV単位の手直しの内容に関わらず
そのまま書き戻せる(数が変わっている場合はインデックスがズレて壊れた形状になるため
書き戻さずスキップする)。
"""

def _cv_count(shape:str):
    """
    nurbsCurveシェイプの実際のCV数を調べる。

    Parameters
    ----------
        string shape : nurbsCurveシェイプノード

    Returns
    -------
        int : CV数(periodicカーブの場合も、ラップ分を除いた実際の制御点数)
    """
    sel = OpenMaya.MSelectionList()
    sel.add(shape)
    fn = OpenMaya.MFnNurbsCurve(sel.getDagPath(0))
    return fn.numCVs

def _get_shape_data(shape:str):
    """
    1本のnurbsCurveシェイプからCVのローカル座標を取り出す。

    Parameters
    ----------
        string shape : nurbsCurveシェイプノード

    Returns
    -------
        dict : {"degree":int, "cvs":[[x,y,z], ...]}
    """
    cvs = [list(cmds.getAttr(f"{shape}.controlPoints[{i}]")[0]) for i in range(_cv_count(shape))]
    return {"degree":cmds.getAttr(f"{shape}.degree"), "cvs":cvs}

def _apply_shape_data(shape:str, data:dict):
    """
    _get_shape_dataで取り出した形状データを既存のnurbsCurveシェイプへ書き戻す。
    保存時とCV数が異なる場合は、インデックスがズレて壊れた形状になってしまうため
    何もせずスキップする(shapeを作り直すコントローラーの形状テンプレートが変わった場合等)。

    Parameters
    ----------
        string shape : 書き戻し先のnurbsCurveシェイプノード
        dict data : _get_shape_dataの戻り値

    Returns
    -------
        bool : 書き戻せたらTrue、CV数不一致でスキップしたらFalse
    """
    n = _cv_count(shape)
    if(n != len(data["cvs"])):
        cmds.warning(f"{shape} : 保存時とCV数が異なるため適用をスキップしました(保存時{len(data['cvs'])}個 → 現在{n}個)")
        return False
    for i,cv in enumerate(data["cvs"]):
        cmds.setAttr(f"{shape}.controlPoints[{i}]",*cv,type="double3")
    return True

def _expand_to_controllers(nodes):
    """
    指定されたノード群を、名前が"Con_"で始まるtransform一覧へ展開する。
    ノード自身がCon_*ならそのまま採用し、それ以外(リグのトップグループ等)は
    子孫からCon_*を探す。

    Parameters
    ----------
        list nodes : 起点にするノード(ロングネーム)のリスト

    Returns
    -------
        list : 重複の無いCon_*トランスフォーム(ロングネーム)のリスト
    """
    result=[]
    seen=set()
    for node in nodes:
        if(node.split("|")[-1].startswith("Con_")):
            candidates=[node]
        else:
            candidates=cmds.listRelatives(node,allDescendents=True,fullPath=True,type="transform") or []
        for c in candidates:
            if(c.split("|")[-1].startswith("Con_") and c not in seen):
                seen.add(c)
                result.append(c)
    return result

def target_controllers(targets=None):
    """
    書き出し/読み込みの対象になるCon_*トランスフォーム一覧を決める。
    targets省略時は選択中のノードを、選択も無ければシーン内の全Con_*を対象にする。
    targets/選択のノードはCon_*自体でなくてもよく、リグのトップグループ等を渡せば
    子孫のCon_*をまとめて対象にできる(複数キャラクターが同じシーンにいる場合の
    絞り込みに使う)。

    targets/選択の中にCon_*が1つも見つからない場合(例えば、リグ作成直後に無関係な
    オブジェクトが選択されたまま残っている等)は、絞り込むつもりの選択ではなく
    「たまたま何か選択されているだけ」とみなし、警告した上でシーン内の全Con_*へ
    フォールバックする。これをしないと、無関係なものが選択されているだけで
    出力・読み込みの対象が0件になり、全コントローラーが「見つからない」扱いに
    なってしまう(実際に発生した不具合: リグ作成直後に何かが選択されたまま
    シェイプ読み込みを行うと全件スキップになり、一見シーンを開き直さないと
    直らないように見えていた。開き直すと選択が外れるため直って見えていただけで、
    原因は選択によるフィルタそのものだった)。

    Parameters
    ----------
        list targets : 対象を絞るノード。省略可

    Returns
    -------
        list : Con_*トランスフォーム(ロングネーム)のリスト
    """
    if(targets):
        scoped = _expand_to_controllers(cmds.ls(targets,long=True))
        if(scoped):
            return scoped
        cmds.warning("指定された対象にコントローラーが含まれていないため、シーン内の全Con_*を対象にします")
    else:
        sel = cmds.ls(sl=True,long=True)
        if(sel):
            scoped = _expand_to_controllers(sel)
            if(scoped):
                return scoped
            cmds.warning("選択中のオブジェクトにコントローラーが含まれていないため、シーン内の全Con_*を対象にします")
    return cmds.ls("Con_*",type="transform",long=True) or []

def export_shapes(path:str, targets=None):
    """
    コントローラーのカーブ形状(CVのローカル座標)をjsonへ書き出す。

    Parameters
    ----------
        string path : 出力先jsonパス
        list targets : 対象を絞るノード(target_controllers参照)。省略可

    Returns
    -------
        int : 書き出したコントローラー数
    """
    if(not path):
        cmds.warning("出力先が指定されていません")
        return 0

    objs = target_controllers(targets)
    data = {}
    for obj in objs:
        shapes = cmds.listRelatives(obj,shapes=True,type="nurbsCurve",fullPath=True) or []
        if(not shapes):
            continue
        data[obj.split("|")[-1]] = [_get_shape_data(s) for s in shapes]

    with open(path,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

    print(f"{len(data)}個のコントローラー形状を書き出しました : {path}")
    return len(data)

def import_shapes(path:str, targets=None):
    """
    export_shapesで書き出したjsonを読み込み、名前が一致するコントローラーへCV座標を書き戻す。
    同名のコントローラーが複数見つかり絞り込めない場合(同じシーンに複数キャラクターがいる等)は
    警告してスキップするので、対象キャラクターのコントローラーかリグのトップグループを
    選択してから実行する。

    Parameters
    ----------
        string path : 読み込むjsonパス
        list targets : 適用先を絞るノード(target_controllers参照)。省略可

    Returns
    -------
        (int,int) : (適用できた数, スキップした数)
    """
    if(not path):
        cmds.warning("入力元が指定されていません")
        return (0,0)

    with open(path,"r",encoding="utf-8") as f:
        data = json.load(f)

    #target_controllersは対象が1件も無ければ常にシーン内の全Con_*へフォールバックするため、
    #ここでは常にその結果だけを対象にすればよい(「絞り込み無し」を別扱いする必要が無い)
    scope = target_controllers(targets)
    scope_by_name = {}
    for o in scope:
        scope_by_name.setdefault(o.split("|")[-1],[]).append(o)

    applied=0
    skipped=0
    cmds.undoInfo(openChunk=True,chunkName="AutoRigForHumanoid_ImportControlShapes")
    try:
        for short_name,shape_list in data.items():
            candidates = scope_by_name.get(short_name,[])

            if(not candidates):
                cmds.warning(f"{short_name} : 対象が見つからないためスキップしました")
                skipped+=1
                continue
            if(len(candidates)>1):
                cmds.warning(f"{short_name} : 対象が{len(candidates)}個あり絞り込めないためスキップしました(対象のコントローラーかリグのトップグループを選択してから実行してください)")
                skipped+=1
                continue

            obj = candidates[0]
            shapes = cmds.listRelatives(obj,shapes=True,type="nurbsCurve",fullPath=True) or []
            if(len(shapes)!=len(shape_list)):
                cmds.warning(f"{obj} : シェイプの数が保存時と異なるためスキップしました(保存時{len(shape_list)}個 → 現在{len(shapes)}個)")
                skipped+=1
                continue

            results = [_apply_shape_data(s,d) for s,d in zip(shapes,shape_list)]
            if(all(results)):
                applied+=1
            else:
                skipped+=1
    finally:
        cmds.undoInfo(closeChunk=True)

    print(f"{applied}個のコントローラー形状を適用しました({skipped}個スキップ) : {path}")
    return (applied,skipped)

def browse_export_path(path_field:str):
    """
    書き出し先jsonパスの選択ダイアログを開き、結果をtextFieldへ書き込む。

    Parameters
    ----------
        string path_field : 書き込み先のtextField

    Returns
    -------
        無し
    """
    path = cmds.fileDialog2(fileMode=0,caption="Export Control Shapes",fileFilter="Json Files (*.json)")
    if(path):
        cmds.textField(path_field,edit=True,tx=path[0])

def browse_import_path(path_field:str):
    """
    読み込むjsonパスの選択ダイアログを開き、結果をtextFieldへ書き込む。

    Parameters
    ----------
        string path_field : 書き込み先のtextField

    Returns
    -------
        無し
    """
    path = cmds.fileDialog2(fileMode=1,caption="Import Control Shapes",fileFilter="Json Files (*.json)")
    if(path):
        cmds.textField(path_field,edit=True,tx=path[0])
