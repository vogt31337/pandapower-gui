#!/usr/bin/env python
#-*- coding: utf-8 -*-
"""
Created on %(date)s

@author: %(username)s
"""

import sys

from PyQt5 import QtGui, QtCore, QtWidgets
import pandapower.networks as nw
import pandapower.plotting as plot

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, net):

        super(MainWindow, self).__init__()

        self.net = net

        self.setGeometry(300, 300, 400, 300)

        btn = QtWidgets.QPushButton("ok", self)
        btn.move(40, 40)
        btn.clicked.connect(self.plot_network)

        combo = QtWidgets.QComboBox(self)
        combo.addItem("mvOberrehein")
        combo.addItem("case9")
        combo.move(40, 0)
        combo.adjustSize()
        combo.activated[str].connect(self.network_choice)


    def plot_network(self):

        plot.simple_plot(self.net)

    def network_choice(self, text):

        if text == "mvOberrehein":
            self.net = nw.mv_oberrhein()

        elif text == "case9":
            self.net = nw.case9()






if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow(nw.mv_oberrhein())
    main_window.show()
    sys.exit(app.exec_())