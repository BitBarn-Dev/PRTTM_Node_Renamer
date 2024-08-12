import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui

class CustomListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super(CustomListWidget, self).__init__(parent)
        self.setAcceptDrops(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setDropIndicatorShown(True)

    def dragEnterEvent(self, event):
        print("Drag enter event")
        mime_data = event.mimeData()
        print(f"Mime formats: {mime_data.formats()}")
        event.accept()
        print("Drag enter accepted")

    def dragMoveEvent(self, event):
        event.accept()
        print("Drag move accepted")

    def dropEvent(self, event):
        print("Drop event triggered")
        mime_data = event.mimeData()
        print(f"Mime formats: {mime_data.formats()}")
        
        if mime_data.hasFormat('application/x-qabstractitemmodeldatalist'):
            print("Processing QAbstractItemModel data")
            model_data = mime_data.data('application/x-qabstractitemmodeldatalist')
            item_texts = self.decode_model_data(model_data)
            self.process_dropped_items(item_texts)
        elif mime_data.hasText():
            print(f"Processing text data: {mime_data.text()}")
            self.process_dropped_items([mime_data.text()])
        else:
            print("Unrecognized mime data format")
            for format in mime_data.formats():
                print(f"Data for {format}: {mime_data.data(format)}")
        
        event.accept()
        print("Drop event accepted")

    def decode_model_data(self, model_data):
        stream = QtCore.QDataStream(model_data)
        items = []
        while not stream.atEnd():
            row = stream.readInt32()
            column = stream.readInt32()
            map_items = stream.readInt32()
            for i in range(map_items):
                key = stream.readInt32()
                value = stream.readQVariant()
                if key == 0:  # Qt.DisplayRole
                    items.append(str(value))
        return items

    def process_dropped_items(self, items):
        print(f"Processing dropped items: {items}")
        current_items = set(self.item(i).text().strip().lower() for i in range(self.count()))
        
        for item_text in items:
            cleaned_text = item_text.strip()
            if cleaned_text and cleaned_text.lower() not in current_items:
                print(f"Adding new item: '{cleaned_text}'")
                self.addItem(cleaned_text)
                current_items.add(cleaned_text.lower())
            else:
                print(f"Duplicate or empty item, not adding: '{cleaned_text}'")
        
        print(f"Current items after drop: {[self.item(i).text() for i in range(self.count())]}")

    def dropMimeData(self, index, data, action):
        print(f"dropMimeData called: index={index}, action={action}")
        if data.hasFormat('application/x-qabstractitemmodeldatalist'):
            model_data = data.data('application/x-qabstractitemmodeldatalist')
            item_texts = self.decode_model_data(model_data)
            self.process_dropped_items(item_texts)
        elif data.hasText():
            self.process_dropped_items([data.text()])
        return True

class SelectionSetEditor(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selection Set Editor")
        self.setMinimumSize(800, 600)
        self.selected_set = None
        self.create_ui()
        self.populate_tree_widget()
        self.populate_list_widget_with_selection()

    def create_ui(self):
        main_layout = QtWidgets.QHBoxLayout(self)

        # Left panel
        left_panel = QtWidgets.QVBoxLayout()
        main_layout.addLayout(left_panel, 1)

        # Search bar
        self.search_bar = QtWidgets.QLineEdit()
        self.search_bar.setPlaceholderText("Search objects...")
        self.search_bar.textChanged.connect(self.filter_tree)
        left_panel.addWidget(self.search_bar)

        # Tree Widget
        self.tree_widget = QtWidgets.QTreeWidget()
        self.tree_widget.setHeaderLabel("Scene Hierarchy")
        self.tree_widget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.tree_widget.setDragEnabled(True)
        left_panel.addWidget(self.tree_widget)

        # Right panel
        right_panel = QtWidgets.QVBoxLayout()
        main_layout.addLayout(right_panel, 1)

        # Radio buttons
        radio_layout = QtWidgets.QHBoxLayout()
        self.create_edit_radio = QtWidgets.QRadioButton("Create/Edit")
        self.edit_existing_radio = QtWidgets.QRadioButton("Edit Existing")
        self.create_edit_radio.setChecked(True)
        radio_layout.addWidget(self.create_edit_radio)
        radio_layout.addWidget(self.edit_existing_radio)
        right_panel.addLayout(radio_layout)

        # Selection Set Dropdown
        self.set_dropdown = QtWidgets.QComboBox()
        self.set_dropdown.setEnabled(False)
        right_panel.addWidget(self.set_dropdown)

        # Line Edit for set name
        self.name_input = QtWidgets.QLineEdit()
        right_panel.addWidget(self.name_input)

        # List Widget
        self.list_widget = CustomListWidget()
        right_panel.addWidget(self.list_widget)

        # Remove Selected Button
        self.remove_button = QtWidgets.QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_selected_items)
        right_panel.addWidget(self.remove_button)

        # Commit Button
        self.commit_button = QtWidgets.QPushButton("Commit Changes")
        right_panel.addWidget(self.commit_button)

        # Connect signals
        self.create_edit_radio.toggled.connect(self.toggle_mode)
        self.edit_existing_radio.toggled.connect(self.toggle_mode)
        self.set_dropdown.currentIndexChanged.connect(self.load_selected_set)
        self.commit_button.clicked.connect(self.commit_changes)

    def populate_tree_widget(self):
        all_objects = sorted(cmds.ls(assemblies=True))
        for obj in all_objects:
            self.add_item_to_tree(obj, self.tree_widget.invisibleRootItem())

    def add_item_to_tree(self, obj, parent):
        item = QtWidgets.QTreeWidgetItem(parent, [obj])
        children = sorted(cmds.listRelatives(obj, children=True, type='transform') or [])
        for child in children:
            self.add_item_to_tree(child, item)

    def filter_tree(self):
        filter_text = self.search_bar.text().lower()
        self.filter_tree_item(self.tree_widget.invisibleRootItem(), filter_text)

    def filter_tree_item(self, item, filter_text):
        item_visible = False
        for i in range(item.childCount()):
            child = item.child(i)
            child_visible = self.filter_tree_item(child, filter_text)
            item_visible = item_visible or child_visible

        if filter_text in item.text(0).lower():
            item_visible = True

        item.setHidden(not item_visible)
        return item_visible

    def populate_list_widget_with_selection(self):
        selected_objects = cmds.ls(selection=True, long=True)
        self.list_widget.clear()
        self.list_widget.addItems(selected_objects)

    def toggle_mode(self):
        is_edit_mode = self.edit_existing_radio.isChecked()
        self.set_dropdown.setEnabled(is_edit_mode)
        self.name_input.setEnabled(not is_edit_mode)
        
        if is_edit_mode:
            self.populate_set_dropdown()
        else:
            self.populate_list_widget_with_selection()

    def populate_set_dropdown(self):
        self.set_dropdown.clear()
        sets = cmds.ls(type='objectSet')
        self.set_dropdown.addItems(sets)

    def load_selected_set(self):
        if self.edit_existing_radio.isChecked():
            selected_set = self.set_dropdown.currentText()
            if selected_set:
                set_members = cmds.sets(selected_set, q=True) or []
                self.list_widget.clear()
                self.list_widget.addItems(set_members)

    def remove_selected_items(self):
        for item in self.list_widget.selectedItems():
            self.list_widget.takeItem(self.list_widget.row(item))

    def commit_changes(self):
        objects_to_set = [self.list_widget.item(i).text() for i in range(self.list_widget.count())]
        
        # Filter out shape nodes
        objects_to_set = [obj for obj in objects_to_set if cmds.objectType(obj) != 'mesh']
        
        if self.create_edit_radio.isChecked():
            set_name = self.name_input.text().strip()
            if not set_name:
                QtWidgets.QMessageBox.warning(self, "Invalid Name", "Please enter a valid set name.")
                return
            try:
                cmds.sets(objects_to_set, name=set_name)
                QtWidgets.QMessageBox.information(self, "Success", f"Selection set '{set_name}' created/updated.")
                self.selected_set = set_name
                self.accept()
            except Exception as e:
                QtWidgets.QMessageBox.warning(self, "Error", f"Failed to create/update set: {str(e)}")
        else:
            selected_set = self.set_dropdown.currentText()
            if selected_set:
                try:
                    cmds.sets(clear=selected_set)
                    cmds.sets(objects_to_set, addElement=selected_set)
                    QtWidgets.QMessageBox.information(self, "Success", f"Selection set '{selected_set}' updated.")
                    self.selected_set = selected_set
                    self.accept()
                except Exception as e:
                    QtWidgets.QMessageBox.warning(self, "Error", f"Failed to update set: {str(e)}")

    def get_selected_set(self):
        return self.selected_set