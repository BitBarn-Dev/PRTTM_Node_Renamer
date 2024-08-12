import sys
import os
import importlib
from PySide2 import QtWidgets, QtCore
import maya.OpenMayaUI as apiUI
from shiboken2 import wrapInstance

# Import your custom classes
from PRTTM_Node_Renamer.src.views.object_namer_tool import ObjectNamerTool
from PRTTM_Node_Renamer.src.views.object_widget import ObjectWidget
from PRTTM_Node_Renamer.src.views.selection_set_editor import SelectionSetEditor

# Function to retrieve the Maya main window
def get_maya_main_window():
    """Retrieve the main Maya window as a Qt widget."""
    ptr = apiUI.MQtUtil.mainWindow()
    if ptr is not None:
        return wrapInstance(int(ptr), QtWidgets.QWidget)
    raise RuntimeError("Could not find the Maya main window.")

def setup_paths():
    """Set up the paths for the current directory and the views folder."""
    current_dir = os.path.dirname(__file__)
    
    if current_dir not in sys.path:
        sys.path.append(current_dir)

    views_path = os.path.join(current_dir, 'views')
    if views_path not in sys.path:
        sys.path.append(views_path)

def main():
    """Main function to initialize and show the ObjectNamerTool."""
    setup_paths()

    # Reload the modules to ensure changes are reflected
    importlib.reload(sys.modules['PRTTM_Node_Renamer.src.views.object_namer_tool'])
    importlib.reload(sys.modules['PRTTM_Node_Renamer.src.views.object_widget'])
    importlib.reload(sys.modules['PRTTM_Node_Renamer.src.views.selection_set_editor']) 

    # Get the existing QApplication instance or create one if none exists
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)

    # Get the Maya main window to parent the UI
    maya_main_window = get_maya_main_window()

    try:
        object_namer_ui.close()  # Close the old window if it exists
    except Exception:
        pass

    object_namer_ui = ObjectNamerTool(parent=maya_main_window)
    object_namer_ui.setWindowFlags(object_namer_ui.windowFlags() | QtCore.Qt.Window)
    object_namer_ui.show()

if __name__ == "__main__":
    main()
