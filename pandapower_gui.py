"""-*- coding: utf-8 -*-.

Copyright (c) Tobie Nortje, Leon Thurner, Jonas Haack
All rights reserved. Use of this source code is governed
by a BSD-style license that can be found in the LICENSE file.
File created by Tobie Nortje ---
"""

# general
import sys
import time

from functools import partial
import pandas as pd

# pandapower
import pandapower as pp
import pandapower.networks as pnw
# import pandapower.plotting as pplot
import pandapower.shortcircuit as sc


# pandapower gui
from element_windows import BusWindow
from element_windows import ExtGridWindow
from element_windows import GenWindow
from element_windows import LineWindow
from element_windows import LoadWindow
from element_windows import TrafoWindow

try:
    import pplog as logging
except ImportError:
    import logging

logger = logging.getLogger(__name__)

#qt
try:
    """
    for the pyqt version setup:
    pyqt                      5.6.0            py36hb5ed885_5
    """
    from PyQt5 import uic

    from PyQt5.QtCore import pyqtSlot
    from PyQt5.QtCore import Qt
    from PyQt5.QtCore import QTimer
    from PyQt5.QtCore import QUrl

    from PyQt5.QtGui import QIcon
    from PyQt5.QtGui import QPixmap

    from PyQt5.QtWebKitWidgets import QWebView

    # from PyQt5 import QtWidgets
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtWidgets import QDialog
    from PyQt5.QtWidgets import QFileDialog
    from PyQt5.QtWidgets import QMainWindow
    from PyQt5.QtWidgets import QMessageBox
    from PyQt5.QtWidgets import QSizePolicy
    from PyQt5.QtWidgets import QSplashScreen
    from PyQt5.QtWidgets import QTableWidgetItem
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.QtWidgets import QWidget

    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    QT_VERSION = "5"
    logger.info("PyQt {} loaded".format(QT_VERSION))
except ImportError:
    """
    for the pyqt version setup:
    pyqt                      5.6.0            py35hd46907b_5
    PyQt5                     5.10.1                    <pip>
    """
    from PyQt5 import uic

    from PyQt5.QtCore import pyqtSlot
    from PyQt5.QtCore import Qt
    from PyQt5.QtCore import QTimer
    from PyQt5.QtCore import QUrl

    from PyQt5.QtGui import QIcon
    from PyQt5.QtGui import QPixmap

    from PyQt5.QtWebEngineWidgets import QWebEngineView as QWebView

    # from PyQt5 import QtWidgets
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtWidgets import QDialog
    from PyQt5.QtWidgets import QFileDialog
    from PyQt5.QtWidgets import QMainWindow
    from PyQt5.QtWidgets import QMessageBox
    from PyQt5.QtWidgets import QSizePolicy
    from PyQt5.QtWidgets import QSplashScreen
    from PyQt5.QtWidgets import QTableWidgetItem
    from PyQt5.QtWidgets import QVBoxLayout
    from PyQt5.QtWidgets import QWidget

    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
    QT_VERSION = "5"
    logger.info("PyQt {} loaded".format(QT_VERSION))

import matplotlib.pyplot as plt

import pandapower.plotting as plot

from qtconsole.rich_jupyter_widget import RichJupyterWidget
from qtconsole.inprocess import QtInProcessKernelManager

from IPython.lib import guisupport

_GUI_VERSION = "dev 0"


class QIPythonWidget(RichJupyterWidget):
    """Convenience class for a live IPython console widget.

    We can replace the standard banner using the customBanner argument

    TODO(QIPythonWidget): stream all pandapower events to the console
    """

    def __init__(self, customBanner=None, *args, **kwargs):
        if customBanner:
            self.banner = customBanner
        super(QIPythonWidget, self).__init__(*args, **kwargs)
        self.kernel_manager = kernel_manager = QtInProcessKernelManager()
        kernel_manager.start_kernel()
        kernel_manager.kernel.gui = 'qt4'
        self.kernel_client = kernel_client = self._kernel_manager.client()
        kernel_client.start_channels()

        def stop():
            """Stop."""
            kernel_client.stop_channels()
            kernel_manager.shutdown_kernel()
            guisupport.get_app_qt4().exit()
        self.exit_requested.connect(stop)

    def pushVariables(self, variableDict):
        """Push Variables to the console widget.

        Given a dictionary containing name / value pairs, push those variables to the IPython
        console widget
        """
        self.kernel_manager.kernel.shell.push(variableDict)

    def clearTerminal(self):
        """Clear the terminal."""
        self._control.clear()

    def printText(self, text):
        """Print some plain text to the console."""
        self._append_plain_text(text)

    def executeCommand(self, command):
        """Execute a command in the frame of the console widget."""
        self._execute(command, False)


