"""Controlled noise-sigma sensitivity sweep on fresh seeded sessions."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QPushButton,QPlainTextEdit
from ..stress.sensitivity import sweep

class SensitivityWidget(QWidget):
    def __init__(self,scenario):
        super().__init__();self.scenario=scenario;self.setWindowTitle('What-if sensitivity');layout=QVBoxLayout(self)
        self.output=QPlainTextEdit();self.output.setReadOnly(True);layout.addWidget(self.output)
        button=QPushButton('Sweep Gaussian noise 0–20 σ');button.clicked.connect(self.run);layout.addWidget(button)
    def run(self):
        config=self.scenario.from_dict(self.scenario.to_dict());config.disturbance.noise_types=['gaussian']
        result=sweep(config,'disturbance','noise_std',[0,5,10,15,20],frames=90)
        self.output.setPlainText('\n'.join(f"σ={r['value']:<3}  pointing RMSE={r['pointing_rmse_px']}px  centroid RMSE={r['centroid_rmse_px']}px" for r in result))
