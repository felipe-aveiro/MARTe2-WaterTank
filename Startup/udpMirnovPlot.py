# from time import perf_counter

from PySide2.QtNetwork import QUdpSocket, QHostAddress


import numpy as np

import pyqtgraph as pg

from pyqtgraph.Qt import (
        QtWidgets,
        QtCore,)

from pyqtgraph.Qt.QtWidgets import (
        QVBoxLayout,
        QMessageBox,)
# from socket import socket, AF_INET, SOCK_DGRAM

UDP_PORT = 7755       # Target port
# from PyQt6.QtNetwork import QUdpSocket, QHostAddress

win = pg.GraphicsLayoutWidget(show=True)
win.setWindowTitle('Scrolling Mirnov Plots')

N_CHANNELS = 12
BUFFER_SIZE = 300

# -- update data in the array such that plot appears to scroll

mirnov_plot = win.addPlot()
mirnov_plot.setLabel('left', 'Mirnov Signals')
mirnov_plot.addLegend()

data_buffers = [np.empty(BUFFER_SIZE) for _ in range(N_CHANNELS)]
curves = []

for i in range(N_CHANNELS):
    curve = mirnov_plot.plot(pen=pg.intColor(i, hues=N_CHANNELS), name=f'Mirnov_{i}')
    curves.append(curve)

ptr_mirnov = 0

def readPendingDatagrams():
    global udpSocket, mirnov_packet, ptr_mirnov, data_buffers

    while udpSocket.hasPendingDatagrams():
        datagram = udpSocket.receiveDatagram()
        mirnov_packet = datagram.data()
        mirnov = np.frombuffer(mirnov_packet, dtype=np.float32)

        for i in range(N_CHANNELS):
            data_buffers[i][:-1] = data_buffers[i][1:] # shift data in the array one sample left
            data_buffers[i][-1] = mirnov[i]
            curves[i].setData(data_buffers[i])
            curves[i].setPos(ptr_mirnov, 0)

        
    ptr_mirnov += 1


# Create a UDP socket
# Notice the use of SOCK_DGRAM for UDP packets
# udpSocket = socket(AF_INET, SOCK_DGRAM)
udpSocket = QUdpSocket()

"""
# udpSocket.bind(('', UDP_PORT))
# udpSocket.bind(QHostAddress.LocalHost, UDP_PORT)
# udpSocket.bind("127.0.0.1", 7755)
"""
udpSocket.bind(UDP_PORT) 

udpSocket.readyRead.connect(readPendingDatagrams)

timer = pg.QtCore.QTimer()
#timer.timeout.connect(update)
timer.start(100)

if __name__ == '__main__':
    pg.exec()

