"""Explainable candidate-score table for the OpenCV detector."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPlainTextEdit

class XRayOverlay(QWidget):
    def __init__(self):
        super().__init__();layout=QVBoxLayout(self);layout.addWidget(QLabel('CANDIDATE SCORE CONTRIBUTIONS'))
        self.text=QPlainTextEdit();self.text.setReadOnly(True);layout.addWidget(self.text)
    def show_candidates(self,candidates):
        lines=[]
        for i,c in enumerate(candidates[:10],1):
            terms=c.get('contributions',{})
            lines.append(f"#{i} ({c['x']:.1f}, {c['y']:.1f}) · score {c['score']:.2f} · area {c['area']} · brightness {c['brightness']}\n    "+', '.join(f'{k}={v:.2f}' for k,v in terms.items()))
        self.text.setPlainText('\n'.join(lines) if lines else 'No image-space candidates this frame.')
