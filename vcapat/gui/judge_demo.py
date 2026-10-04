"""Time-boxed guided walkthrough; user retains manual scenario controls."""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QPushButton

SCRIPT=[('Coarse alignment: detect a beacon before applying fine pointing.',20),
        ('Observe three successful detections establishing lock.',30),
        ('Compare fog, noise and target motion on identical seeds.',40),
        ('Enable X-Ray and inspect the image candidates and prediction.',30),
        ('Load the bundled MP4 and compare detections with truth CSV.',40),
        ('Run the handover scenario, then inspect the evidence PDF.',40)]

class JudgeDemo(QWidget):
    def __init__(self):
        super().__init__();self.setWindowTitle('Guided judge walkthrough');self.step=0;self.remaining=0
        layout=QVBoxLayout(self);self.caption=QLabel('Click start for a paced walkthrough. Follow the prompts in the main window.')
        self.caption.setWordWrap(True);layout.addWidget(self.caption)
        button=QPushButton('Start walkthrough');button.clicked.connect(self.start);layout.addWidget(button)
        self.timer=QTimer(self);self.timer.timeout.connect(self.advance)
    def start(self):self.step=0;self.remaining=0;self.timer.start(1000);self.advance()
    def advance(self):
        if self.remaining<=0:
            if self.step>=len(SCRIPT):self.caption.setText('Walkthrough complete. Open the exported report for evidence.');self.timer.stop();return
            self.remaining=SCRIPT[self.step][1];self.step+=1
        self.remaining-=1
        self.caption.setText(f'{self.step}/{len(SCRIPT)} · {SCRIPT[self.step-1][0]}\n{self.remaining} seconds remaining')
