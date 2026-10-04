"""Scrubbable MP4 viewer for sample recordings or exported session video."""
import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage,QPixmap
from PySide6.QtWidgets import QWidget,QVBoxLayout,QLabel,QSlider,QPushButton,QFileDialog

class ReplayWidget(QWidget):
    def __init__(self,path=None):
        super().__init__();self.cap=None;self.setWindowTitle('Cinematic replay · MP4')
        layout=QVBoxLayout(self);self.image=QLabel('Open an MP4 to replay');self.image.setMinimumSize(480,300);self.image.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image);self.slider=QSlider(Qt.Horizontal);layout.addWidget(self.slider)
        button=QPushButton('Open MP4');button.clicked.connect(self.browse);layout.addWidget(button)
        self.slider.valueChanged.connect(self.show_frame)
        if path:self.open(path)
    def browse(self):
        path,_=QFileDialog.getOpenFileName(self,'Select recording','','Videos (*.mp4 *.avi *.mov)')
        if path:self.open(path)
    def open(self,path):
        if self.cap:self.cap.release()
        self.cap=cv2.VideoCapture(str(path))
        if not self.cap.isOpened():self.image.setText('Cannot decode this video');return
        self.slider.setRange(0,max(0,int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))-1));self.show_frame(0)
    def show_frame(self,index):
        if not self.cap:return
        self.cap.set(cv2.CAP_PROP_POS_FRAMES,index);ok,frame=self.cap.read()
        if not ok:return
        rgb=cv2.cvtColor(frame,cv2.COLOR_BGR2RGB);h,w=rgb.shape[:2]
        image=QImage(rgb.data,w,h,3*w,QImage.Format_RGB888).copy()
        self.image.setPixmap(QPixmap.fromImage(image).scaled(self.image.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
    def closeEvent(self,event):
        if self.cap:self.cap.release()
        super().closeEvent(event)
