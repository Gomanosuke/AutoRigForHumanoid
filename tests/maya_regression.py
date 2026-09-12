"""Run with mayapy; pass an output directory for disposable scene backups."""
import json
import math
import pathlib
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))
import maya.standalone
maya.standalone.initialize(name='python')
from maya import cmds
from AutoRigForHumanoid import autorig_createBase as base, autorig_utility as utility

output = pathlib.Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=True)
for plugin in ('matrixNodes', 'quatNodes', 'lookdevKit'):
    cmds.loadPlugin(plugin)

def backup(label):
    path = output / (label + '.mb')
    if path.exists():
        raise FileExistsError(path)
    cmds.file(rename=str(path))
    cmds.file(save=True, type='mayaBinary')
    assert path.stat().st_size > 0

def matrix(obj):
    return cmds.xform(obj, q=True, ws=True, m=True)

def error(left, right):
    return max(abs(a-b) for a,b in zip(left,right))

results = {}
for axis in range(3):
    for sign in (-1, 1):
        cmds.file(new=True, force=True)
        direction = [0.0]*3
        direction[axis] = 5.0*sign
        root = cmds.joint(p=(0,0,0))
        middle = cmds.joint(p=direction)
        end = cmds.joint(p=[2*v for v in direction])
        backup('straight_%d_%s' % (axis, 'positive' if sign>0 else 'negative'))
        utility.set_ik_preferred_angle(middle, end)
        handle = cmds.ikHandle(sj=root, ee=end, sol='ikRPsolver')[0]
        cmds.xform(handle, ws=True, t=[v for v in direction])
        position = cmds.xform(end, q=True, ws=True, t=True)
        assert math.dist(position,direction)<1e-5, (axis,sign,position)
        assert max(abs(v) for v in cmds.getAttr(middle+'.rotate')[0])>10
        results['straight_%d_%d'%(axis,sign)] = True

for order in range(6):
    cmds.file(new=True, force=True)
    root = cmds.joint(name='sourceRoot',p=(0,0,0))
    child = cmds.joint(name='sourceChild',p=(0,5,0))
    for node in (root,child):
        cmds.setAttr(node+'.rotateOrder',order)
        cmds.setAttr(node+'.rotate',13,27,-19)
        cmds.setAttr(node+'.jointOrient',9,-15,21)
    parent=cmds.group(empty=True,name='rig')
    expected={n:matrix(n) for n in (root,child)}
    backup('rotate_order_%d'%order)
    base.create_dummyHumanoid({'c_hips':root,'c_spine':child},'sample',parent)
    drift=max(error(expected[n],matrix(n)) for n in expected)
    assert drift<1e-8,(order,drift)
    results['rotate_order_%d'%order]=drift

for undo_enabled in (True,False):
    cmds.file(new=True,force=True)
    cmds.joint(name='sourceRoot',p=(0,0,0))
    cmds.group(empty=True,name='Orient_C_sample')
    cmds.group(empty=True,name='Position_C_sample')
    backup('rollback_'+str(undo_enabled))
    cmds.undoInfo(state=undo_enabled)
    expected_nodes=set(cmds.ls())
    expected_matrix=matrix('sourceRoot')
    original_check=base.autorig_preparation.check_textfield
    original_field=cmds.textField
    original_build=base.create_dummyHumanoid
    original_refresh=cmds.refresh
    refresh_calls=[]
    def checked_refresh(*args,**kwargs):
        # Batch mode can silently accept flags rejected by interactive Maya.
        assert not any(flag in kwargs for flag in ('q','query','e','edit'))
        refresh_calls.append(kwargs.copy())
        return original_refresh(*args,**kwargs)
    cmds.refresh=checked_refresh
    base.autorig_preparation.check_textfield=lambda *args:(True,{'c_hips':'sourceRoot'})
    cmds.textField=lambda *args,**kwargs:'sample'
    def fail(*args):
        cmds.setAttr('sourceRoot.jointOrientX',37)
        raise RuntimeError('injected build failure')
    base.create_dummyHumanoid=fail
    try:
        try:
            base.create_rig({},'name')
            raise AssertionError('Expected build failure')
        except RuntimeError as exc:
            assert str(exc)=='injected build failure'
        assert set(cmds.ls())==expected_nodes
        assert error(expected_matrix,matrix('sourceRoot'))<1e-10
        assert cmds.undoInfo(q=True,state=True)==undo_enabled
        assert refresh_calls==[{'suspend':True},{'suspend':False},{}]
        results['rollback_'+str(undo_enabled)]=True
    finally:
        base.autorig_preparation.check_textfield=original_check
        cmds.textField=original_field
        base.create_dummyHumanoid=original_build
        cmds.refresh=original_refresh

cmds.file(new=True,force=True)
node=cmds.createNode('transform')
cmds.addAttr(node,longName='twist',attributeType='double')
cmds.setAttr(node+'.twist',23)
backup('twist_exception')
try:
    utility.ik_twist_offset(node,'missing_object',[1.0]*16)
    raise AssertionError('Expected query failure')
except ValueError:
    pass
assert cmds.getAttr(node+'.twist')==23
results['twist_exception_restored']=True
(output/'results.json').write_text(json.dumps(results,indent=2))
print('REGRESSION_PASS',len(results),flush=True)
maya.standalone.uninitialize()
