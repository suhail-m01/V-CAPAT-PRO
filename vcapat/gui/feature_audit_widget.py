"""Visible honest 55-feature coverage for the desktop application."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPlainTextEdit
from ..core.feature_registry import FEATURES

class FeatureAudit(QWidget):
    def __init__(self):
        super().__init__();self.setWindowTitle('55-feature audit · limits and integration points');self.resize(850,650)
        layout=QVBoxLayout(self)
        intro=QLabel('RUNNABLE = bounded software function · PARTIAL = meaningful subset · INTEGRATION = needs external assets or qualification. No ISRO certification implied.')
        intro.setWordWrap(True);layout.addWidget(intro)
        text=QPlainTextEdit();text.setReadOnly(True)
        text.setPlainText('\n\n'.join(f'{i:02d}  {name}  [{status}]\n{scope}\nSource: {source}' for i,name,status,scope,source in FEATURES))
        layout.addWidget(text)
