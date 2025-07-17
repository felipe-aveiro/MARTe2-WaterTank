from PySide2.QtNetwork import QUdpSocket

import numpy as np
import pyqtgraph as pg

from pyqtgraph.Qt import QtWidgets, QtCore

UDP_PORT = 7755

win = pg.GraphicsLayoutWidget(show=True)
win.setWindowTitle('Waveform Plot')

waveform_buffer = np.zeros(100)

ptr = 0

plot = win.addPlot()
curve = plot.plot(waveform_buffer, pen='w', name="Waveform")
plot.setYRange(-0.1, 0.1)

udpSocket = QUdpSocket()
udpSocket.bind(UDP_PORT)

def readPendingDatagrams():
    global waveform_buffer, ptr

    while udpSocket.hasPendingDatagrams():
        datagram = udpSocket.receiveDatagram()
        raw_data = datagram.data() 
        print(raw_data)

        try:
            values64 = np.frombuffer(raw_data, dtype=np.float64)

            if values64.size > 0:
                # print(f"Waveform signal: {values64[0]}")

                waveform_buffer[:-1] = waveform_buffer[1:]
                waveform_buffer[-1] = values64[0]

                ptr += 1
                curve.setData(waveform_buffer)
                curve.setPos(ptr, 0)
        except Exception as e:
            print(f"Error processing datagram: {e}")

udpSocket.readyRead.connect(readPendingDatagrams)

timer = QtCore.QTimer()
timer.start(100)

if __name__ == '__main__':
    pg.exec()
