from maya import cmds
import importlib

from . import gui

def show_window():
    importlib.reload(gui)
    gui.create_window()
