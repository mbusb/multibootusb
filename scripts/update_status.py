__author__ = 'sundar'
from PyQt4 import QtCore
import config

class UpdateStatusThread(QtCore.QThread):
    update_status = QtCore.pyqtSignal(str)
    def __init__(self, *args, **kwargs):
        QtCore.QThread.__init__(self)
        #self.function = function
        self.args = args
        self.kwargs = kwargs

    def __del__(self):
        self.wait()

    def run(self):
        #self.function(*self.args, **self.kwargs)
        while self.isRunning():
            self.update_status.emit(config.iso_extract_file_name)
        return