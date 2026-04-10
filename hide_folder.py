import sys
import os
import json
import hashlib
import ctypes
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QFileDialog, QListWidget,
    QListWidgetItem, QMessageBox, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont, QIcon, QColor

DATA_FILE = os.path.join(os.path.dirname(__file__), "hidden_folders.json")

def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()

def load_data() -> dict:
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

def set_folder_hidden(path: str, hide: bool):
    """Toggle Windows hidden + system attribute on a folder."""
    attrs = ctypes.windll.kernel32.GetFileAttributesW(path)
    FILE_ATTRIBUTE_HIDDEN = 0x2
    FILE_ATTRIBUTE_SYSTEM = 0x4
    if hide:
        attrs |= FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_SYSTEM
    else:
        attrs &= ~FILE_ATTRIBUTE_HIDDEN & ~FILE_ATTRIBUTE_SYSTEM
    ctypes.windll.kernel32.SetFileAttributesW(path, attrs)


STYLE = """
QMainWindow, QWidget#root {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #1a1a2e, stop:0.5 #16213e, stop:1 #0f3460);
}
QLabel#title {
    color: #e94560;
    font-size: 26px;
    font-weight: bold;
    padding: 10px 0;
}
QLabel#subtitle {
    color: #a8dadc;
    font-size: 13px;
}
QLabel {
    color: #e0e0e0;
    font-size: 13px;
}
QPushButton {
    border-radius: 8px;
    padding: 10px 18px;
    font-size: 13px;
    font-weight: bold;
    border: none;
}
QPushButton#primary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #e94560, stop:1 #c62a47);
    color: white;
}
QPushButton#primary:hover { background: #ff6b81; }
QPushButton#secondary {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #0f3460, stop:1 #533483);
    color: #a8dadc;
    border: 1px solid #533483;
}
QPushButton#secondary:hover { background: #533483; color: white; }
QPushButton#success {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #06d6a0, stop:1 #028a60);
    color: white;
}
QPushButton#success:hover { background: #06d6a0; }
QPushButton#danger {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #e94560, stop:1 #9b1d2e);
    color: white;
}
QPushButton#danger:hover { background: #ff4d6d; }
QLineEdit {
    background: rgba(255,255,255,0.07);
    border: 1px solid #533483;
    border-radius: 8px;
    padding: 10px 14px;
    color: #e0e0e0;
    font-size: 13px;
}
QLineEdit:focus { border: 1px solid #e94560; }
QListWidget {
    background: rgba(255,255,255,0.05);
    border: 1px solid #533483;
    border-radius: 10px;
    color: #e0e0e0;
    font-size: 13px;
    padding: 4px;
}
QListWidget::item {
    padding: 10px 8px;
    border-radius: 6px;
    margin: 2px 4px;
}
QListWidget::item:selected {
    background: rgba(233,69,96,0.3);
    color: #ff6b81;
}
QListWidget::item:hover { background: rgba(83,52,131,0.4); }
QFrame#card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(83,52,131,0.6);
    border-radius: 14px;
}
"""


