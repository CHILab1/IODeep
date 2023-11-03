from PyQt5.QtWidgets import QGridLayout, QPushButton, QSlider, QApplication, QMainWindow, QLabel, QScrollArea, QMessageBox, QDialog, QVBoxLayout, QWidget, QGraphicsScene
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPen
from PyQt5.QtGui import QPixmap, QWheelEvent, QImage
from utils import Spinner, Lista, DICOMViewer
from PyQt5.QtCore import Qt, QRect, QPoint
from PyQt5 import QtCore, QtWidgets
from functools import partial
import simple_orthanc
import typing
import sys
import os

class Main(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(100,100,600,600)
        self.lista= Lista()
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.lista)
        self.lista.return_value.connect(self.handle_returned_value)
        self.lista.show()

    def handle_returned_value(self, value):
        print(f"Returned Value: {value}")
        self.lista.close()
        self.viewer= DICOMViewer(value[1])
        self.viewer.show()



if __name__ == '__main__':
    app = QApplication([])
    main_activity = Main()
    app.exec_()
