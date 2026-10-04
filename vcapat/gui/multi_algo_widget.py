"""On-demand seeded head-to-head CV accuracy and processing comparison."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QPushButton,QPlainTextEdit
from ..stress.stress_suite import compare_detectors

class MultiAlgoWidget(QWidget):
    def __init__(self,scenario):
        super().__init__();self.scenario=scenario;self.setWindowTitle('Detection arena');layout=QVBoxLayout(self)
        self.output=QPlainTextEdit();self.output.setReadOnly(True);layout.addWidget(self.output)
        button=QPushButton('Compare four detectors (120 frames each)');button.clicked.connect(self.run);layout.addWidget(button)
    def run(self):
        result=compare_detectors(self.scenario)
        self.output.setPlainText('\n'.join(f"{i+1}. {r['detector']:<14} centroid RMSE={r['centroid_rmse_px']}px · pipeline={r['processing_fps']}fps" for i,r in enumerate(result['ranking'])))
