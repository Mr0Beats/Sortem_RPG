import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QLineEdit, QPushButton, 
                             QTabWidget, QScrollArea, QGridLayout, QLabel)
from PyQt6.QtCore import QThread, pyqtSlot, Qt

from core.game.engine import GameEngine
from cli.router import Router
from cli.commands import (LoadAllCommand, SaveAllCommand, CreateCharCommand, 
                          ListCharsCommand, ImportCharCommand, BattleCommand, StartFileManagerCommand)
from infra.gui_importer.gui_adapter import GuiDisplayAdapter
from infra.gui_importer.components import CharacterCard

class GameThread(QThread):
    def __init__(self, display_adapter, game_engine):
        super().__init__()
        self.display = display_adapter
        self.game_engine = game_engine
        self.router = Router()
        
        self.router.register("load_all", LoadAllCommand(self.game_engine, self.display)) 
        self.router.register("save_all", SaveAllCommand(self.game_engine, self.display)) 
        self.router.register("create", CreateCharCommand(self.game_engine, self.display))
        self.router.register("ls", ListCharsCommand(self.game_engine, self.display))
        self.router.register("import", ImportCharCommand(self.game_engine, self.display)) 
        self.router.register("play", BattleCommand(self.game_engine, self.display))
        self.router.register("files", StartFileManagerCommand(self.game_engine, self.display))

    def run(self):
        self.display.show("System ready. GUI Mode Initialized")
        
        while True:
            try:
                inp = self.display.prompt("> ").strip()
                if inp == "exit": break
                self.router.handle_input(inp)
            except Exception as e:
                self.display.show(f"Error: {e}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sortem RPG - GUI Version")
        self.resize(900, 700)
        self.setStyleSheet("background-color: #1e1e1e; color: white;")

        self.game_engine = GameEngine()
        self.display_adapter = GuiDisplayAdapter()
        
        self.display_adapter.text_written.connect(self.append_text)
        self.display_adapter.input_request.connect(self.enable_input)

        self.game_thread = GameThread(self.display_adapter, self.game_engine)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("QTabBar::tab { background: #333; color: white; padding: 10px; } QTabBar::tab:selected { background: #555; }")
        
        self.console_tab = self.create_console_tab()
        self.tabs.addTab(self.console_tab, "Game Console")
        
        self.catalog_tab = self.create_catalog_tab()
        self.tabs.addTab(self.catalog_tab, "Character Catalog")

        main_layout.addWidget(self.tabs)
        
        self.game_thread.start()

    def create_console_tab(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        btn_layout = QHBoxLayout()
        
        btn_load = QPushButton("Load All")
        btn_load.setStyleSheet("background-color: #007acc; padding: 5px;")
        btn_load.clicked.connect(lambda: self.send_command_auto("load_all"))
        
        btn_save = QPushButton("Save All")
        btn_save.setStyleSheet("background-color: #2ea043; padding: 5px;")
        btn_save.clicked.connect(lambda: self.send_command_auto("save_all"))

        btn_refresh = QPushButton("Refresh Catalog")
        btn_refresh.setStyleSheet("background-color: #d89e00; padding: 5px;")
        btn_refresh.clicked.connect(self.refresh_catalog)

        btn_layout.addWidget(btn_load)
        btn_layout.addWidget(btn_save)
        btn_layout.addWidget(btn_refresh)
        layout.addLayout(btn_layout)

        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        self.text_area.setStyleSheet("font-family: Consolas; font-size: 14px; background-color: #111; border: 1px solid #444;")
        layout.addWidget(self.text_area)

        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setStyleSheet("padding: 5px; font-size: 14px; background-color: #222; border: 1px solid #555;")
        self.input_field.returnPressed.connect(self.send_user_input)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.setStyleSheet("padding: 5px; background-color: #444;")
        self.send_btn.clicked.connect(self.send_user_input)
        
        input_layout.addWidget(self.input_field)
        input_layout.addWidget(self.send_btn)
        layout.addLayout(input_layout)
        
        return widget

    def create_catalog_tab(self):
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        self.catalog_content = QWidget()
        self.catalog_layout = QGridLayout(self.catalog_content)
        self.catalog_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        scroll.setWidget(self.catalog_content)
        return scroll

    def refresh_catalog(self):
        for i in reversed(range(self.catalog_layout.count())): 
            self.catalog_layout.itemAt(i).widget().setParent(None)

        chars = self.game_engine.characters
        if not chars:
            lbl = QLabel("No characters loaded.\nGo to Console and type 'import' or click 'Load All'")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.catalog_layout.addWidget(lbl, 0, 0)
            return

        row, col = 0, 0
        max_cols = 3
        
        for char in chars:
            card = CharacterCard(char)
            self.catalog_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        self.tabs.setCurrentIndex(1)

    @pyqtSlot(str)
    def append_text(self, text):
        self.text_area.append(text)
        sb = self.text_area.verticalScrollBar()
        sb.setValue(sb.maximum())

    @pyqtSlot(str)
    def enable_input(self, prompt_text):
        if prompt_text.strip():
            self.text_area.append(f"<span style='color: yellow'>{prompt_text}</span>")
        self.input_field.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.input_field.setFocus()

    def send_user_input(self):
        text = self.input_field.text()
        self.input_field.clear()
        self.input_field.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        self.text_area.append(f"<span style='color: cyan'> > {text}</span>")
        
        self.display_adapter.set_user_input(text)

    def send_command_auto(self, cmd):
        if self.input_field.isEnabled():
            self.input_field.setText(cmd)
            self.send_user_input()
            if cmd == "load_all":
                from PyQt6.QtCore import QTimer
                QTimer.singleShot(500, self.refresh_catalog)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())