import numpy as np
from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtCore import QEvent, QRect, Qt
from qgis.PyQt.QtGui import QBrush, QColor, QFont, QFontMetrics, QPainter, QPixmap
from qgis.PyQt.QtWidgets import (
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QSpacerItem,
    QStyledItemDelegate,
    QStyleOptionButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from threedi_models_simulations.utils.general import ScientificDoubleDelegate


class ColorIndicatorLabel(QLabel):
    def __init__(self, text, circle_color, parent):
        super().__init__(parent)
        self.text = text
        self.circle_color = circle_color
        self.setStyleSheet("background: transparent;")

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()

        circle_diameter = int(h * 0.8)
        spacing = int(h * 0.2)
        circle_x = int(h * 0.1)
        circle_y = (h - circle_diameter) // 2
        painter.setBrush(QBrush(self.circle_color))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(circle_x, circle_y, circle_diameter, circle_diameter)

        # Configure text
        painter.setPen(Qt.black)
        font = self.font()
        painter.setFont(font)
        fm = QFontMetrics(font)
        text_height = fm.ascent()
        text_x = circle_x + circle_diameter + spacing
        text_y = (h + text_height) // 2 - 2

        painter.drawText(text_x, text_y, self.text)
        painter.end()


class DuplicateNodeDialog(QDialog):
    def __init__(
        self, current_node_ids, current_values, new_node_ids, new_values, parent
    ):
        super().__init__(parent)
        self.setWindowTitle("Loaded node ID's")
        layout = QGridLayout(self)
        self.setLayout(layout)

        self.table = QTableWidget(self)
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(
            ["Active", "New node ID", "New value", "Existing value"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        # self.table.customContextMenuRequested.connect(self.menu_requested)
        self.table.installEventFilter(self)

        delegate = ScientificDoubleDelegate(self.table, decimals=2)
        self.table.setItemDelegateForColumn(1, delegate)
        self.table.setItemDelegateForColumn(2, delegate)
        self.table.setColumnWidth(0, 40)

        assert len(current_node_ids) == len(current_values)
        assert len(new_node_ids) == len(new_values)

        # Find duplicate indexes and values
        self.duplicate_idxs = np.arange(len(new_node_ids))[
            np.in1d(new_node_ids, current_node_ids)
        ]

        contains_duplicates = False
        duplicate_color = QColor("#FFD27E")

        # Fill the page with the current model
        for idx, (new_node_id, new_value) in enumerate(zip(new_node_ids, new_values)):
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            check_item.setCheckState(Qt.Checked)
            node_item = QTableWidgetItem(str(new_node_id))
            node_item.setFlags(node_item.flags() & ~Qt.ItemIsEditable)
            value_item = QTableWidgetItem(str(new_value))
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(row_position, 0, check_item)
            self.table.setItem(row_position, 1, node_item)
            self.table.setItem(row_position, 2, value_item)

            item = QTableWidgetItem()
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)

            if idx in self.duplicate_idxs:
                node_item.setBackground(duplicate_color)
                value_item.setBackground(duplicate_color)

                item = QTableWidgetItem(str(current_values[idx]))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setBackground(duplicate_color)

            self.table.setItem(row_position, 3, item)

        layout.addWidget(self.table)

        duplicate_frame = QFrame(self)
        duplicate_frame.setFrameShape(
            QFrame.Panel
        )  # Box, Panel, StyledPanel, HLine, VLine
        duplicate_frame.setFrameShadow(QFrame.Raised)
        duplicate_layout = QGridLayout()
        duplicate_frame.setLayout(duplicate_layout)
        if len(self.duplicate_idxs) == 0:
            duplicate_frame.hide()

        label = ColorIndicatorLabel(
            "Item already present in current table", duplicate_color, duplicate_frame
        )
        label.setFixedWidth(210)
        duplicate_layout.addWidget(label, 0, 0)

        duplicate_layout.addItem(
            QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 1
        )

        toggle_button = QPushButton("Toggle duplicate node selection", duplicate_frame)
        toggle_button.setFixedWidth(200)
        duplicate_layout.addWidget(toggle_button, 0, 2)
        toggle_button.clicked.connect(self.toggle_duplicates)

        message_label = QLabel(
            "Warning: the file contains nodes with different values than currently in the table. These will be overwritten when not deselected.",
            duplicate_frame,
        )
        message_label.setStyleSheet(
            "background-color: #FFD27E; border: 1px solid orange; border-radius: 5px;"
        )
        message_label.setWordWrap(True)
        duplicate_layout.addWidget(message_label, 1, 0, 1, 3)

        layout.addWidget(duplicate_frame)

        buttons_layout = QHBoxLayout()
        self.pb_cancel = QPushButton("Cancel")
        buttons_layout.addWidget(self.pb_cancel)
        buttons_layout.addSpacerItem(
            QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        )
        self.pb_cancel.clicked.connect(self.reject)
        self.pb_add = QPushButton("Add values")
        buttons_layout.addWidget(self.pb_add)
        layout.addLayout(buttons_layout, 3, 0, 1, 1)

        self.resize(600, 600)

    def toggle_duplicates(self):
        # Iterate over rows, check whether id is in duplicates -> toggles
        pass

    def collect_nodes(self):
        # Iterate over rows, collect checked values
        self.accept()

    def eventFilter(self, obj, event):
        if obj == self.table and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Space:
                selected_rows = set(
                    index.row() for index in self.table.selectedIndexes()
                )
                for row in selected_rows:
                    item = self.table.item(row, 0)
                    current_state = item.checkState()
                    new_state = (
                        Qt.Unchecked if current_state == Qt.Checked else Qt.Checked
                    )
                    item.setCheckState(new_state)
                return True  # event handled
        return super().eventFilter(obj, event)
