"""
Various methods of drawing scrolling plots.
"""

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
win.setWindowTitle('pyqtgraph example: Scrolling Plots')


# 1) Simplest approach -- update data in the array such that plot appears to scroll
#    In these examples, the array size is fixed.

def readPendingDatagrams():
    global udpSocket, data2, ptr2

    while udpSocket.hasPendingDatagrams():
        datagram = udpSocket.receiveDatagram()
        data = datagram.data()
        print(data)
        time = np.frombuffer(data, dtype=np.uint32)
        print(f"Counter: {time[0]}, Time: {time[1]} \u00b5s")
        values64 = np.frombuffer(data, dtype=np.float64)
        print(f"Reference: {values64[0]}, Actual Value: {values64[1]}")

        data2[:-1] = data2[1:]  # shift data in the array one sample left
        data2[-1] = values64[1]
        ptr2 += 1
        curve2.setData(data2)
        curve2.setPos(ptr2, 0)
        data2b[:-1] = data2b[1:]  # shift data in the array one sample left
        data2b[-1] = values64[2]
        curve2b.setData(data2b)
        curve2b.setPos(ptr2, 0)
#        processTheDatagram(datagram)


# Create a UDP socket
# Notice the use of SOCK_DGRAM for UDP packets
# udpSocket = socket(AF_INET, SOCK_DGRAM)
udpSocket = QUdpSocket()

# udpSocket.bind(('', UDP_PORT))
# udpSocket.bind(QHostAddress.LocalHost, UDP_PORT)
udpSocket.bind(UDP_PORT)
# udpSocket.bind("127.0.0.1", 7755)
udpSocket.readyRead.connect(
            readPendingDatagrams)


p1 = win.addPlot()
p2 = win.addPlot()
data1 = np.random.normal(size=300)
curve1 = p1.plot(data1)
data2 = np.zeros(30)
data2b = np.zeros(30)


curve2 = p2.plot(data2, pen='r', name="Reference")
curve2b = p2.plot(data2b)
ptr1 = 0
ptr2 = 0

def update1():
    global data1, ptr1
    data1[:-1] = data1[1:]  # shift data in the array one sample left
                            # (see also: np.roll)
    data1[-1] = np.random.normal()
    curve1.setData(data1)

    ptr1 += 1
#    curve2.setData(data1)
#    curve2.setPos(ptr1, 0)
    
# update all plots
def update():
    update1()
#    update2()
#    update3()

timer = pg.QtCore.QTimer()
timer.timeout.connect(update)
timer.start(500)

if __name__ == '__main__':
    pg.exec()