class MplCanvas(FigureCanvas):
    """Matplotlib canvas class to create figures."""

    def __init__(self):
        """Initialize."""
        self.fig = plt.Figure()
        self.ax = self.fig.add_subplot(111)
        FigureCanvas.__init__(self, self.fig)
        FigureCanvas.setSizePolicy(
            self, QSizePolicy.Expanding, QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class MplWidget(QWidget):
    """Matplotlib widget."""

    def __init__(self, parent=None):
        """Initialize."""
        QWidget.__init__(self, parent)   # Inherit from QWidget
        self.canvas = MplCanvas()        # Create canvas object
        self.vbl = QVBoxLayout()         # Set box for plotting

    def update_canvas(self):
        """Update the Figure (including the colorbar)."""
        pass

    def add_toolbar(self, mpl_toolbar):
        """Add a toolbar below the plot."""
        self.vbl.addWidget(self.canvas)
        self.vbl.addWidget(mpl_toolbar)
        self.setLayout(self.vbl)


class mainWindow(QMainWindow):
    """Create main window."""

    def __init__(self):
        super(mainWindow, self).__init__()
        uic.loadUi('resources/ui/main_develop.ui', self)

        self.mainPrintMessage("Welcome to pandapower version: " +
                              pp.__version__ +
                              "\nQt vesrion: " +
                              QT_VERSION +
                              "\nGUI version: " +
                              _GUI_VERSION + "\n" +
                              "\nNetwork variable stored in : net")

        self.embedIpythonInterpreter()  # embed the ipython

        # collections builder setup
        self.lastBusSelected = None
        self.embedCollectionsBuilder()  # plot the network in widget_1
        self.embedResultCollectionsBuilder()  # plot the network in widget_2

        self.load_network(net=createSampleNetwork(), name="GUI Example Network")
        # self.load_network(net=pnw.mv_oberrhein(), name="Junkernetz")

        self.initialiseCollectionsPlot()
        self.network_graph.canvas.ax.xaxis.set_visible(False)
        self.network_graph.canvas.ax.yaxis.set_visible(False)
        self.network_graph.canvas.ax.set_aspect('equal', 'datalim')
        self.network_graph.canvas.ax.autoscale_view(True, True, True)

        self.result_plot.canvas.ax.xaxis.set_visible(False)
        self.result_plot.canvas.ax.yaxis.set_visible(False)
        self.result_plot.canvas.ax.set_aspect('equal', 'datalim')
        self.result_plot.canvas.ax.autoscale_view(True, True, True)

        self.pushButton.clicked.connect(self.on_click_standard_plot)
        self.pushButton_2.clicked.connect(self.on_click_line_loading_plot)
        self.pushButton_3.clicked.connect(self.on_click_bus_voltage_plot)
        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)

        self.collectionsDoubleClick = False

        self.tabWidget.setCurrentIndex(0)  # set firtst tab

        # menubar
        # self.actionNew_Network.triggered.connect(self.mainEmptyClicked)
        self.actionNew_Network.triggered.connect(self.clearMainCollectionBuilder)
        self.actionLoad.triggered.connect(self.mainLoadClicked)
        self.actionSave.triggered.connect(self.mainSaveClicked)
        self.actionQuit.triggered.connect(self.mainQuitClicked)
        self.actionCigre_lv.triggered.connect(self.mainExampleClicked)
        self.actionCigre_mv.triggered.connect(self.mainExampleClicked)
        self.actionCigre_hv.triggered.connect(self.mainExampleClicked)

        self.actionAbout.triggered.connect(self.show_license)
        self.actionDocumentation.triggered.connect(self.show_docs)

        # toolbar
        self.actionrunpp.triggered.connect(self.runpp)
        self.actionrunpp.triggered.connect(self.lossesSummary)
        self.actionrunpp.setIcon(QIcon('resources/icons/runpp.png'))

        self.actionrunppOptions.triggered.connect(self.runpp_options)
        self.actionrunppOptions.setIcon(QIcon('resources/icons/runpp_options.png'))

        # run shortcircuit
        # self.actionSC.triggered.connect(self.runsc)
        self.actionSC.setIcon(QIcon('resources/icons/shortcircuit.png'))
        self.actionSC.triggered.connect(self.runsc_options)

        # show initialised and updated element tables
        self.tabWidget_inspect.setCurrentIndex(0)
        self.show_element_table()
        self.set_table_tabs_inactive()
        self.tabWidget.currentChanged.connect(self.show_element_table)
        self.tabWidget.currentChanged.connect(self.set_table_tabs_inactive)
        self.tabWidget_inspect.currentChanged.connect(self.show_element_table)
        # self.tabWidget_inspect.currentChanged.connect(self.set_table_tabs_inactive)

        # show initialised and updated results tables
        self.tabWidget_result.setCurrentIndex(0)
        self.show_result_table()
        self.tabWidget_result.currentChanged.connect(self.show_result_table)
        # self.tabWidget_result.currentChanged.connect(self.set_table_tabs_inactive)

        # interpreter
        self.runTests.clicked.connect(self.runPandapowerTests)

        self.show()

    def show_license(self):
        license_text = open("LICENSE", "r")
        self.license = QMessageBox()
        self.license.setIcon(QMessageBox.Information)
        self.license.setWindowTitle("pandapower GUI")
        self.license.setText(license_text.read())
        self.license.show()

    def show_docs(self):
        self.docs = QWebView()
        self.docs.load(QUrl("https://pandapower.readthedocs.io"))
        self.docs.setWindowTitle("pandapower Documentation")
        self.docs.show()

    def printLineSeperator(self, ch="=", n=40):
        """Print some characters."""
        return ch*n+"\n"

    def mainPrintMessage(self, message):
        # self.main_message.append(self.printLineSeperator())
        self.main_message.append(message)
        self.main_message.append(self.printLineSeperator())

    def embedIpythonInterpreter(self):
        """Embed an IPyton QT Console Interpreter."""
        self.ipyConsole = QIPythonWidget(
            customBanner="""Welcome to the console\nType \
                            whos to get list of variables \
                            \n =========== \n""")

        self.interpreter_vbox.addWidget(self.ipyConsole)
        self.ipyConsole.pushVariables({"pp": pp, "sc": sc})

    def mainLoadClicked(self):
        filename = QFileDialog.getOpenFileName(filter="*.json")  # "*.xlsx, *.p, *.json"
        if filename[0]:
            if filename[1]=="*.json":
                net = pp.from_json(filename[0])
            elif filename[1]=="*.xlsx":
                net = pp.from_excel(filename[0])
            elif filename[1]=="*.p":
                net = pp.from_pickle(filename[0])
            else:
                net = pnw.create_empty_network()
                logger.warning("Empty net created")

        try:
            self.load_network(net=net, name=filename[0].split('/')[-1])
        except Exception:
            logger.warning("No file loaded")

    def load_network(self, net, name):
        """Load a network."""
        self.net = net
        if "_runpp_options" not in self.net:
            self.net._runpp_options = dict()
        # self.ipyConsole.executeCommand("del(net)")
        # self.ipyConsole.clearTerminal()
        if "_runsc_options" not in self.net:
            self.net._runsc_options = dict()
        self.ipyConsole.printText("\n\n"+"-"*40)
        self.ipyConsole.printText("\nNew net loaded \n")
        self.ipyConsole.printText("-"*40+"\n\n")
        self.ipyConsole.pushVariables({"net": self.net})
        self.ipyConsole.executeCommand("net")
        self.initialiseCollectionsPlot()
        self.clearResultCollectionsPlot()
        self.mainPrintMessage(name + " loaded")
        self.mainPrintMessage(str(self.net))
        self.result_table.clear()
        self.element_table.clear()

    def mainSaveClicked(self):
        # filename = QFileDialog.getOpenFileName()
        filename = QFileDialog.getSaveFileName(self, 'Save net')
        logger.info("{}".format(filename[0]))
        try:
            pp.to_excel(self.net, filename[0])
            self.mainPrintMessage("Saved case to: " + filename[0])
        except:
            self.mainPrintMessage("Case not saved, maybe empty?")

    def mainQuitClicked(self):
        reply = QMessageBox.question(
            self, "Message",
            "Are you sure you want to quit? Any unsaved work will be lost.",
            QMessageBox.Save | QMessageBox.Close | QMessageBox.Cancel,
            QMessageBox.Save)

        if reply == QMessageBox.Close:
            app.quit()
        elif reply == QMessageBox.Save:
            self.mainSaveClicked()
        else:
            pass

    def mainExampleClicked(self):
        if self.actionCigre_lv.triggered:
            self.load_network(net=pnw.create_cigre_network_lv(), name="Cigre LV Network")
            logger.info("Cigre LV")
            self.actionCigre_lv.triggered = False
        elif self.actionCigre_mv.triggered:
            self.load_network(net=pnw.create_cigre_network_mv(with_der="all"), name="Cigre MV Network")
            logger.info("Cigre MV")
            self.actionCigre_mv.triggered = False
        elif self.actionCigre_hv.triggered:
            self.load_network(net=pnw.create_cigre_network_hv(length_km_6a_6b=0.1), name="Cigre HV Network")
            logger.info("Cigre HV")
            self.actionCigre_hv.triggered = False

    def runpp(self):
        """Run pandapapower loadflow and trigger results output plot."""
        try:
            pp.runpp(self.net, **self.net._runpp_options)
            self.mainPrintMessage(str(self.net))
            self.initialiseResultCollectionsPlot()
            self.pushButton.setEnabled(True)
            self.pushButton_2.setEnabled(True)
            self.pushButton_3.setEnabled(True)
        except pp.LoadflowNotConverged:
            self.mainPrintMessage("Power Flow did not Converge!")
        except:
            self.mainPrintMessage("Error occured - empty network?")

    def runpp_options(self):
        try:
            runppOptions(self.net, parent=self)
            # self.options.show()
        except Exception as e:
            logger.warning("{}".format(e))

    def runsc_options(self):
        try:
            runscOptions(self.net, parent=self)
            #            self.options.show()
        except Exception as e:
            logger.warning("{}".format(e))

    def lossesSummary(self):
        """Print the losses in each element that has losses."""
        # get total losses
        self.mainPrintMessage("Losses report generated:")
        losses = 0.0
        for i in self.net:
            if 'res' in i:
                if 'pl_kw' in self.net[i]:
                    if not self.net[i]['pl_kw'].empty:
                        # logger.info("{}".format(i))
                        # self.main_message.append(i)
                        self.main_message.append(i)
                        self.main_message.append(
                            self.net[i]['pl_kw'].to_string())
                        # logger.warning("{}".format(self.net[i]['pl_kw']))
                        losses += self.net[i]['pl_kw'].sum()
        self.main_message.append("Total Losses (kW)")
        self.main_message.append(str(losses))

        # get total load
        total_load_kw = self.net.res_gen.sum() + self.net.res_sgen.sum() + \
            self.net.res_ext_grid.sum()
        self.main_message.append("Total nett load flowing in network")
        self.main_message.append(str(total_load_kw['p_kw']))

        # losses percentage
        self.main_message.append("% losses")
        loss_pct = losses / total_load_kw['p_kw']
        self.main_message.append(str(abs(loss_pct * 100)))

    def runsc(self):
        try:
            sc.calc_sc(self.net, **self.net._runsc_options)
            # self.mainPrintMessage(str(self.net))
        except pp.LoadflowNotConverged:
            self.mainPrintMessage("Power Flow did not Converge!")
        except:
            self.mainPrintMessage("Error occured - empty network?")
        self.tabWidget_result_sc.setCurrentIndex(0)
        self.show_result_sc_table()
        self.tabWidget_result_sc.currentChanged.connect(self.show_result_sc_table)

    def get_element_index(self):
        index = self.tabWidget_inspect.currentIndex()
        tab_list = {0: 'bus', 1: 'line', 2: 'switch', 3: 'load', 4: 'sgen', 5: 'ext_grid',
                    6: 'trafo', 7: 'trafo3w', 8: 'gen', 9: 'shunt', 10: 'impedance', 11: 'ward',
                    12: 'xward', 13: 'dcline', 14: 'measurement'}
        element = tab_list[index]
        return element

    def get_result_index(self):
        index = self.tabWidget_result.currentIndex()
        tab_list = {0: 'res_bus', 1: 'res_line', 2: 'res_load', 3: 'res_sgen', 4: 'res_ext_grid',
                    5: 'res_trafo', 6: 'res_trafo3w', 7: 'res_gen', 8: 'res_shunt', 9: 'res_ward',
                    10: 'res_xward', 11: 'res_dcline'}
        element = tab_list[index]
        return element

    def get_result_sc_index(self):
        index = self.tabWidget_result_sc.currentIndex()
        tab_list = {0: 'res_bus_sc', 1: 'res_line_sc', 2: 'res_load_sc', 3: 'res_sgen_sc',
                    4: 'res_ext_grid_sc', 5: 'res_trafo_sc', 6: 'res_trafo3w_sc', 7: 'res_gen_sc',
                    8: 'res_shunt_sc', 9: 'res_ward_sc', 10: 'res_xward_sc', 11: 'res_dcline_sc'}
        # tab_list = {0: 'res_bus', 1: 'res_line', 2: 'res_load', 3: 'res_sgen', 4: 'res_ext_grid',
        #           5: 'res_trafo', 6: 'res_trafo3w', 7: 'res_gen', 8: 'res_shunt', 9: 'res_ward',
        #            10: 'res_xward', 11: 'res_dcline'}
        element = tab_list[index]
        return element

    def show_element_table(self):
        element = self.get_element_index()
        self.show_table(element, self.element_table)

    def show_result_table(self):
        element = self.get_result_index()
        self.show_table(element, self.result_table)

    def show_result_sc_table(self):
        element = self.get_result_sc_index()
