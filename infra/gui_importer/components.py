from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
import os

from infra.image_loader import cache_image

class CharacterCard(QFrame):
    def __init__(self, character):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFixedWidth(220)
        self.setStyleSheet("background-color: #2b2b2b; border-radius: 10px; margin: 5px; border: 1px solid #444;")
        
        layout = QVBoxLayout()
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedHeight(200)
        
        char_name = getattr(character, 'name', 'Unknown')
        char_game = getattr(character, 'game', 'custom')
        
        stats = getattr(character, 'stats', {}) or {}
        
        char_level = getattr(character, 'level', None)
        if char_level is None:
            char_level = stats.get('level', 1)

        SUPPORTED_GAMES = ['genshin', 'genshin impact', 'starrail', 'honkai']
        
        image_path = ""
        is_supported = str(char_game).lower() in SUPPORTED_GAMES
        
        if is_supported:
            image_path = cache_image("", char_name)
        
        pixmap_loaded = False
        if image_path and os.path.exists(image_path) and os.path.getsize(image_path) > 0:
            pixmap = QPixmap(image_path)
            if not pixmap.isNull():
                self.image_label.setPixmap(pixmap.scaled(
                    190, 190, 
                    Qt.AspectRatioMode.KeepAspectRatio, 
                    Qt.TransformationMode.SmoothTransformation
                ))
                pixmap_loaded = True

        if not pixmap_loaded:
            self.image_label.setText(f"[No Image]\n{char_name}")
            style = "color: #90ee90; border: 1px dashed #2ea043; padding: 10px;"
            if is_supported:
                style = "color: #777; border: 1px dashed #555; padding: 10px;"
            
            self.image_label.setStyleSheet(style)
            self.image_label.setWordWrap(True)

        layout.addWidget(self.image_label)

        name_label = QLabel(f"{char_name}")
        name_label.setStyleSheet("font-weight: bold; font-size: 18px; color: #ffcc00; border: none;")
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setWordWrap(True)
        layout.addWidget(name_label)

        game_display = str(char_game).upper() if char_game else "CUSTOM"
        lvl_text = f"Lvl: {char_level} | {game_display}"
        lvl_label = QLabel(lvl_text)
        lvl_label.setStyleSheet("color: #aaaaaa; font-size: 12px; border: none;")
        lvl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lvl_label)

        stats_layout = QHBoxLayout()

        hp = getattr(character, 'max_hp', 0) or getattr(character, 'base_hp', 0)
        if hp == 0: hp = getattr(character, 'hp', 0)
        
        atk = getattr(character, 'attack', 0) or getattr(character, 'base_attack', 0)
        if atk == 0: atk = getattr(character, 'base_attack', 0)

        if hp == 0:
            hp = stats.get('max_hp', stats.get('hp', stats.get('base_hp', stats.get('health', 0))))
            
        if atk == 0:
            atk = stats.get('attack', stats.get('base_attack', 0))

        hp_lbl = QLabel(f"❤️ {hp}")
        hp_lbl.setStyleSheet("color: #ff5555; font-weight: bold; border: none;")
        atk_lbl = QLabel(f"⚔️ {atk}")
        atk_lbl.setStyleSheet("color: #55ffff; font-weight: bold; border: none;")
        
        stats_layout.addWidget(hp_lbl)
        stats_layout.addStretch()
        stats_layout.addWidget(atk_lbl)
        
        layout.addLayout(stats_layout)
        self.setLayout(layout)