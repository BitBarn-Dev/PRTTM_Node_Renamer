from PySide2 import QtWidgets, QtCore
import re

class ObjectWidget(QtWidgets.QWidget):
    preview_updated = QtCore.Signal()

    def __init__(self, obj_name, parent=None):
        super().__init__(parent)
        self.obj_name = obj_name
        self.original_name = obj_name
        self.is_valid = self.validate_name(obj_name)
        self.create_ui()

    def create_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        top_layout = QtWidgets.QHBoxLayout()
        main_layout.addLayout(top_layout)

        # Checkbox
        self.checkbox = QtWidgets.QCheckBox()
        self.checkbox.setChecked(False)  # Unchecked by default
        self.checkbox.setEnabled(False)  # Disable user interaction
        top_layout.addWidget(self.checkbox)

        # Left/Right/Center Dropdown
        self.lrc_dropdown = QtWidgets.QComboBox()
        self.lrc_dropdown.addItems(["L", "R", "C"])
        top_layout.addWidget(self.lrc_dropdown)

        # Name LineEdit
        self.name_lineedit = QtWidgets.QLineEdit()
        top_layout.addWidget(self.name_lineedit)

        # Object Type Dropdown
        self.type_dropdown = QtWidgets.QComboBox()
        self.type_dropdown.addItems(["GEO", "JNT", "CTRL"])
        top_layout.addWidget(self.type_dropdown)

        # Status Label
        self.status_label = QtWidgets.QLabel()
        top_layout.addWidget(self.status_label)

        # Preview Label
        self.preview_label = QtWidgets.QLabel()
        self.preview_label.setVisible(False)
        main_layout.addWidget(self.preview_label)

        self.populate_fields()
        self.update_status()

        # Connect signals
        self.lrc_dropdown.currentIndexChanged.connect(self.on_widget_changed)
        self.name_lineedit.textChanged.connect(self.on_widget_changed)
        self.type_dropdown.currentIndexChanged.connect(self.on_widget_changed)

    def validate_name(self, name):
        pattern = r'^([CLR])_([a-zA-Z0-9]+)_(GEO|JNT|CTRL)$'
        return bool(re.match(pattern, name))

    def populate_fields(self):
        if self.is_valid:
            parts = self.obj_name.split('_')
            self.lrc_dropdown.setCurrentText(parts[0])
            self.name_lineedit.setText(parts[1])
            self.type_dropdown.setCurrentText(parts[2])
        else:
            self.name_lineedit.setText(self.obj_name)
            # Set default values for invalid names
            self.lrc_dropdown.setCurrentText("C")
            self.type_dropdown.setCurrentText("GEO")

    def on_widget_changed(self):
        self.update_preview()
        self.update_status()
        self.preview_updated.emit()

    def update_preview(self):
        cleaned_name = self.clean_name(self.name_lineedit.text())
        new_name = f"{self.lrc_dropdown.currentText()}_{cleaned_name}_{self.type_dropdown.currentText()}"
        self.is_valid = self.validate_name(new_name)
        self.preview_label.setText(f"Preview: {new_name}")

    def clean_name(self, name):
        # Remove illegal characters and spaces
        return re.sub(r'[^a-zA-Z0-9]', '', name)

    def update_status(self):
        if not self.is_valid:
            self.status_label.setText("Invalid")
            self.status_label.setStyleSheet("color: red;")
            self.checkbox.setChecked(False)
            self.preview_label.setVisible(False)
        elif self.has_changed():
            self.status_label.setText("Modified")
            self.status_label.setStyleSheet("color: orange;")
            self.checkbox.setChecked(True)
            self.preview_label.setVisible(True)
        else:
            self.status_label.setText("Valid")
            self.status_label.setStyleSheet("color: green;")
            self.checkbox.setChecked(False)
            self.preview_label.setVisible(False)
        
        self.updateGeometry()
        self.parent().parent().updateGeometry()

    def get_combined_name(self):
        cleaned_name = self.clean_name(self.name_lineedit.text())
        return f"{self.lrc_dropdown.currentText()}_{cleaned_name}_{self.type_dropdown.currentText()}"

    def has_changed(self):
        return self.get_combined_name() != self.original_name

    def is_checked(self):
        return self.checkbox.isChecked()

    def sizeHint(self):
        size = super().sizeHint()
        if self.preview_label.isVisible():
            size.setHeight(size.height() + self.preview_label.sizeHint().height())
        return size