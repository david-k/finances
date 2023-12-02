import sys
import os
import datetime
import sqlite3
from decimal import Decimal

from PyQt6.QtWidgets import (QApplication,
                             QMainWindow,
                             QWidget,
                             QTableWidget,
                             QTableWidgetItem,
                             QHeaderView,
                             QAbstractItemView,
                             QDialog,
                             QDialogButtonBox,
                             QLabel,
                             QFormLayout,
                             QGroupBox,
                             QPushButton,
                             QVBoxLayout)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor

import schwifty


# Utils
#===================================================================================================
def fmt_money(v):
    return "{:.2f}€".format(Decimal(v) / 100)


def build_remote_name(tx):
    remote_name_parts = []
    if tx["ultimate_debtor"]:
        remote_name_parts.append(tx["ultimate_debtor"])
    elif tx["remote_name"]:
        remote_name_parts.append(tx["remote_name"])

    if tx["remote_account"]:
        remote_name_parts.append(tx["remote_account"].split(":")[-1])

    if not remote_name_parts:
        # Credit card transactions don't have a remote account. Thus, we use the first line of
        # the puspose field, which usually contains the information we want
        remote_name_parts.append(tx["purpose"].split("\n")[0])

    return "\n".join(remote_name_parts)


# GUI classes
#===================================================================================================
class TransactionDetails(QDialog):
    def __init__(self, tx, conn, parent):
        QDialog.__init__(self, parent)
        self.setModal(False)

        self.setWindowTitle("Transaktion | " + tx["entry_date"])

        tx_form = QFormLayout()
        tx_form.addRow("Konto:", QLabel(tx["local_account"], textInteractionFlags=Qt.TextInteractionFlag.TextSelectableByMouse))
        tx_form.addRow("Zweck:", QLabel(tx["purpose"], wordWrap=True, textInteractionFlags=Qt.TextInteractionFlag.TextSelectableByMouse))

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        layout = QVBoxLayout()
        layout.addLayout(tx_form)

        if tx["matching_txn"] != None:
            layout.addWidget(QPushButton("Gegenstück"))

        layout.addWidget(buttons)
        self.setLayout(layout)

    def _on_click_matching_details(self):
        matching_txn = conn.execute("select * from transactions where id = ?", (tx["matching_txn"],)).fetchone()


class TransactionTable(QTableWidget):
    def __init__(self, transactions, conn, *args):
        QTableWidget.__init__(self, *args)

        self._db = conn
        self._transactions = transactions
        self.setColumnCount(3)
        self.setRowCount(len(transactions))

        self.setHorizontalHeaderLabels(["Konto", "Zielkonto", "Zweck"])

        for n, tx in enumerate(transactions):
            self.setItem(n, 0, QTableWidgetItem(tx["local_account"].split(":")[1]))
            self.setItem(n, 1, QTableWidgetItem(build_remote_name(tx)))
            self.setItem(n, 2, QTableWidgetItem(tx["purpose"]))


        # Make columns stretch to fill all available space...
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        # ...except for the first two rows
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.resizeColumnsToContents()

        # Users should only be able to select entire rows, not individual cells
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # By default, scrolling moves by entire rows/columns. Use smooth scrolling instead
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)

        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        self.cellDoubleClicked.connect(self._cell_double_clicked)


    def _cell_double_clicked(self, row, col):
        # TODO Careful! This only works as long as the table cannot be filtered.
        tx = self._transactions[row]
        TransactionDetails(tx, self._db, self).show()


class MainWindow(QMainWindow):
    def __init__(self, conn, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setWindowTitle('Finanzen')

        transactions = conn.execute("select * from transactions").fetchall()
        self.tx_table = TransactionTable(transactions, conn, self)

        self.setCentralWidget(self.tx_table)
        self.show()


# MAIN
#===================================================================================================
if len(sys.argv) != 2:
    print("Usage: gui <TRANSACTIONS_FILE>")
    sys.exit(1)

db_file = sys.argv[1]

# Init DB
conn = sqlite3.connect(db_file)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA foreign_keys = ON")

# Init GUI
app = QApplication([])
window = MainWindow(conn)
sys.exit(app.exec())
