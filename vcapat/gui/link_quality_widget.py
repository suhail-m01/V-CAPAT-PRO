"""Live illustrative pointing-loss bar with explicit non-calibration warning."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QProgressBar

class LinkQualityWidget(QWidget):
    def __init__(self):
        super().__init__();self.setWindowTitle('Optical link proxy');layout=QVBoxLayout(self)
        self.bar=QProgressBar();self.bar.setRange(0,100);layout.addWidget(self.bar)
        self.note=QLabel('Illustrative pointing-loss proxy · not measured BER or SNR');layout.addWidget(self.note)
    def update_quality(self,percentage):self.bar.setValue(int(percentage))
