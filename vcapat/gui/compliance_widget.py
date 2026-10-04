"""Live evidence-aware ISRO threshold check list."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel
from ..metrics.compliance import compliance

class ComplianceWidget(QWidget):
    def __init__(self):
        super().__init__();self.setWindowTitle('Specification compliance');self.layout=QVBoxLayout(self);self.label=QLabel('No evidence yet');self.layout.addWidget(self.label)
    def update_summary(self,summary):
        checks=compliance(summary);self.label.setText('\n'.join(f"{r['status']:4}  {r['label']}  ({r['value']})" for r in checks.values()))
