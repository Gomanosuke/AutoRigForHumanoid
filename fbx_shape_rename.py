from maya import cmds
import json
from pathlib import Path

#json読み込み
with open(f"{Path(__file__).resolve().parent}/blendshape_name.json", mode="rt", encoding="utf-8") as f:
    preset_dict = json.load(f)

def import_path(path_list:list):
    path = cmds.fileDialog2(
        fileMode=1,
        caption="Select FBX(ASCII)",
        fileFilter="FBX Files (*.fbx)"
    )

    if path:
        cmds.textField(path_list[0],edit=True,tx=path[0])
        file_name=path[0]
        file_name=file_name.replace("."+file_name.split(".")[-1],"")
        
        json_name=file_name+"_shapeList.json"
        cmds.textField(path_list[1],edit=True,tx=json_name)

        export_name=file_name+"_convert.fbx"
        cmds.textField(path_list[2],edit=True,tx=export_name)

def json_path(path_list:list):
    path = cmds.fileDialog2(
        fileMode=0,
        caption="Export Json",
        fileFilter="Json Files (*.json)"
    )

    if path:
        cmds.textField(path_list[1],edit=True,tx=path[0])

def export_path(path_list:list):
    path = cmds.fileDialog2(
        fileMode=0,
        caption="Export FBX",
        fileFilter="FBX Files (*.fbx)"
    )

    if path:
        cmds.textField(path_list[2],edit=True,tx=path[0])

def export_json(path_list:list):
    fbx_path=cmds.textField(path_list[0],q=True,tx=True)
    json_path=cmds.textField(path_list[1],q=True,tx=True)

    shape_name_list = []

    with open(fbx_path, 'r', encoding='utf-8', errors='ignore') as f:
        fbx = f.readlines()

    for line in fbx:
        if '"Shape"' in line and '"Geometry::' in line:
            # 分割処理
            parts = line.split('"Geometry::')
            if len(parts) > 1:
                shape_name = parts[1].split('"')[0]
                shape_name_list.append(shape_name)


    shape_name_dict = {}
    for shape_name in shape_name_list:
        if shape_name in preset_dict:
            shape_name_dict[shape_name]=preset_dict[shape_name]
        else:
            name=shape_name
            name=name.replace(".","_").replace("-","_")
            shape_name_dict[shape_name]=name


    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(shape_name_dict, f, ensure_ascii=False, indent=4, sort_keys=True)



def check_json(path_list:list, mode:int):
    with open(path_list[1], 'r', encoding='utf-8') as json_open:
        json_load = json.load(json_open)
        error = []
        for key in  json_load:
            value = json_load[key]
            for i in json_load:
                if value == json_load[i] and i!=key and value not in error:
                    error.append(value)
                    cmds.warning(f"{value} は {key} と {i} で重複しています")

        if len(error) == 0:
            main(json_load, path_list, mode)

