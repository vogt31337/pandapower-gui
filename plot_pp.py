import sys
import random
import matplotlib
matplotlib.use("Qt5Agg")
from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenu, QVBoxLayout, QSizePolicy, QMessageBox, QWidget
from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

import pandapower as pp
import pandapower.plotting as pplot
import pandapower.networks as nw
import seaborn

colors = seaborn.color_palette()


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # We want the axes cleared every time plot() is called
        self.axes.hold(False)
        #
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                QSizePolicy.Expanding,
                QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

"""
class pandapower_plot(MyMplCanvas):
   ""draw a pandapower case""
    net = nw.mv_oberrhein()
    pp.runpp(net)
    cmap_list = [(20,'green'), (50, 'yellow'), (60, 'red')]
    cmap, norm = pplot.cmap_continous(cmap_list)
    lc = pplot.create_line_collection(net, net.line.index, zorder=1, cmap=cmap, norm=norm, linewidths=2)
    pplot.draw_collections([lc], figsize=(8, 6))
"""
class pandapower_plot(MyMplCanvas):
    net = nw.mv_oberrhein()
    lc = pplot.create_line_collection(net, net.line.index, color="grey", zorder=1)  # create lines
    bc = pplot.create_bus_collection(net, net.bus.index, size=80, color=colors[0], zorder=2)  # create buses
    pplot.draw_collections([lc, bc], figsize=(8, 6))  # plot lines and buses


class ApplicationWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowTitle("application main window")

        self.file_menu = QMenu('&File', self)
        self.file_menu.addAction('&Quit', self.fileQuit,
                QtCore.Qt.CTRL + QtCore.Qt.Key_Q)
        self.menuBar().addMenu(self.file_menu)

        self.help_menu = QMenu('&Help', self)
        self.menuBar().addSeparator()
        self.menuBar().addMenu(self.help_menu)

        self.help_menu.addAction('&About', self.about)

        self.main_widget = QWidget(self)

        l = QVBoxLayout(self.main_widget)
        sc = pandapower_plot(self.main_widget, width=5, height=4, dpi=100)

        l.addWidget(sc)

        self.main_widget.setFocus()
        self.setCentralWidget(self.main_widget)


    def fileQuit(self):
        self.close()

    def closeEvent(self, ce):
        self.fileQuit()



if __name__ == '__main__':
    app = QApplication(sys.argv)

    aw = ApplicationWindow()
    aw.setWindowTitle("PyQt5 Matplot Example")
    aw.show()
    #sys.exit(qApp.exec_())
    app.exec_()