#        element = self.get_result_index()
        self.show_table(element, self.result_sc_table)

    def show_table(self, element, table_widget):
        table = self.net[element]
        table_widget.setColumnCount(len(table.columns) + 1)
        table_widget.setRowCount(len(table))
        header = ["index"] + table.columns.tolist()
        table_widget.setHorizontalHeaderLabels(header)
        for i, (idx, row) in enumerate(table.iterrows()):
            table_widget.setItem(i, 0, QTableWidgetItem(str(idx)))
            for k, value in enumerate(row.values, 1):
                logger.debug("{}: {}, {}, {}".format(element, i, k, value))
                table_widget.setItem(i, k, QTableWidgetItem(str(value)))
        table_widget.doubleClicked.connect(partial(self.table_doubleclicked, element, table_widget))

    def set_table_tabs_inactive(self):
        """Set the tabs for selecting the tables inactive for all elements that are empty in net."""
        par = []
        res = []
        res_sc = []
        for tb in list(self.net.keys()):
            if isinstance(self.net[tb], pd.DataFrame) and len(self.net[tb]) > 0:
                if 'res_' in tb:
                    if "_sc" in tb:
                        res_sc.append(tb)
                    else:
                        res.append(tb)
                else:
                    par.append(tb)

        tab_list = {
            'bus': 0, 'dcline': 13, 'ext_grid': 5, 'gen': 8, 'impedance': 10, 'line': 1, 'load': 3,
            'measurement': 14, 'sgen': 4, 'shunt': 9, 'switch': 2, 'trafo': 6, 'trafo3w': 7,
            'ward': 11, 'xward': 12}
        for element in tab_list.keys():
            if element in par:
                self.tabWidget_inspect.setTabEnabled(tab_list[element], True)
            else:
                self.tabWidget_inspect.setTabEnabled(tab_list[element], False)
        res_tab_list = {
            'res_bus': 0, 'res_dcline': 11, 'res_ext_grid': 4, 'res_gen': 7, 'res_line': 1,
            'res_load': 2, 'res_sgen': 3, 'res_shunt': 8, 'res_trafo': 5, 'res_trafo3w': 6,
            'res_ward': 9, 'res_xward': 10}
        for result in res_tab_list.keys():
            if result in res:
                self.tabWidget_result.setTabEnabled(res_tab_list[result], True)
            else:
                self.tabWidget_result.setTabEnabled(res_tab_list[result], False)
        res_tab_sc_list = {
            'res_bus_sc': 0, 'res_dcline_sc': 11, 'res_ext_grid_sc': 4, 'res_gen_sc': 7,
            'res_line_sc': 1, 'res_load_sc': 2, 'res_sgen_sc': 3, 'res_shunt_sc': 8,
            'res_trafo_sc': 5, 'res_trafo3w_sc': 6, 'res_ward_sc': 9, 'res_xward_sc': 10}
        for result_sc in res_tab_sc_list.keys():
            if result_sc in res_sc:
                self.tabWidget_result_sc.setTabEnabled(res_tab_sc_list[result_sc], True)
            else:
                self.tabWidget_result_sc.setTabEnabled(res_tab_sc_list[result_sc], False)


    def table_doubleclicked(self, element, table_widget, cell):
        try:
            index = int(table_widget.item(cell.row(), 0).text())
            self.open_element_window(element, index)
        except Exception as e:
            logger.info("{}".format(e))

    # res
    def res_bus_clicked(self):
        self.res_message.setHtml(str(self.net.res_bus.to_html()))

    def res_lines_clicked(self):
        self.res_message.setHtml(str(self.net.res_line.to_html()))

    # def res_switch_clicked(self):
    #    self.res_message.setHtml(str(self.net.res_switch.to_html()))

    def res_load_clicked(self):
        self.res_message.setHtml(str(self.net.res_load.to_html()))

    def res_sgen_clicked(self):
        self.res_message.setHtml(str(self.net.res_sgen.to_html()))

    def res_ext_grid_clicked(self):
        self.res_message.setHtml(str(self.net.res_ext_grid.to_html()))

    def res_trafo_clicked(self):
        self.res_message.setHtml(str(self.net.res_trafo.to_html()))

    def res_trafo3w_clicked(self):
        self.res_message.setHtml(str(self.net.res_trafo3w.to_html()))

    def res_gen_clicked(self):
        self.res_message.setHtml(str(self.net.res_gen.to_html()))

    def res_shunt_clicked(self):
        self.res_message.setHtml(str(self.net.res_shunt.to_html()))

    def res_ward_clicked(self):
        self.res_message.setHtml(str(self.net.res_ward.to_html()))

    def res_xward_clicked(self):
        self.res_message.setHtml(str(self.net.res_xward.to_html()))

    def res_dcline_clicked(self):
        self.res_message.setHtml(str(self.net.res_dcline.to_html()))

    # interpreter
    def runPandapowerTests(self):
        self.ipyConsole.executeCommand("import pandapower.test as test")
        self.ipyConsole.executeCommand("print('Running tests ...')")
        #self.ipyConsole.executeCommand("test.run_all_tests()")

    # collections
    def initialiseCollectionsPlot(self):
        """Initialize network plot."""
        logger.info("Inialise Network Collections")
        self.xmin = self.net.bus_geodata.x.min()
        self.xmax = self.net.bus_geodata.x.max()
        self.ymin = self.net.bus_geodata.y.min()
        self.ymax = self.net.bus_geodata.y.max()
        self.scale = max((self.xmax - self.xmin), (self.ymax - self.ymin))
        self.collections = {}
        self.updateBusCollection()
        self.updateLineCollection()
        self.updateTrafoCollections()
        self.updateLoadCollections()
        self.updateExtGridCollections()
        logger.info(self.collections)
        self.drawCollections()

    def drawCollections(self):
        """Fill network plot."""
        self.network_graph.canvas.ax.clear()
        for name, c in self.collections.items():
            if c is not None:
                self.network_graph.canvas.ax.add_collection(c)
                self.network_graph.canvas.ax.set_xlim((self.xmin*0.98, self.xmax*1.02))
                self.network_graph.canvas.ax.set_ylim((self.ymin*0.98, self.ymax*1.02))
                self.network_graph.canvas.draw()
        logger.info("Drew Network Collections")

    # Result collections
    def initialiseResultCollectionsPlot(self, selection=['simple']):
        """Initialize results plot.

        TODO(result_collections): add more predefined result plots
        TODO(result_collections): add more collections
        TODO(result_collections): add random geodata if *_geodata is empty
        TODO(result_collections): create GUI for plot customisation
        """
        self.result_collections = {}
        if 'simple' in selection:
            self.updateSimplePlotCollection()
        if 'line_loading' in selection:
            self.updateLineLoadingPlotCollection()
        if 'bus_voltage' in selection:
            self.updateBusVoltagePlotCollection()
        if 'bus' in selection:
            self.updateBusResultsCollection()
        if 'line' in selection:
            self.updateLineResultsCollection()
        if 'dummy' in selection:
            self.updateDummyResultsCollection()
        # self.updateTrafoCollections()
        # self.updateLoadCollections()
        # self.updateExtGridCollections()
        self.drawResultCollections()

    def clearResultCollectionsPlot(self):
        """Empty results plot."""
        self.result_plot.canvas.ax.cla()
        self.result_plot.canvas.draw()
        self.pushButton.setEnabled(False)
        self.pushButton_2.setEnabled(False)
        self.pushButton_3.setEnabled(False)
        # self.result_plot.canvas.fig.clf()

    def drawResultCollections(self, plot_colorbars=True):
        """Fill results plot."""
        self.result_plot.canvas.ax.clear()
        self.result_plot.canvas.cbar_load = {}
        for name, c in self.result_collections.items():
            if c:
                self.result_plot.canvas.ax.add_collection(c)
                if plot_colorbars and hasattr(c, "has_colormap") and c.has_colormap:
                    extend = c.extend if hasattr(c, "extend") else "neither"
                    self.result_plot.canvas.cbar_load[name] = plt.colorbar(
                        c, extend=extend, ax=self.result_plot.canvas.ax, shrink=0.9)
        self.result_plot.canvas.ax.set_xlim((self.xmin*0.98, self.xmax*1.02))
        self.result_plot.canvas.ax.set_ylim((self.ymin*0.98, self.ymax*1.02))
        self.result_plot.canvas.draw()

        # remove colorbar to avoid infitit extension
        for name in self.result_plot.canvas.cbar_load.keys():
            self.result_plot.canvas.cbar_load[name].remove()

        logger.info("Drew Result Collections")

    @pyqtSlot()
    def on_click_standard_plot(self):
        """Load the simple_plot to the results plot."""
        self.initialiseResultCollectionsPlot()

    @pyqtSlot()
    def on_click_line_loading_plot(self):
        """Load the line loading plot to the results plot."""
        self.initialiseResultCollectionsPlot(selection=['line_loading'])

    @pyqtSlot()
    def on_click_bus_voltage_plot(self):
        """Load the bus voltage plot to the results plot."""
        self.initialiseResultCollectionsPlot(selection=['bus_voltage'])

    @pyqtSlot()
    def on_click_dummy_plot(self):
        """Load a nonstandard (here: dummy -> only trafos) plot to the results plot."""
        self.initialiseResultCollectionsPlot(selection=['dummy'])

    def updateDummyResultsCollection(self, redraw=False):
        """Update dummy collection in results plot."""
        t1, t2 = plot.create_trafo_collection(
            self.net, picker=True, size=self.scale*0.02, infofunc=lambda x: ("trafo", x))
        self.result_collections["trafo2"] = t2
        self.result_collections["trafo1"] = t1
        if redraw:
            self.drawResultCollections()

    def updateLineLoadingPlotCollection(self, redraw=True):
        """Update line loading collection in results plot."""
        cmap_list = [(20, "green"), (50, "yellow"), (60, "red")]
        cmap, norm = plot.cmap_continous(cmap_list)

        lc = plot.create_line_collection(
            self.net, self.net.line.index, zorder=1, cmap=cmap, norm=norm, linewidths=2)

        self.result_collections["line"] = lc

        if redraw:
            self.drawResultCollections()

    def updateBusVoltagePlotCollection(self, redraw=True):
        """Update bus voltage collection in results plot."""
        cmap_list = [(20, "green"), (50, "yellow"), (60, "red")]
        cmap, norm = plot.cmap_continous(cmap_list)

        lc = plot.create_line_collection(
            self.net, self.net.line.index, zorder=1, cmap=cmap, norm=norm, linewidths=2)

        cmap_list = [(0.975, "blue"), (1.0, "green"), (1.03, "red")]
        cmap, norm = plot.cmap_continous(cmap_list)
        bc = plot.create_bus_collection(
            self.net, self.net.bus.index, size=80, zorder=2, cmap=cmap, norm=norm)

        self.result_collections["line"] = lc
        self.result_collections["bus"] = bc

        if redraw:
            self.drawResultCollections()

    def updateBusCollection(self, redraw=False):
        bc = plot.create_bus_collection(self.net, size=self.scale*0.01,
                zorder=2, picker=True, color="black",  patch_type="rect",
                infofunc=lambda x: ("bus", x))
        self.collections["bus"] = bc
        if redraw:
            self.drawCollections()

    def updateSimplePlotCollection(
        self, redraw=True, respect_switches=False,  line_width=1.0, bus_size=1.0,
        ext_grid_size=1.0, switch_size=1.0, switch_distance=1.0,
        plot_line_switches=False, scale_size=True, bus_color="b", line_color='grey',
        trafo_color='k', ext_grid_color='y', switch_color='k', library="igraph",
        show_plot=True):
        """Update collection simple_plot style in results plot."""
        # don't hide lines if switches are plotted
        if plot_line_switches:
            respect_switches = False

        # create geocoord if none are available
        if len(self.net.line_geodata) == 0 and len(self.net.bus_geodata) == 0:
            logger.warning("No or insufficient geodata available --> Creating artificial coordinates." +
                           " This may take some time")
            plot.create_generic_coordinates(self.net, respect_switches=respect_switches, library=library)

        if scale_size:
            # if scale_size -> calc size from distance between min and max geocoord
            mean_distance_between_buses = sum((self.net['bus_geodata'].max() - self.net[
                'bus_geodata'].min()) / 200)
            # set the bus / ext_grid sizes accordingly
            # Comment: This is implemented because if you would choose a fixed values
            # (e.g. bus_size = 0.2), the size
            # could be to small for large networks and vice versa
            bus_size *= mean_distance_between_buses
            ext_grid_size *= mean_distance_between_buses * 1.5
            switch_size *= mean_distance_between_buses * 1
            switch_distance *= mean_distance_between_buses * 2

        # create bus collections to plot
        bc = plot.create_bus_collection(self.net, self.net.bus.index, size=bus_size, color=bus_color, zorder=10)
        if bc:
            self.result_collections["bus"] = bc

        # if bus geodata is available, but no line geodata
        use_bus_geodata = len(self.net.line_geodata) == 0
        in_service_lines = self.net.line[self.net.line.in_service].index
        nogolines = set(self.net.switch.element[(self.net.switch.et == "l") & (self.net.switch.closed == 0)]) \
            if respect_switches else set()
        plot_lines = in_service_lines.difference(nogolines)

        # create line collections
        lc = plot.create_line_collection(
            self.net, plot_lines, color=line_color, linewidths=line_width,
            use_bus_geodata=use_bus_geodata)
        if lc:
            self.result_collections["line"] = lc

        # create ext_grid collections
        eg_buses_with_geo_coordinates = set(self.net.ext_grid.bus.values) & set(self.net.bus_geodata.index)
        if len(eg_buses_with_geo_coordinates) > 0:
            eg = plot.create_bus_collection(self.net, eg_buses_with_geo_coordinates, patch_type="rect",
                                       size=ext_grid_size, color=ext_grid_color, zorder=11)
        if eg:
            self.result_collections["ext_grid"] = eg

        # create trafo collection if trafo is available
        trafo_buses_with_geo_coordinates = [t for t, trafo in self.net.trafo.iterrows()
                                            if trafo.hv_bus in self.net.bus_geodata.index and
                                            trafo.lv_bus in self.net.bus_geodata.index]
        if len(trafo_buses_with_geo_coordinates) > 0:
            tc = plot.create_trafo_collection(self.net, trafo_buses_with_geo_coordinates,
                                                color=trafo_color)

        # create trafo3w collection if trafo3w is available
        trafo3w_buses_with_geo_coordinates = [
            t for t, trafo3w in self.net.trafo3w.iterrows() if trafo3w.hv_bus in self.net.bus_geodata.index and
            trafo3w.mv_bus in self.net.bus_geodata.index and trafo3w.lv_bus in self.net.bus_geodata.index]
        if len(trafo3w_buses_with_geo_coordinates) > 0:
            tc = plot.create_trafo3w_collection(self.net, trafo3w_buses_with_geo_coordinates,
                                                  color=trafo_color)

        if tc:
            self.result_collections["trafo1"] = tc[0]
            self.result_collections["trafo2"] = tc[1]


        # FIXME: switches prevent the whole simple plot from functioning
        # if plot_line_switches and len(self.net.switch):
        #     sc = plot.create_line_switch_collection(
        #         self.net, size=switch_size, distance_to_bus=switch_distance,
        #         use_line_geodata=not use_bus_geodata, zorder=12, color=switch_color)
        # if sc:
        #     self.result_collections["switches"] = sc

        if redraw:
            self.drawResultCollections()

    def updateBusResultsCollection(self, redraw=False):
        """Update collection for buses in results plot."""
        cmap_list = [(0.975, "blue"), (1.0, "green"), (1.03, "red")]
        cmap, norm = plot.cmap_continous(cmap_list)
        bc = plot.create_bus_collection(
            self.net, size=self.scale*0.01,
            zorder=2, picker=True, cmap=cmap, norm=norm, infofunc=lambda x: ("bus", x))

        self.result_collections["bus"] = bc
        if redraw:
            self.drawResultCollections()

    def updateExtGridCollections(self, redraw=False):
        eg1, eg2 = plot.create_ext_grid_collection(
            self.net, size=self.scale*0.05, zorder=2, picker=True,
            infofunc=lambda x: ("ext_grid", x))
        self.collections["ext_grid1"] = eg1
        self.collections["ext_grid2"] = eg2
        if redraw:
            self.drawCollections()

    def updateLineCollection(self, redraw=False):
        lc = plot.create_line_collection(
                self.net, self.net.line.index, zorder=1, linewidths=1,
                picker=True, color="green",
                use_bus_geodata=True,  # use_line_geodata=False,
                infofunc=lambda x: ("line", x))
        self.collections["line"] = lc
        if redraw:
            self.drawCollections()

    def updateLineResultsCollection(self, redraw=False):
        """Update collection for lines in results plot."""
        cmap_list = [(20, "green"), (50, "yellow"), (60, "red")]
        cmap, norm = plot.cmap_continous(cmap_list)

        lc = plot.create_line_collection(
            self.net, self.net.line.index, zorder=1, cmap=cmap, norm=norm, linewidths=1,
            use_bus_geodata=True,  # use_line_geodata=False,
            picker=True, infofunc=lambda x: ("line", x))

        self.result_collections["line"] = lc
        if redraw:
            self.drawCollections()

    def updateTrafoCollections(self, redraw=False):
        t1, t2 = plot.create_trafo_collection(self.net, picker=True, size=self.scale*0.02,
                                                     infofunc=lambda x: ("trafo", x))
        self.collections["trafo1"] = t1
        self.collections["trafo2"] = t2
        if redraw:
            self.drawCollections()

    def updateLoadCollections(self, redraw=False):
        l1, l2 = plot.create_load_collection(self.net, size=self.scale*0.02,
                                                    picker=True,
                                                    infofunc=lambda x: ("load", x))
        self.collections["load1"] = l1
        self.collections["load2"] = l2
        if redraw:
            self.drawCollections()

    def updateGenCollections(self, redraw=False):
        l1, l2 = plot.create_gen_collection(self.net, size=self.scale*0.02,
                                                   picker=True,
                                                   infofunc=lambda x: ("gen", x))
        self.collections["gen1"] = l1
        self.collections["gen2"] = l2
        if redraw:
            self.drawCollections()

    # clear the figure in widget_1
    def clearMainCollectionBuilder(self):
        self.network_graph.canvas.ax.clear()
        logger.info("figure cleared")
        self.net = pp.create_empty_network()
        self.collections = {}
        self.drawCollections()

    def embedCollectionsBuilder(self):
        """Show the network plot in widget_1."""
        self.dpi = 100
        self.network_graph = MplWidget(self.widget_1)
        # self.fig = plt.Figure()
        # self.canvas = FigureCanvas(self.fig)
        # self.ax = self.fig.add_subplot(111)
        # self.ax.set_axis_bgcolor("white")
        # when a button is pressed on the canvas?
        # FIXME(embedCollectionsBuilder): clicking elements does not work any more
        # TODO(embedCollectionsBuilder): implement mouse-over events
        self.network_graph.canvas.mpl_connect('button_press_event', self.onCollectionsClick)
        # self.canvas.mpl_connect('button_release_event', self.onCollectionsClick)
        self.network_graph.canvas.mpl_connect('pick_event', self.onCollectionsPick)

        mpl_toolbar = NavigationToolbar(self.network_graph.canvas, self.widget_1)
        # self.gridLayout.addWidget(self.network_graph.canvas)
        # self.gridLayout.addWidget(mpl_toolbar)
        self.network_graph.add_toolbar(mpl_toolbar)

        self.network_graph.canvas.fig.subplots_adjust(
            left=0.0, right=1, top=1, bottom=0, wspace=0.02, hspace=0.04)
        self.dragged = None

    def embedResultCollectionsBuilder(self):
        """Create a figure for result plots in widget_2.

        # TODO(embedResultCollectionsBuilder): implement mouse-over events
        """
        self.dpi = 100
        self.result_plot = MplWidget(self.widget_2)
        mpl_toolbar = NavigationToolbar(self.result_plot.canvas, self.widget_2)
        self.result_plot.add_toolbar(mpl_toolbar)
        self.result_plot.canvas.fig.subplots_adjust(
            left=0.0, right=1, top=1, bottom=0, wspace=0.02, hspace=0.04)
        self.dragged = None

    def onCollectionsClick(self, event):
        logger.info("clicked")
        self.collectionsDoubleClick = event.dblclick
        self.last = "clicked"
        if self.create_bus.isChecked():
            geodata = (event.xdata, event.ydata)
            try:
                self.bus_window = BusWindow(self.net,
                                            self.updateBusCollection,
                                            geodata=geodata)
            except Exception as inst:
                logger.warning("{}".format(inst))

    def onCollectionsPick(self, event):
        if self.collectionsDoubleClick == False:
            QTimer.singleShot(200,
                              partial(self.performcollectionsSingleClickActions, event))

    def performcollectionsSingleClickActions(self, event):
        logger.info("picked")
        collection = event.artist
        element, index = collection.info[event.ind[0]]
        logger.info("==== {}".format(event.ind[0]))
        logger.info("==== {}".format(collection))
        logger.info("single")
        if self.collectionsDoubleClick:
            # ignore second click of collectionsDoubleClick
            if self.last == "doublecklicked":
                self.last = "clicked"
            else:
                self.last = "doublecklicked"
                logger.info("Double Clicked a {}".format(element))
                self.open_element_window(element, index)
        else:
            self.collectionsSingleClickActions(event, element, index)

    def open_element_window(self, element, index):
        if element == "bus":
            logger.info("will build bus")
            self.element_window = BusWindow(self.net,
                                            self.updateBusCollection,
                                            index=index)
        elif element == "line":
            logger.info("will bild line")
            logger.info("{}".format(index))
            self.element_window = LineWindow(self.net,
                                             self.updateLineCollection,
                                             index=index)
        elif element == "load":
            self.element_window = LoadWindow(self.net,
                                             self.updateLoadCollections,
                                             index=index)
        elif element == "gen":
            self.element_window = GenWindow(self.net,
                                            self.updateGenCollections,
                                            index=index)
        elif element == "ext_grid":
            self.element_window = ExtGridWindow(self.net,
                                                self.updateExtGridCollections,
                                                index=index)
        elif element == "trafo":
            logger.info("trafo doubleclicked")

    def collectionsSingleClickActions(self, event, element, index):
        # what to do when single clicking on an element
        if element != "bus":
            return
        if self.create_line.isChecked():
            if self.lastBusSelected is None:
                self.lastBusSelected = index
            elif self.lastBusSelected != index:
                self.build_message.setText(str(self.lastBusSelected)+"-"+str(index))
                self.line_window = LineWindow(self.net,
                                              self.updateLineCollection,
                                              from_bus=self.lastBusSelected,
                                              to_bus=index)
                self.lastBusSelected = None
        elif self.create_trafo.isChecked():
            if self.lastBusSelected is None:
                self.lastBusSelected = index
            elif self.lastBusSelected != index:
                self.build_message.setText(str(self.lastBusSelected)+"-"+str(index))
                self.trafo_window = TrafoWindow(
                    self.net, self.updateTrafoCollections, from_bus=self.lastBusSelected,
                    to_bus=index)
                self.lastBusSelected = None
                # pp.create_transformer(self.net, self.lastBusSelected, index,
                #                       std_type="0.25 MVA 10/0.4 kV")
                # self.lastBusSelected = None
                # self.updateTrafoCollections()
                # self.drawCollections()
        elif self.create_load.isChecked():
            try:
                self.load_window = LoadWindow(self.net,
                                              self.updateLoadCollections,
                                              bus=index)
            except Exception as e:
                logger.warning("{}".format(e))
            self.lastBusSelected = None
        elif self.create_gen.isChecked():
            try:
                self.gen_window = GenWindow(self.net,
                                            self.updateGenCollections,
                                            bus=index)
            except Exception as e:
                logger.warning("{}".format(e))
            self.lastBusSelected = None
        elif self.create_ext_grid.isChecked():
            try:
                self.ext_grid_window = ExtGridWindow(self.net,
                                                     self.updateExtGridCollections,
                                                     bus=index)
            except Exception as e:
                logger.warning("{}".format(e))
            self.lastBusSelected = None


