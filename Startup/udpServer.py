import socket
import numpy as np

# Create a UDP socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to an address and port
server_address = ('localhost', 7755)
server_socket.bind(server_address)

print("UDP server is up and listening...")

while True:
    # Receive data from the client
    data, client_address = server_socket.recvfrom(1024)
    print(f"Received {len(data)} bytes, message: {data}")
    time = np.frombuffer(data, dtype=np.uint32)
    values64 = np.frombuffer(data, dtype=np.float64)
    print(f"Counter: {time[0]} RefValue: {values64[1]:.2f} "
          f"WaterHeight: {values64[2]:.3f}")
