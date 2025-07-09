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


# ------------------------------------------------------------------------
# Storing received data (initial values for reference input)
times = [0.0]  # Store time values (x axis); force the first time value to 0
ref_values = [0.0]  # Store reference values (y axis); force the first reference value to 3.0
# For GAMRef -> ref_values = [/GAMRef/OutputSignals/Default]
# For GAMSin -> ref_values = [/GAMSin/Offset]
# For GAMRamp -> ref_values = [/GAMRamp/Expression/**evaluate expression with Input1 = 0**]
heights = [0.0]  # Store height values (y axis); force the first water height value to 0
# ------------------------------------------------------------------------

# ------------------------------------------------------------------------
# Set maximum time of 60 seconds
end_time = 60
time_interval = 1e-3  # Sampling time
# ------------------------------------------------------------------------



# Graphic settings (no real-time updates)
plt.ion()
fig, ax = plt.subplots()
line, = ax.plot([], [], label='Water Height', linewidth=2, color='#2285c5') # Line for water height
line2, = ax.plot([], [], label='Reference Value', linestyle='--', linewidth=2, color='#616161')  # Line for reference value

ax.set_xlim(0, end_time)  
ax.set_ylim(0, 1.5) 
ax.set_yticks([0.5, 1, 1.5])
ax.set_xlabel('Time (seconds)')
ax.set_ylabel('Water Height (m)')
ax.legend(frameon=True, edgecolor='black')

plt.rcParams['font.family'] = 'Helvetica'

# Customization
for x in [60, 50, 40, 30, 20, 10, 0]:
   plt.axvline(x=x, color='#b6b6b6', linestyle='-', linewidth=0.5)  
for y in [1.5, 1, 0.5]:
    plt.axhline(y=y, color='#b6b6b6', linestyle='-', linewidth=0.5)

plt.tick_params(axis='both', direction='in', length=10, color='black')

plt.gcf().set_facecolor('#dcdcdc')

time = np.zeros(2, dtype=np.uint32)

# Adjust x-ticks to include odd numbers
x_ticks = np.arange(0, 61, 10)  # Adjust to display from 0 to 60 seconds (step of 10)
plt.xticks(x_ticks)  # Set x-axis ticks to include all numbers
#odd_x_ticks = np.arange(1, 61, 2)  # Odd numbers between 1 and 10
#plt.xticks(np.append(x_ticks, odd_x_ticks))  # Include odd numbers as well

if time_interval == 1e-3:
    time_index = 'ms'
elif time_interval == 1e-2:
    time_index = 'cs'
else:
    time_index = ''

while time[0] <= end_time*(1/time_interval) - 1:
    try:
        # Receive data
        data, client_address = server_socket.recvfrom(1024)

        # Unpack data
        time = np.frombuffer(data, dtype=np.uint32)
        values64 = np.frombuffer(data, dtype=np.float64)

        # Store data in arrays
        times.append((time[0])*time_interval)
        ref_values.append(values64[1])
        heights.append(values64[2])

        print(f"Timer: {time[0]*time_interval:.3f} s | RefValue: {values64[1]:.2f} | WaterHeight: {values64[2]:.3f}")

    except KeyboardInterrupt:
        print("\nApplication killed.\n")
        break

line.set_xdata(times)
line.set_ydata(heights)

line2.set_xdata(times)  # Set reference time values
line2.set_ydata(ref_values)  # Set reference height values

# Save the plot window with the data
# Change name according to specific scenario
plt.savefig('/home/felipe/git-repos/MARTe2-WaterTank/DataVisualization/Outputs/MARTe2-Engine/output_graph_Simulink-comparison.png')
# Close socket
server_socket.close()