class runscOptions(QDialog):
    def __init__(self, net, parent=None):
        super(runscOptions, self).__init__(parent=parent)
        uic.loadUi('resources/ui/sc_widget.ui', self)
        self.net = net
        self.faults = {"3ph": self.sc_3ph, "2ph": self.sc_2ph}
        self.cases = {"max": self.case_max, "min": self.case_min}
        self.set_parameters(**self.net._runsc_options)
        self.okBtn.clicked.connect(partial(self.exit_window, True, False))
        self.cancelBtn.clicked.connect(partial(self.exit_window, False, False))
        self.runBtn.clicked.connect(partial(self.exit_window, True, True))
        self.show()

    def set_parameters(self, **kwargs):
        fault = kwargs.get("fault", "3ph")
        case = kwargs.get("case", "max")
        self.faults[fault].setChecked(True)
        self.cases[case].setChecked(True)

    def get_parameters(self):
        for fault, widget in self.faults.items():
            if widget.isChecked():
                self.net._runsc_options["fault"] = fault
        for case, widget in self.cases.items():
            if widget.isChecked():
                self.net._runsc_options["case"] = case

    def exit_window(self, save, run):
        if save:
            self.get_parameters()
        if run:
            self.parent().runsc()
        self.close()


class runppOptions(QDialog):
    def __init__(self, net, parent=None):
        super(runppOptions, self).__init__(parent=parent)
        uic.loadUi('resources/ui/runpp_options.ui', self)
        self.net = net
        self.inits = {"flat": self.InitFlat, "dc": self.InitDC, "results": self.InitResults,
                      "auto":self.InitAuto}
        self.algos = {"nr": self.NewtonRaphson, "bf": self.BackwardForward}
        self.voltage_angles = {True: self.VoltageAnglesTrue, False: self.VoltageAnglesFalse,
                               "auto": self.VoltageAnglesAuto}
        self.set_parameters(**self.net._runpp_options)
        self.ok_button.clicked.connect(partial(self.exit_window, True, False))
        self.cancel_button.clicked.connect(partial(self.exit_window, False, False))
        self.run_button.clicked.connect(partial(self.exit_window, True, True))
        self.show()

    def set_parameters(self, **kwargs):
        init = kwargs.get("init", "auto")
        algorithm = kwargs.get("algorithm", "nr")
        voltage_angles = kwargs.get("calculate_voltage_angles", "auto")
        enforce_q_lims = kwargs.get("enforce_q_lims", False)
        voltage_dependent_loads = kwargs.get("voltage_dependent_loads", True)

        self.inits[init].setChecked(True)
        self.algos[algorithm].setChecked(True)
        self.voltage_angles[voltage_angles].setChecked(True)
        self.EnforceQLims.setChecked(enforce_q_lims)
        self.VoltageDependent.setChecked(voltage_dependent_loads)

    def get_parameters(self):
        for init, widget in self.inits.items():
            if widget.isChecked():
                self.net._runpp_options["init"] = init
        for algorithm, widget in self.algos.items():
            if widget.isChecked():
                self.net._runpp_options["algorithm"] = algorithm
        for voltage_angles, widget in self.voltage_angles.items():
            if widget.isChecked():
                self.net._runpp_options["calculate_voltage_angles"] = voltage_angles
        self.net._runpp_options["enforce_q_lims"] = self.EnforceQLims.isChecked()
        self.net._runpp_options["voltage_dependent_loads"] = self.VoltageDependent.isChecked()

    def exit_window(self, save, run):
        if save:
            self.get_parameters()
        if run:
            self.parent().runpp()
        self.close()


