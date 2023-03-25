from PySide2.QtCore import (QMetaObject, QRect, QSize)
from PySide2.QtGui import QFont
from PySide2.QtWidgets import *


class ModLoaderUI(QMainWindow):
    # noinspection PyArgumentList
    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        if self.objectName():
            self.setObjectName('ModLoader')
        self.setFixedSize(QSize(811, 625))

        font = QFont()
        font.setPointSize(8)

        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName('centralwidget')
        self.setCentralWidget(self.centralwidget)

        self.menu_bar = QMenuBar(self)
        self.menu_bar.setObjectName('menu_bar')
        self.menu_bar.setGeometry(QRect(0, 0, 811, 26))
        self.setMenuBar(self.menu_bar)

        self.settings_menu = QMenu(self.menu_bar)
        self.settings_menu.setObjectName('settings_men')
        self.menu_bar.addAction(self.settings_menu.menuAction())

        self.auto_3dmigoto = QAction(self)
        self.auto_3dmigoto.setObjectName('auto_3dmigoto')
        self.auto_3dmigoto.setCheckable(True)
        self.settings_menu.addAction(self.auto_3dmigoto)

        self.content_tab = QTabWidget(self.centralwidget)
        self.content_tab.setObjectName('content_tab')
        self.content_tab.setGeometry(QRect(10, 10, 791, 578))

        self.manage = QWidget()
        self.manage.setObjectName('manage')
        self.create = QWidget()
        self.create.setObjectName('create')

        self.content_tab.addTab(self.manage, 'Manage')
        self.content_tab.addTab(self.create, 'Create')

        self.slots = QListWidget(self.manage)
        self.slots.setObjectName('slots')
        self.slots.setGeometry(QRect(10, 10, 601, 231))
        self.slots.setSortingEnabled(False)

        self.activate_btn = QPushButton(self.manage)
        self.activate_btn.setObjectName('activate_btn')
        self.activate_btn.setGeometry(QRect(630, 10, 141, 31))

        self.delete_btn = QPushButton(self.manage)
        self.delete_btn.setObjectName('delete_btn')
        self.delete_btn.setGeometry(QRect(630, 130, 141, 31))

        self.duplicate_btn = QPushButton(self.manage)
        self.duplicate_btn.setObjectName('duplicate_btn')
        self.duplicate_btn.setGeometry(QRect(630, 90, 141, 31))

        self.edit_btn = QPushButton(self.manage)
        self.edit_btn.setObjectName('edit_btn')
        self.edit_btn.setGeometry(QRect(630, 50, 141, 31))

        self.normal_mod_count = QLabel(self.manage)
        self.normal_mod_count.setObjectName('normal_mod_count')
        self.normal_mod_count.setGeometry(QRect(630, 200, 141, 21))
        self.normal_mod_count.setFont(font)

        self.merged_mod_count = QLabel(self.manage)
        self.merged_mod_count.setObjectName('merged_mod_count')
        self.merged_mod_count.setGeometry(QRect(630, 220, 141, 21))
        self.merged_mod_count.setFont(font)

        self.cur_active_mod = QLabel(self.manage)
        self.cur_active_mod.setObjectName('cur_active_mod')
        self.cur_active_mod.setGeometry(QRect(10, 250, 581, 21))
        self.cur_active_mod.setFont(font)

        self.slot_info_group = QGroupBox(self.manage)
        self.slot_info_group.setObjectName('slot_info_group')
        self.slot_info_group.setGeometry(QRect(-1, 290, 791, 261))

        self.slot_items = QTreeWidget(self.slot_info_group)
        self.slot_items.setObjectName('slot_items')
        self.slot_items.setGeometry(QRect(11, 20, 763, 201))
        self.slot_items.headerItem().setText(0, '')
        self.slot_items.header().setVisible(False)
        self.slot_items.setSortingEnabled(False)

        self.mod_type = QLabel(self.slot_info_group)
        self.mod_type.setObjectName('mod_type')
        self.mod_type.setGeometry(QRect(14, 230, 91, 21))
        self.mod_type.setFont(font)

        self.mod_key = QLabel(self.slot_info_group)
        self.mod_key.setObjectName('mod_key')
        self.mod_key.setGeometry(QRect(254, 230, 341, 21))
        self.mod_key.setFont(font)

        self.mod_size = QLabel(self.slot_info_group)
        self.mod_size.setObjectName('mod_size')
        self.mod_size.setGeometry(QRect(134, 230, 101, 21))
        self.mod_size.setFont(font)

        self.slot_name_label = QLabel(self.create)
        self.slot_name_label.setObjectName('slot_name_label')
        self.slot_name_label.setGeometry(QRect(90, 20, 71, 16))

        self.name_input = QLineEdit(self.create)
        self.name_input.setObjectName('name_input')
        self.name_input.setGeometry(QRect(160, 13, 441, 31))

        # TODO Delete this shit
        self.is_hidden = QCheckBox(self.create)
        self.is_hidden.setObjectName('is_hidden')
        self.is_hidden.setGeometry(QRect(610, 20, 81, 20))

        self.mod_label = QLabel(self.create)
        self.mod_label.setObjectName('mod_label')
        self.mod_label.setGeometry(QRect(90, 60, 71, 16))

        self.child_mod_label = QLabel(self.create)
        self.child_mod_label.setObjectName('child_mod_label')
        self.child_mod_label.setGeometry(QRect(340, 60, 71, 16))

        self.mod_list = QComboBox(self.create)
        self.mod_list.setObjectName('mod_list')
        self.mod_list.setGeometry(QRect(90, 80, 231, 31))

        self.child_mod_list = QComboBox(self.create)
        self.child_mod_list.setObjectName('child_mod_list')
        self.child_mod_list.setEnabled(False)
        self.child_mod_list.setGeometry(QRect(340, 80, 231, 31))

        self.c_mod_type = QLabel(self.create)
        self.c_mod_type.setObjectName('c_mod_type')
        self.c_mod_type.setGeometry(QRect(90, 120, 91, 16))

        self.c_mod_size = QLabel(self.create)
        self.c_mod_size.setObjectName('c_mod_size')
        self.c_mod_size.setGeometry(QRect(210, 120, 111, 16))

        self.c_mod_key = QLabel(self.create)
        self.c_mod_key.setObjectName('c_mod_key')
        self.c_mod_key.setGeometry(QRect(340, 120, 351, 16))

        self.add_btn = QPushButton(self.create)
        self.add_btn.setObjectName('add_btn')
        self.add_btn.setGeometry(QRect(590, 80, 101, 31))

        self.edit_mod_list = QTreeWidget(self.create)
        self.edit_mod_list.headerItem().setText(0, '')
        self.edit_mod_list.setObjectName('edit_mod_list')
        self.edit_mod_list.setGeometry(QRect(90, 150, 601, 321))
        self.edit_mod_list.header().setVisible(False)
        self.edit_mod_list.setSortingEnabled(False)

        self.note_label = QLabel(self.create)
        self.note_label.setObjectName('note_label')
        self.note_label.setGeometry(QRect(90, 480, 211, 16))

        self.cancel_button = QPushButton(self.create)
        self.cancel_button.setObjectName('cancel_button')
        self.cancel_button.setGeometry(QRect(160, 510, 221, 31))

        self.save_button = QPushButton(self.create)
        self.save_button.setObjectName('save_button')
        self.save_button.setGeometry(QRect(390, 510, 221, 31))

        self.retranslate_ui()
        QMetaObject.connectSlotsByName(self)

    def retranslate_ui(self):
        self.setWindowTitle('Mod Loader')

        self.auto_3dmigoto.setText('Auto launch 3dmigoto')
        self.activate_btn.setText('Activate')
        self.delete_btn.setText('Delete')
        self.duplicate_btn.setText('Duplicate')
        self.edit_btn.setText('Edit')

        self.normal_mod_count.setText('Normal mods:')
        self.merged_mod_count.setText('Merged mods:')
        self.slot_info_group.setTitle('Slot info')
        self.mod_type.setText('Type:')
        self.mod_key.setText('Key:')

        self.mod_size.setText('Size:')
        self.cur_active_mod.setText('Current active:')
        self.save_button.setText('Save')
        self.cancel_button.setText('Cancel')
        self.slot_name_label.setText('Slot name')

        self.mod_label.setText('Mod')
        self.child_mod_label.setText('Child mod')
        self.add_btn.setText('Add')
        self.note_label.setText('Note: Double click to delete an item')
        self.is_hidden.setText('Hidden')

        self.c_mod_type.setText('Type:')
        self.c_mod_size.setText('Size:')
        self.c_mod_key.setText('Key:')
        self.settings_menu.setTitle('Settings')
