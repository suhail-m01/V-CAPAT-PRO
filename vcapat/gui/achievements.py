"""Evidence-derived badges; unevaluated achievements remain locked."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel

from ..metrics.achievements import earned_achievements

class Achievements(QWidget):
    def __init__(self):
        super().__init__();self.setWindowTitle('Achievements');self.layout=QVBoxLayout(self)
        self.label=QLabel('No earned badges yet. Run a session and reopen this gallery.');self.label.setWordWrap(True);self.layout.addWidget(self.label)
    def update_session(self,rows,summary):
        badges=earned_achievements(rows,summary)
        self.label.setText('\n'.join('★ '+b for b in badges) if badges else 'No earned badges yet.')
