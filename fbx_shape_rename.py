from maya import cmds
from maya import OpenMaya
import importlib
import json

def import_path(path_list:list):
    path = cmds.fileDialog2(
        fileMode=1,
        caption="Select FBX(ASCII)",
        fileFilter="FBX Files (*.fbx)"
    )

    if len(path)!=0:
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

    if len(path)!=0:
        cmds.textField(path_list[1],edit=True,tx=path[0])

def export_path(path_list:list):
    path = cmds.fileDialog2(
        fileMode=0,
        caption="Export FBX",
        fileFilter="FBX Files (*.fbx)"
    )

    if len(path)!=0:
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

    shape_name_dict = {name: name for name in shape_name_list}

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
                    print(f"{value} は {key} と {i} で重複しています")

        if len(error) == 0:
            main(json_load, path_list, mode)

def main(blendshape_dict:dict, path_list:list, mode:int):
    with open(path_list[0], 'r', encoding='utf-8', errors='ignore') as f:
        fbx = f.readlines()

        for line_number, line in enumerate(fbx):
            for key in blendshape_dict:

                check_dict = {f'P: "{key}", "Number", "", "A",0' : f'P: "{blendshape_dict[key]}", "Number", "", "A",0',
                              f'"Geometry::{key}", "Shape"' : f'"Geometry::{blendshape_dict[key]}", "Shape"',
                              f' "SubDeformer::{key}", "BlendShapeChannel" ' : f' "SubDeformer::{blendshape_dict[key]}", "BlendShapeChannel" ',
                              f';SubDeformer::{key}, Deformer::' : f';SubDeformer::{blendshape_dict[key]}, Deformer::',
                              f';Geometry::{key}, SubDeformer::{key}' : f';Geometry::{blendshape_dict[key]}, SubDeformer::{blendshape_dict[key]}'}

                for word in check_dict:
                    if mode==1:
                        if word in line:
                            fbx[line_number] = line.replace(word, check_dict[word])
                            print(word+"を"+check_dict[word]+"に置き換え")
                    elif mode==2:
                        if check_dict[word] in line:
                            fbx[line_number] = line.replace(check_dict[word], word)
                            print(check_dict[word] + "を" + word + "に置き換え")

        with open(path_list[2], 'w', encoding='utf-8') as f:
            f.writelines(fbx)

def export_fbx_init(path_list:list,mode:int):
    path=[]
    path.append(cmds.textField(path_list[0],q=True,tx=True))
    path.append(cmds.textField(path_list[1],q=True,tx=True))
    path.append(cmds.textField(path_list[2],q=True,tx=True))
    check_json(path, mode)