class PinDialog(QWidget):
    """Reusable PIN/password entry card."""
    def __init__(self, title: str, on_confirm, on_cancel=None, confirm_label="Confirm"):
        super().__init__()
        self.on_confirm = on_confirm
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        lbl = QLabel(title)
        lbl.setObjectName("subtitle")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

        self.pin_input = QLineEdit()
        self.pin_input.setPlaceholderText("Enter PIN / Password")
        self.pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.pin_input.returnPressed.connect(self._confirm)
        layout.addWidget(self.pin_input)

        btn_row = QHBoxLayout()
        if on_cancel:
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setObjectName("secondary")
            cancel_btn.clicked.connect(on_cancel)
            btn_row.addWidget(cancel_btn)

        confirm_btn = QPushButton(confirm_label)
        confirm_btn.setObjectName("primary")
        confirm_btn.clicked.connect(self._confirm)
        btn_row.addWidget(confirm_btn)
        layout.addLayout(btn_row)

    def _confirm(self):
        pin = self.pin_input.text().strip()
        if not pin:
            return
        self.on_confirm(pin)
        self.pin_input.clear()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🔒 Folder Hider")
        self.setMinimumSize(620, 580)
        self.data = load_data()

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(16)

        # Title
        title = QLabel("🔒 Folder Hider")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        sub = QLabel("Hide folders with a PIN — only you can reveal them")
        sub.setObjectName("subtitle")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(sub)

        # Stacked area (list view ↔ pin dialogs)
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack, 1)

        # Page 0 — main list
        self.list_page = QWidget()
        self._build_list_page()
        self.stack.addWidget(self.list_page)

        # Page 1 — hide: pick folder then set pin
        self.hide_page = QWidget()
        self._build_hide_page()
        self.stack.addWidget(self.hide_page)

        # Page 2 — unhide: enter pin
        self.unhide_page = QWidget()
        self._build_unhide_page()
        self.stack.addWidget(self.unhide_page)

        self.stack.setCurrentIndex(0)
        self._refresh_list()

    # ── Page builders ──────────────────────────────────────────────────────

    def _build_list_page(self):
        layout = QVBoxLayout(self.list_page)
        layout.setSpacing(12)

        # Action buttons
        btn_row = QHBoxLayout()
        hide_btn = QPushButton("＋  Hide a Folder")
        hide_btn.setObjectName("primary")
        hide_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        unhide_btn = QPushButton("🔓  Unhide Selected")
        unhide_btn.setObjectName("success")
        unhide_btn.clicked.connect(self._start_unhide)

        remove_btn = QPushButton("🗑  Remove Entry")
        remove_btn.setObjectName("danger")
        remove_btn.clicked.connect(self._remove_entry)

        for b in (hide_btn, unhide_btn, remove_btn):
            btn_row.addWidget(b)
        layout.addLayout(btn_row)

        # List card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(12, 12, 12, 12)

        list_lbl = QLabel("Hidden Folders")
        list_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        list_lbl.setStyleSheet("color: #a8dadc;")
        card_layout.addWidget(list_lbl)

        self.folder_list = QListWidget()
        card_layout.addWidget(self.folder_list)
        layout.addWidget(card, 1)

    def _build_hide_page(self):
        layout = QVBoxLayout(self.hide_page)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setMaximumWidth(460)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(24, 24, 24, 24)
        c_layout.setSpacing(14)

        lbl = QLabel("Step 1 — Choose a folder to hide")
        lbl.setObjectName("subtitle")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.addWidget(lbl)

        self.folder_path_lbl = QLabel("No folder selected")
        self.folder_path_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.folder_path_lbl.setWordWrap(True)
        self.folder_path_lbl.setStyleSheet("color: #888; font-size: 12px;")
        c_layout.addWidget(self.folder_path_lbl)

        browse_btn = QPushButton("📂  Browse…")
        browse_btn.setObjectName("secondary")
        browse_btn.clicked.connect(self._browse_folder)
        c_layout.addWidget(browse_btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #533483;")
        c_layout.addWidget(sep)

        lbl2 = QLabel("Step 2 — Set a PIN / Password")
        lbl2.setObjectName("subtitle")
        lbl2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        c_layout.addWidget(lbl2)

        self.new_pin_input = QLineEdit()
        self.new_pin_input.setPlaceholderText("Enter PIN / Password")
        self.new_pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        c_layout.addWidget(self.new_pin_input)

        self.confirm_pin_input = QLineEdit()
        self.confirm_pin_input.setPlaceholderText("Confirm PIN / Password")
        self.confirm_pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_pin_input.returnPressed.connect(self._do_hide)
        c_layout.addWidget(self.confirm_pin_input)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self._back_to_list)

        hide_btn = QPushButton("🔒  Hide Folder")
        hide_btn.setObjectName("primary")
        hide_btn.clicked.connect(self._do_hide)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(hide_btn)
        c_layout.addLayout(btn_row)

        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)
        self._selected_folder = ""

    def _build_unhide_page(self):
        layout = QVBoxLayout(self.unhide_page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card = QFrame()
        card.setObjectName("card")
        card.setMaximumWidth(400)
        c_layout = QVBoxLayout(card)
        c_layout.setContentsMargins(24, 24, 24, 24)
        c_layout.setSpacing(14)

        self.unhide_path_lbl = QLabel("")
        self.unhide_path_lbl.setObjectName("subtitle")
        self.unhide_path_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.unhide_path_lbl.setWordWrap(True)
        c_layout.addWidget(self.unhide_path_lbl)

        self.unhide_pin_input = QLineEdit()
        self.unhide_pin_input.setPlaceholderText("Enter PIN / Password")
        self.unhide_pin_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.unhide_pin_input.returnPressed.connect(self._do_unhide)
        c_layout.addWidget(self.unhide_pin_input)

        btn_row = QHBoxLayout()
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary")
        cancel_btn.clicked.connect(self._back_to_list)

        confirm_btn = QPushButton("🔓  Unhide")
        confirm_btn.setObjectName("success")
        confirm_btn.clicked.connect(self._do_unhide)

        btn_row.addWidget(cancel_btn)
        btn_row.addWidget(confirm_btn)
        c_layout.addLayout(btn_row)

        layout.addWidget(card, alignment=Qt.AlignmentFlag.AlignCenter)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _refresh_list(self):
        self.folder_list.clear()
        for path, info in self.data.items():
            status = "🔴 Hidden" if info.get("hidden") else "🟢 Visible"
            item = QListWidgetItem(f"{status}   {path}")
            self.folder_list.addItem(item)

    def _back_to_list(self):
        self.new_pin_input.clear()
        self.confirm_pin_input.clear()
        self.unhide_pin_input.clear()
        self.folder_path_lbl.setText("No folder selected")
        self._selected_folder = ""
        self.stack.setCurrentIndex(0)

    def _browse_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder to Hide")
        if path:
            self._selected_folder = path
            self.folder_path_lbl.setText(path)
            self.folder_path_lbl.setStyleSheet("color: #06d6a0; font-size: 12px;")

    def _do_hide(self):
        path = self._selected_folder
        if not path:
            QMessageBox.warning(self, "No Folder", "Please select a folder first.")
            return
        pin = self.new_pin_input.text().strip()
        confirm = self.confirm_pin_input.text().strip()
        if not pin:
            QMessageBox.warning(self, "Empty PIN", "Please enter a PIN or password.")
            return
        if pin != confirm:
            QMessageBox.warning(self, "Mismatch", "PINs do not match. Try again.")
            self.confirm_pin_input.clear()
            return
        if path in self.data and self.data[path].get("hidden"):
            QMessageBox.information(self, "Already Hidden", "This folder is already hidden.")
            return

        set_folder_hidden(path, True)
        self.data[path] = {"pin": hash_pin(pin), "hidden": True}
        save_data(self.data)
        self._refresh_list()
        self._back_to_list()
        QMessageBox.information(self, "Done", f"Folder hidden successfully!\n\n{path}")

    def _start_unhide(self):
        item = self.folder_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select a folder from the list first.")
            return
        # Extract path from item text (after the status emoji + spaces)
        text = item.text()
        path = text.split("   ", 1)[1]
        if not self.data.get(path, {}).get("hidden"):
            QMessageBox.information(self, "Not Hidden", "This folder is not currently hidden.")
            return
        self._unhide_target = path
        self.unhide_path_lbl.setText(f"Unlock: {path}")
        self.unhide_pin_input.clear()
        self.stack.setCurrentIndex(2)

    def _do_unhide(self):
        pin = self.unhide_pin_input.text().strip()
        if not pin:
            return
        path = self._unhide_target
        if hash_pin(pin) != self.data[path]["pin"]:
            QMessageBox.warning(self, "Wrong PIN", "Incorrect PIN. Try again.")
            self.unhide_pin_input.clear()
            return
        set_folder_hidden(path, False)
        self.data[path]["hidden"] = False
        save_data(self.data)
        self._refresh_list()
        self._back_to_list()
        QMessageBox.information(self, "Done", f"Folder is now visible!\n\n{path}")

    def _remove_entry(self):
        item = self.folder_list.currentItem()
        if not item:
            QMessageBox.warning(self, "No Selection", "Select an entry to remove.")
            return
        text = item.text()
        path = text.split("   ", 1)[1]
        reply = QMessageBox.question(
            self, "Remove Entry",
            f"Remove this entry from the list?\n\n{path}\n\n"
            "Note: if the folder is still hidden, it will remain hidden on disk.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            del self.data[path]
            save_data(self.data)
            self._refresh_list()


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLE)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