def displaySplashScreen(n=2):
    """Create and display the splash screen."""
    splash_pix = QPixmap('resources/icons/panda-power.png')
    splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
    splash.setMask(splash_pix.mask())
    splash.show()
    app.processEvents()
    time.sleep(n)
    splash.hide()


def createSampleNetwork():
    net = pp.create_empty_network()
    b1 = pp.create_bus(net, vn_kv=20., name="HV", geodata=(5, 30))
    b2 = pp.create_bus(net, vn_kv=0.4, name="MV", geodata=(5, 28))
    b3 = pp.create_bus(net, vn_kv=0.4, name="Load Bus", geodata=(5, 22))

    # create bus elements
    pp.create_ext_grid(net, bus=b1, vm_pu=1.02, s_sc_max_mva=2, rx_max=0.1, name="Grid Connection")
    pp.create_load(net, bus=b3, p_kw=100, q_kvar=50, name="Load")

    # create branch elements
    tid = pp.create_transformer(net, hv_bus=b1, lv_bus=b2, std_type="0.4 MVA 20/0.4 kV",
                                name="Trafo")
    pp.create_line(
        net, from_bus=b2, to_bus=b3, length_km=0.1, geodata=((5, 28), (5, 22)),
        name="Line", std_type="NAYY 4x50 SE")
    return net

if __name__ == '__main__':
    app = 0
    app = QApplication(sys.argv)
    displaySplashScreen()
    window = mainWindow()
    sys.exit(app.exec_())
