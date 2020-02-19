#https://build-system.fman.io/pyqt5-tutorial
import pandas
import argparse
from PyQt5 import QApp
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, , QHBoxLayout
def downloadFromSQL():
    pass
class Data:
    def __init__(self, path = None):
        # load patients
        # load cases
        # load procedures

        # load automatic selected data
        # load manually selected data
        
        # load proc IDs
        # load diagnosis IDs
        pass
    def saveRegisterAsTemp(self):
        pass
    
    def saveAsCSV(self):
        pass
    def addManualInformation(self):
        pass
    def getIncompletePatients(self):
        pass
    


This is the prior answer from Alvaro Fuentes, with the minor updates necessary for PyQt5.

import sys
from PyQt5.Qt import *

class MyPopup(QWidget):
    def __init__(self, mainwin):
        QWidget.__init__(self)

        # I want to change the lable1 of MainWindow
        mainwin.label1.setText('hello')


class MainWindow(QMainWindow):
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
        self.cw = QWidget(self)
        self.setCentralWidget(self.cw)
        
        self.
        
        self.btn1 = QPushButton("Click me", self.cw)
        self.btn1.setGeometry(QRect(50, 50, 100, 30))
        self.label1 = QLabel("No Commands running", self.cw)
        self.btn1.clicked.connect(self.doit)
        self.w = None


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = MainWindow()
    myapp.show()
    sys.exit(app.exec_())

