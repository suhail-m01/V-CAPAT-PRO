"""Centralized dark mission-control Qt stylesheet."""
STYLE='''
QWidget{background:#091521;color:#e6f0f5;font-family:Segoe UI,Arial;font-size:12px}QMainWindow{background:#08131e}
QMenuBar,QMenu{background:#102131;color:#e3eef5}QMenu::item:selected{background:#1c433a;color:#6ee4be}QGroupBox{background:#101f2d;border:1px solid #263b4c;border-radius:12px;margin-top:12px;padding:14px 12px 10px;font-weight:bold;color:#bfcfdc;letter-spacing:1px}
QGroupBox::title{subcontrol-origin:margin;left:14px;top:0;padding:0 5px;background:#091521;color:#8eafba}
QGroupBox QLabel{background:transparent}QPushButton{background:#172a39;border:1px solid #315064;border-radius:8px;padding:9px 13px;font-weight:bold;color:#d9e9ee}
QPushButton:hover{border:1px solid #70e2bf;background:#204039}QPushButton:pressed{background:#2a5a4b}
QPushButton#primary{background:#6ee4be;color:#06231e;border-color:#6ee4be}
QComboBox,QSpinBox,QDoubleSpinBox{background:#0b1a28;border:1px solid #365061;border-radius:7px;padding:7px;color:#e4f1f7;min-width:80px}
QComboBox QAbstractItemView{background:#142536;color:white;selection-background-color:#296052}
QLabel#heading{font-size:25px;font-weight:800;color:white}QLabel#eyebrow{font-size:10px;font-weight:bold;color:#6ee4be;letter-spacing:2px}
QLabel#muted{color:#8ca2b3}QLabel#large{font-size:22px;font-weight:bold;color:#6ee4be}QTabWidget::pane{border:1px solid #30485a;border-radius:8px}QTabBar::tab{padding:8px 16px;background:#142635;color:#91a8b9}QTabBar::tab:selected{color:#70e2bf;background:#1c3938}
'''

