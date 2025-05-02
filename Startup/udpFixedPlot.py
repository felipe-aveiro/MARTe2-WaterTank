import socket
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use('Agg')

UDP_IP = "localhost"
UDP_PORT = 7755

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((UDP_IP, UDP_PORT))

print("\nUDP server is up and listening...\n")

# Storing received data
times = []  # Store time values (x axis)
ref_values = []  # Store reference values (y axis)
heights = []  # Store height values (y axis)

# Graphic settings (no real-time updates)
plt.ion()
fig, ax = plt.subplots()
line, = ax.plot([], [], label='Water Height', linewidth=2, color='#2285c5') # Line for water height
line2, = ax.plot([], [], label='Reference Value', linestyle='--', linewidth=2, color='#616161')  # Line for reference value
ax.set_xlim(0, 30)  
ax.set_ylim(0, 5) 
ax.set_xlabel('Time (seconds)')
ax.set_ylabel('Water Height (m)')
ax.legend(frameon=True, edgecolor='black')

plt.rcParams['font.family'] = 'Helvetica'

# Customization
for x in [5, 10, 15, 20, 25]:
    plt.axvline(x=x, color='#b6b6b6', linestyle='-', linewidth=0.5)  
for y in [5, 4, 3, 2, 1]:
    plt.axhline(y=y, color='#b6b6b6', linestyle='-', linewidth=0.5)

plt.tick_params(axis='both', direction='in', length=10, color='black')

plt.gcf().set_facecolor('#dcdcdc')

time = np.zeros(2, dtype=np.uint32)  

while time[0] <= 30:
    try:
        # Receive data
        data, client_address = server_socket.recvfrom(1024)

        # Unpack data
        time = np.frombuffer(data, dtype=np.uint32)
        values64 = np.frombuffer(data, dtype=np.float64)

        # Store data in arrays
        times.append(time[0]-1)
        ref_values.append(values64[1])
        heights.append(values64[2])

        print(f"Timer: {time[0]-1} s | RefValue: {values64[1]:.2f} | WaterHeight: {values64[2]:.3f}")

    except KeyboardInterrupt:
        print("\nApplication killed.\n")
        break

line.set_xdata(times)
line.set_ydata(heights)

line2.set_xdata(times)  # Set reference time values
line2.set_ydata(ref_values)  # Set reference height values

# Save the plot window with the data
plt.savefig('/home/felipe/git-repos/MARTe2-WaterTank/Startup/output_graph.png')

# Close socket
server_socket.close()
