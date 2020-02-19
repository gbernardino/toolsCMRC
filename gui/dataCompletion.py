#https://build-system.fman.io/pyqt5-tutorial
#https://www.learnpyqt.com/courses/adanced-ui-features/qscrollarea/
import pandas
import argparse
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QVBoxLayout, QPlainTextEdit, QHBoxLayout,QGridLayout
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
    

import sys
from PyQt5.Qt import *
import lorem

class DisplayArea(QVBoxLayout):
    def __init__(self, *args):
        QVBoxLayout.__init__(self, *args)
        self.text = QLabel(lorem.text())
        self.scrollArea = QScrollArea(self.text)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setWidget(self.text)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.addWidget(self.scrollArea)

        
class MainWindow(QMainWindow):
    def __init__(self, *args):
        QMainWindow.__init__(self, *args)
        self.cw = QWidget(self)
        
        self.mainLayout = QGridLayout()
        self.labelPatientAndCase = QLabel('PATIENT')
        self.labelPatientAndCase.setAlignment(Qt.AlignCenter)
        self.mainLayout.addWidget(self.labelPatientAndCase, 0, 0, 1, 2)
        
        self.Display = DisplayArea()
        self.mainLayout.addLayout(self.Display,  1, 0)

        self.dataInput = QLabel( 'hello')
        self.mainLayout.addWidget(self.dataInput, 1,1)

        
        self.cw.setLayout(self.mainLayout)
        self.setCentralWidget(self.cw)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    myapp = MainWindow()
    myapp.show()
    sys.exit(app.exec_())

