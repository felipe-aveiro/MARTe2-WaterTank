import socket
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg')

UDP_IP = "localhost"
UDP_PORT = 7755

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((UDP_IP, UDP_PORT))

print("UDP server is up and listening...")

# Storing received data
times = []  # Store time values (x axis)
ref_values = []  # Store reference values (y axis)
heights = []  # Store height values (y axis)

# Graphic settings (no real-time updates)
# plt.ion()
fig, ax = plt.subplots()
line, = ax.plot([], [], label='Water Height') # Line for water height
line2, = ax.plot([], [], label='Reference Value', linestyle='--')  # Line for reference value
ax.set_xlim(0, 30000)  
ax.set_ylim(0, 100) 
ax.set_xlabel('Time (ms)')
ax.set_ylabel('Water Height (m)')
ax.legend()

count = 0
while count < 30000:
    try:
        # Receive data
        data, client_address = server_socket.recvfrom(1024)

        # Unpack data
        time = np.frombuffer(data, dtype=np.uint32)
        values64 = np.frombuffer(data, dtype=np.float64)

        # Store data in arrays
        times.append(time[0])
        ref_values.append(values64[1])
        heights.append(values64[2])

        print(f"Timer: {time[0]:.2f} s | RefValue: {values64[1]:.2f} | WaterHeight: {values64[2]:.3f}")

        # line.set_xdata(times)
        # line.set_ydata(heights)

        # Updates data
        # plt.draw()
        # plt.pause(0.1)  # Pause to update

        count += 1

    except KeyboardInterrupt:
        print("\nApplication killed.\n")
        break

line.set_xdata(times)
line.set_ydata(heights)

line2.set_xdata(times)  # Set reference time values
line2.set_ydata(ref_values)  # Set reference height values

# Show the plot window with the data
# plt.show()
plt.savefig('/home/felipe/git-repos/MARTe2-WaterTank/Startup/output_graph.png')

# Close socket
server_socket.close()
