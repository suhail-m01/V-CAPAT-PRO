"""Ten concise coarse-alignment lessons with a scored self-check."""
from PySide6.QtWidgets import QWidget,QVBoxLayout,QComboBox,QLabel,QPushButton

LESSONS={
 'Coarse alignment':'Keep the remote terminal in the camera field of view; fine steering is separate.',
 'Why Kalman?':'A state estimate predicts pixel position during a missed detection.',
 'PID control':'Pan and tilt speed follow angular error; integral action corrects sustained bias.',
 'Atmosphere':'Fog lowers contrast; turbulence warps the focal plane image.',
 'Point-ahead':'A travelling beam must lead a moving receiver by its motion during light time.',
 'Detection':'Threshold, connected components and subpixel centroiding turn pixels into candidates.',
 'Search':'After loss, guided scanning can recover an object still inside the reachable field.',
 'Link quality':'Even a valid pixel lock does not guarantee a calibrated communications link.',
 'Handover':'Select a newly detected beacon when the current one cannot be retained.',
 'Digital twin':'Real TLE propagation needs an ephemeris library and ground-station geometry.'}

class Tutorial(QWidget):
    def __init__(self):
        super().__init__();self.setWindowTitle('FSOC teaching mode');layout=QVBoxLayout(self)
        self.selector=QComboBox();self.selector.addItems(LESSONS);layout.addWidget(self.selector)
        self.text=QLabel();self.text.setWordWrap(True);layout.addWidget(self.text)
        self.selector.currentTextChanged.connect(lambda key:self.text.setText(LESSONS[key]));self.text.setText(next(iter(LESSONS.values())))
        self.question=QLabel('Self-check: Does a camera-frame lock prove a calibrated BER?');layout.addWidget(self.question)
        for answer in ('No · link modelling needs independent calibration','Yes · tracking always guarantees a link'):
            button=QPushButton(answer);button.clicked.connect(lambda checked=False,a=answer:self.question.setText('Correct!' if a.startswith('No') else 'Try again: pointing and BER are different.'))
            layout.addWidget(button)
