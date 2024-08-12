from PySide2 import QtWidgets, QtCore
import maya.cmds as cmds
import re

from .object_widget import ObjectWidget
from .selection_set_editor import SelectionSetEditor

class ObjectNamerTool(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Object Namer Tool")
        self.setGeometry(100, 100, 400, 400)
        self.create_ui()

    def create_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)

        # Dropdown for selection sets
        self.selection_set_dropdown = QtWidgets.QComboBox()
        self.selection_set_dropdown.addItem("Select a set...")
        self.selection_set_dropdown.addItem("<create/edit>")
        self.selection_set_dropdown.addItems(self.get_selection_sets())
        self.selection_set_dropdown.currentIndexChanged.connect(self.handle_selection_change)
        main_layout.addWidget(self.selection_set_dropdown)

        # List widget to hold ObjectWidgets
        self.object_list_widget = QtWidgets.QListWidget()
        main_layout.addWidget(self.object_list_widget)

        # Preview label
        self.preview_label = QtWidgets.QLabel("Preview:")
        main_layout.addWidget(self.preview_label)

        # Apply All Changes button
        self.apply_button = QtWidgets.QPushButton("Apply All Changes")
        self.apply_button.clicked.connect(self.apply_all_changes)
        main_layout.addWidget(self.apply_button)

    def get_selection_sets(self):
        sets = cmds.ls(type='objectSet')
        return sets

    def handle_selection_change(self, index):
        if self.selection_set_dropdown.currentText() == "<create/edit>":
            self.launch_selection_set_editor()
        else:
            self.populate_objects()

    def launch_selection_set_editor(self):
        dialog = SelectionSetEditor(self)
        result = dialog.exec_()
        if result == QtWidgets.QDialog.Accepted:
            selected_set = dialog.get_selected_set()
            self.refresh_selection_sets(selected_set)

    def refresh_selection_sets(self, selected_set=None):
        current_index = self.selection_set_dropdown.currentIndex()
        self.selection_set_dropdown.clear()
        self.selection_set_dropdown.addItem("Select a set...")
        self.selection_set_dropdown.addItem("<create/edit>")
        self.selection_set_dropdown.addItems(self.get_selection_sets())
        
        if selected_set:
            index = self.selection_set_dropdown.findText(selected_set)
            if index != -1:
                self.selection_set_dropdown.setCurrentIndex(index)
            else:
                self.selection_set_dropdown.setCurrentIndex(0)
        else:
            self.selection_set_dropdown.setCurrentIndex(current_index)

    def populate_objects(self):
        self.object_list_widget.clear()
        selected_set = self.selection_set_dropdown.currentText()

        if selected_set not in ["Select a set...", "<create/edit>"]:
            objects = cmds.sets(selected_set, q=True)

            if objects:
                for obj in objects:
                    # Get the transform node if the object is a shape
                    if cmds.objectType(obj) == 'mesh':
                        transform = cmds.listRelatives(obj, parent=True, type='transform')
                        if transform:
                            obj = transform[0]
                    
                    if cmds.objectType(obj) == 'transform':
                        self.add_object_widget(obj)
            else:
                print(f"No objects found in the selection set '{selected_set}'.")

    def add_object_widget(self, obj_name):
        object_widget = ObjectWidget(obj_name, self)
        object_widget.preview_updated.connect(self.update_preview)
        list_item = QtWidgets.QListWidgetItem(self.object_list_widget)
        list_item.setSizeHint(object_widget.sizeHint())
        self.object_list_widget.addItem(list_item)
        self.object_list_widget.setItemWidget(list_item, object_widget)

    def update_preview(self):
        combined_strings = [
            self.object_list_widget.itemWidget(self.object_list_widget.item(index)).get_combined_name()
            for index in range(self.object_list_widget.count())
            if self.object_list_widget.itemWidget(self.object_list_widget.item(index)).is_checked()
        ]
        self.preview_label.setText("Preview: " + ", ".join(combined_strings))
        self.updateGeometry()

    def apply_all_changes(self):
        all_valid = True
        for index in range(self.object_list_widget.count()):
            object_widget = self.object_list_widget.itemWidget(self.object_list_widget.item(index))
            if object_widget.is_checked() and not object_widget.is_valid:
                all_valid = False
                break

        if not all_valid:
            QtWidgets.QMessageBox.warning(self, "Invalid Names", "Please correct all invalid names before applying changes.")
            return

        for index in range(self.object_list_widget.count()):
            object_widget = self.object_list_widget.itemWidget(self.object_list_widget.item(index))
            if object_widget.is_checked() and object_widget.has_changed():
                old_name = object_widget.obj_name
                new_name = object_widget.get_combined_name()
                cmds.rename(old_name, new_name)
        
        # Refresh the tool
        self.populate_objects()

    def sizeHint(self):
        size = super().sizeHint()
        for index in range(self.object_list_widget.count()):
            item = self.object_list_widget.item(index)
            widget = self.object_list_widget.itemWidget(item)
            size.setHeight(size.height() + widget.sizeHint().height())
        return size