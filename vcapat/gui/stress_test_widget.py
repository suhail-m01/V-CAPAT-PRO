"""Non-blocking 20-case matrix runner with explicit PASS/N/A counts."""
from PySide6.QtCore import QThread,Signal
from PySide6.QtWidgets import QWidget,QVBoxLayout,QPushButton,QPlainTextEdit
from ..stress.stress_suite import stress_suite

class StressWorker(QThread):
    completed=Signal(object)
    def __init__(self,scenario):super().__init__();self.scenario=scenario
    def run(self):self.completed.emit(stress_suite(self.scenario))

class StressTestWidget(QWidget):
    def __init__(self,scenario):
        super().__init__();self.scenario=scenario;self.setWindowTitle('Stress-test suite');layout=QVBoxLayout(self)
        self.output=QPlainTextEdit();self.output.setReadOnly(True);layout.addWidget(self.output)
        self.button=QPushButton('Run 20 reproducible scenarios');self.button.clicked.connect(self.start);layout.addWidget(self.button);self.worker=None
    def start(self):
        self.button.setEnabled(False);self.output.setPlainText('Running twenty isolated cases…')
        self.worker=StressWorker(self.scenario);self.worker.completed.connect(self.show_result);self.worker.start()
    def show_result(self,result):
        self.output.setPlainText('\n'.join(f"{c['name']:<24}  {c['passed_checks']} pass / {c['failed_checks']} fail" for c in result['cases']))
        self.button.setEnabled(True)
