import maya.cmds as cmds

def fix_skin_scale_offset():
    sel = cmds.ls(sl=True, typ="transform")
    if not sel:
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

fix_skin_scale_offset()