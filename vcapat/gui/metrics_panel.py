"""Reusable source-independent telemetry table for detached monitor windows."""
from PySide6.QtWidgets import QGroupBox,QGridLayout,QLabel

class MetricsPanel(QGroupBox):
    def __init__(self):
        super().__init__('FLIGHT TELEMETRY');self.labels={};grid=QGridLayout(self)
        for i,(key,title) in enumerate([('fps','Pipeline FPS'),('processing_ms','Processing ms'),('pointing_error','Pointing px'),('centroid_error','Centroid px'),('lock_retention','Retention %')]):
            grid.addWidget(QLabel(title),i,0);label=QLabel('—');grid.addWidget(label,i,1);self.labels[key]=label
    def update_metrics(self,snapshot):
        for key,label in self.labels.items():
            value=snapshot.get(key);label.setText('—' if value is None else f'{value:.2f}')
