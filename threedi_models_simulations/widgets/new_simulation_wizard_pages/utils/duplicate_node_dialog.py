import numpy as np
from qgis.core import Qgis, QgsMessageLog
from qgis.PyQt.QtCore import QRect, Qt
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
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            ["New node ID", "New value", "Existing value"]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        # self.table.setSelectionMode(QTableWidget.SingleSelection)
        # self.substance_table.customContextMenuRequested.connect(self.menu_requested)

        delegate = ScientificDoubleDelegate(self.table, decimals=2)
        self.table.setItemDelegateForColumn(1, delegate)
        self.table.setItemDelegateForColumn(2, delegate)

        assert len(current_node_ids) == len(current_values)
        assert len(new_node_ids) == len(new_values)

        # Find duplicate indexes and values
        duplicate_idxs = np.arange(len(new_node_ids))[
            np.in1d(new_node_ids, current_node_ids)
        ]

        contains_duplicates = False
        duplicate_color = QColor("#FFD27E")

        # Fill the page with the current model
        for idx, (new_node_id, new_value) in enumerate(zip(new_node_ids, new_values)):
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)

            node_item = QTableWidgetItem(str(new_node_id))
            value_item = QTableWidgetItem(str(new_value))
            node_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            node_item.setCheckState(Qt.Checked)

            self.table.setItem(row_position, 0, node_item)
            self.table.setItem(row_position, 1, value_item)

            if idx in duplicate_idxs:
                node_item.setBackground(duplicate_color)
                value_item.setBackground(duplicate_color)

            if idx in duplicate_idxs:
                contains_duplicates = True
                item = QTableWidgetItem(str(current_values[idx]))
                item.setBackground(duplicate_color)
                self.table.setItem(
                    row_position,
                    2,
                    item,
                )

        layout.addWidget(self.table)

        duplicate_frame = QFrame(self)
        duplicate_frame.setFrameShape(
            QFrame.Box
        )  # Box, Panel, StyledPanel, HLine, VLine
        duplicate_frame.setFrameShadow(QFrame.Raised)
        duplicate_layout = QGridLayout()
        duplicate_frame.setLayout(duplicate_layout)

        label = ColorIndicatorLabel(
            "Item already present in current table", duplicate_color, duplicate_frame
        )
        label.setFixedWidth(210)
        duplicate_layout.addWidget(label, 0, 0)
        if not contains_duplicates:
            label.hide()

        duplicate_layout.addItem(
            QSpacerItem(200, 20, QSizePolicy.Expanding, QSizePolicy.Minimum), 0, 1
        )

        toggle_button = QPushButton("Toggle duplicate node selection", duplicate_frame)
        toggle_button.setFixedWidth(200)
        duplicate_layout.addWidget(toggle_button, 0, 2)

        message_label = QLabel(
            "Warning: the file contains nodes with different values than currently in the table. These will be overwritten when not deselected.",
            self,
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
        self.pb_add = QPushButton("Add values")
        buttons_layout.addWidget(self.pb_add)
        layout.addLayout(buttons_layout, 3, 0, 1, 1)

        self.resize(600, 600)
