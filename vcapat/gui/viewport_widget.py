"""Viewport Widget for the desktop control room."""
from PySide6.QtCore import Qt,QTimer,QPointF,Signal
from PySide6.QtGui import QImage,QPixmap,QPainter,QPen,QColor,QFont,QIcon
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QComboBox,QGroupBox,QFileDialog,QMessageBox,QDialog,QTabWidget,QFormLayout,QSpinBox,QDoubleSpinBox,QCheckBox,QScrollArea,QFrame)

class CameraLabel(QLabel):
    selected=Signal(float,float)
    def mousePressEvent(self,event):
        image=self.pixmap()
        if image and not image.isNull():
            dx=(self.width()-image.width())/2;dy=(self.height()-image.height())/2
            x=(event.position().x()-dx)/image.width();y=(event.position().y()-dy)/image.height()
            if 0<=x<1 and 0<=y<1:self.selected.emit(x,y)
        super().mousePressEvent(event)

