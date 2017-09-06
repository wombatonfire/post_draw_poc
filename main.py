import itertools
import pickle
import sys
import time

import numpy as np

from matplotlib.animation import Animation
from matplotlib.backends.backend_qt5agg import FigureCanvas
from matplotlib.figure import Figure

from PyQt5 import QtWidgets
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject, QThread
from PyQt5.uic import loadUiType

FormClass, QtBaseClass = loadUiType('main_window.ui')


class MainWindow(FormClass, QtBaseClass):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

    def add_plot(self, plot, event_source):
        canvas = FigureCanvas(plot.fig)
        layout = QtWidgets.QHBoxLayout(self.centralwidget)
        layout.addWidget(canvas)
        ani = DataAnimation(plot, event_source, blit=True)
        canvas.draw()


class Plot(object):
    def __init__(self):
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_xlim(0, 11)
        self.ax.set_ylim(0, 11)
        self.line1 = self.ax.plot([], [], 'o')[0]
        self.updated_artists = []

    def update(self, new_data):
        line1_xdata, line1_ydata = self.line1.get_data()
        x, y = pickle.loads(new_data)
        self.line1.set_data(np.append(line1_xdata, x),
                            np.append(line1_ydata, y))
        self.updated_artists = [self.line1]


class DataReceivedEventListener(object):
    def __init__(self, update_func):
        self.update_plot = update_func
        self.started = False
        self.callbacks = []

    def start(self):
        self.started = True

    def stop(self):
        self.started = False

    def add_callback(self, func, *args, **kwargs):
        self.callbacks.append((func, args, kwargs))

    def remove_callback(self, func, *args, **kwargs):
        if args or kwargs:
            self.callbacks.remove((func, args, kwargs))
        else:
            funcs = [c[0] for c in self.callbacks]
            if func in funcs:
                self.callbacks.pop(funcs.index(func))

    @pyqtSlot(str)
    def on_event(self, coord):
        self.update_plot(coord)
        if self.started:
            for func, args, kwargs in self.callbacks:
                func(*args, **kwargs)


class DataReceiver(QObject):
    data_received_signal = pyqtSignal(str)

    def __init__(self, event_source):
        super(DataReceiver, self).__init__()
        self.data_received_signal.connect(event_source.on_event)

    @pyqtSlot()
    def start(self):
        for i in xrange(11):
            coord = np.random.randint(1, 11, 2)
            self.data_received_signal.emit(pickle.dumps(coord))
            time.sleep(3)



class DataAnimation(Animation):
    def __init__(self, plot, event_source, *args, **kwargs):
        super(DataAnimation, self).__init__(plot.fig, event_source=event_source, *args, **kwargs)
        self.plot = plot

    def new_frame_seq(self):
        return itertools.count()

    def _draw_frame(self, frame_data):
        self._drawn_artists = self.plot.updated_artists
        for artist in self._drawn_artists:
            artist.set_animated(self._blit)

    # def _end_redraw(self, evt):
    #     self._post_draw(None, self._blit)
    #     self.event_source.start()
    #     self._fig.canvas.mpl_disconnect(self._resize_id)
    #     self._resize_id = self._fig.canvas.mpl_connect('resize_event', self._handle_resize)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    main_window = MainWindow()
    plot = Plot()
    event_source = DataReceivedEventListener(plot.update)
    data_receiver = DataReceiver(event_source)
    data_receiver_thread = QThread()
    data_receiver.moveToThread(data_receiver_thread)
    data_receiver_thread.started.connect(data_receiver.start)
    data_receiver_thread.start()
    main_window.add_plot(plot, event_source)
    main_window.show()
    sys.exit(app.exec_())
