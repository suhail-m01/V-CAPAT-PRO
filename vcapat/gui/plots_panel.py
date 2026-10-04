"""Plots Panel for the desktop control room."""
from PySide6.QtCore import Qt,QTimer,QPointF,Signal
from PySide6.QtGui import QImage,QPixmap,QPainter,QPen,QColor,QFont,QIcon
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QComboBox,QGroupBox,QFileDialog,QMessageBox,QDialog,QTabWidget,QFormLayout,QSpinBox,QDoubleSpinBox,QCheckBox,QScrollArea,QFrame)

class Plot(QWidget):
    def __init__(self,engine):super().__init__();self.engine=engine;self.setMinimumHeight(155)
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.Antialiasing);w=self.width();h=self.height()
        p.fillRect(self.rect(),QColor('#0c1926'));p.setPen(QPen(QColor('#243b4b')))
        for i in range(1,5):p.drawLine(35,int(h*i/5),w-12,int(h*i/5))
        history=self.engine.history[-180:];values=[x['error'] for x in history];valid=[v for v in values if v is not None]
        p.setPen(QColor('#8099a9'));p.drawText(12,17,'POINTING ERROR  /  PX')
        if len(valid)<2:return
        ceiling=max(10,max(valid)*1.1);p.setPen(QPen(QColor('#6ee4be'),2))
        old=None
        for i,value in enumerate(values):
            if value is None:old=None;continue
            point=QPointF(35+i*(w-50)/max(1,len(values)-1),h-17-value/ceiling*(h-45))
            if old:p.drawLine(old,point)
            old=point
        p.setPen(QColor('#8099a9'));p.drawText(w-70,17,f'{valid[-1]:.1f} PX')