def main(blendshape_dict:dict, path_list:list, mode:int):
    """
    FBX(ASCII)内のブレンドシェイプ名を一括置換する

    Parameters
    ----------
        dictionary blendshape_dict : {元の名前:変換後の名前}
        list path_list : [入力fbxパス, jsonパス, 出力fbxパス]
        int mode : 1で元→変換後、2で変換後→元(戻す)方向に置換する

    Returns
    -------
        無し
    """
    #置換パターンはblendshape_dictだけから決まり行の内容に依存しないため、
    #行ごとに作り直さずここで1回だけ構築する(元実装は行数×キー数回分ムダに再構築していて低速だった)
    replace_map = {}
    for key,new_key in blendshape_dict.items():
        replace_map.update({
            f'P: "{key}", "Number", "", "A",0' : f'P: "{new_key}", "Number", "", "A",0',
            f'"Geometry::{key}", "Shape"' : f'"Geometry::{new_key}", "Shape"',
            f' "SubDeformer::{key}", "BlendShapeChannel" ' : f' "SubDeformer::{new_key}", "BlendShapeChannel" ',
            f';SubDeformer::{key}, Deformer::' : f';SubDeformer::{new_key}, Deformer::',
            f';Geometry::{key}, SubDeformer::' : f';Geometry::{new_key}, SubDeformer::',
            f'Channel: "{key}" ' : f'Channel: "{new_key}" ',
            f'Shape: "{key}" ' : f'Shape: "{new_key}" ',
            f'Property: "{key}", "Number", "A+N",0' : f'Property: "{new_key}", "Number", "A+N",',
            f'P: "RootGroup|{key}", "KString", "", "", ""' : f'P: "RootGroup|{new_key}", "KString", "", "", ""',
            f'Property: "{key}", "Number", "AN",0' : f'Property: "{new_key}", "Number", "AN",',
        })

    with open(path_list[0], 'r', encoding='utf-8', errors='ignore') as f:
        fbx = f.readlines()

    for line_number in range(len(fbx)):
        for word,replaced in replace_map.items():
            #mode==1: 元→変換後 / mode==2: 変換後→元 の順で探索元・置換先を入れ替える
            src,dst = (word,replaced) if mode==1 else (replaced,word)
            #置換前は毎回fbx[line_number]を参照する(同じ行で複数パターンに一致しても取りこぼさないため)
            if(src in fbx[line_number]):
                fbx[line_number] = fbx[line_number].replace(src,dst)
                print(f"{src}を{dst}に置き換え")

    with open(path_list[2], 'w', encoding='utf-8') as f:
        f.writelines(fbx)

def export_fbx_init(path_list:list,mode:int):
    path=[]
    path.append(cmds.textField(path_list[0],q=True,tx=True))
    path.append(cmds.textField(path_list[1],q=True,tx=True))
    path.append(cmds.textField(path_list[2],q=True,tx=True))
    check_json(path, mode)

def import_fbx():
    path = cmds.fileDialog2(
    fileMode=1,
    caption="Select FBX",
    fileFilter="FBX Files (*.fbx)"
    )[0]
    cmds.file(path,i=True,typ="FBX")

def fix_skin_scale_offset():
    sel = cmds.ls(sl=True, typ="transform")
    if not sel:
        cmds.warning("Jointを選択してください")
        return
    
    parent = sel[0]
    scale = cmds.getAttr(f"{parent}.sx")
    
    # 1. 子供のジョイントを取得（親自身も含む）
    child_joints = cmds.listRelatives(parent, ad=True, f=True, typ="joint") or []
    if cmds.nodeType(parent) == "joint":
        child_joints.append(parent)

    # 2. 各ジョイントの座標を修正
    for obj in child_joints:
        # 座標をスケール分オフセット（ここまでは同じ）
        for attr in ['tx', 'ty', 'tz']:
            val = cmds.getAttr(f"{obj}.{attr}")
            cmds.setAttr(f"{obj}.{attr}", val * scale)

    # 3. 親のスケールを1に戻す（ここで一旦見た目が変わるが、次で直る）
    cmds.setAttr(f"{parent}.sx", 1)
    cmds.setAttr(f"{parent}.sy", 1)
    cmds.setAttr(f"{parent}.sz", 1)

    # 4. スキンクラスターの bindPreMatrix を「現在の正しい状態」に強制同期
    for obj in child_joints:
        # 現在の「正しい見た目」の逆行列を取得
        current_inv_mat = cmds.getAttr(f"{obj}.worldInverseMatrix[0]")
        
        # 接続されているスキンクラスターを全て更新
        conns = cmds.listConnections(f"{obj}.worldMatrix[0]", p=True, d=True, type='skinCluster') or []
        for conn in conns:
            sc_node = conn.split('.')[0]
            index = conn.split('[')[-1].split(']')[0]
            
            # ここで新しい行列を書き込む（これで痩せたメッシュが元に戻る）
            cmds.setAttr(f"{sc_node}.bindPreMatrix[{index}]", current_inv_mat, type="matrix")