# **MARTe2-WaterTank**

> [!NOTE]  
> This repository is part of the experimental setup and development of a Master's thesis in Mechanical Engineering. It explores real-time control and simulation using MARTe2 and Simulink-generated components.

## **Overview**

MARTe2-WaterTank is a project built on top of the [***MARTe2***](https://vcis.f4e.europa.eu/marte2-docs/master/html/) framework, simulating a non-linear water tank system with inflow control of the water level using real-time control techniques. The repository includes:

- [A non-linear water tank model implemented as a GAM (Generic Application Module)](MARTe2-WaterTank/GAMs/WaterTankGAM/)
- Real-time control implemented within MARTe2
  - [using native configurable PID controller](MARTe2-WaterTank/Configurations/WaterTank_Pid_udp.cfg)
  - [using configurable PID controller created with a Simulink user-defined function block](MARTe2-WaterTank/Configurations/WaterTank_Simulink_PID.cfg)
-  Data visualization leveraging Python codes
   -  [**TO DO**: Real-time visualization using `pyqtgraph`](MARTe2-WaterTank/Startup/udpPlot.py)
   -  [Plot generation using `matplotlib`]((MARTe2-WaterTank/Startup/udpFixedPlot.py))
- Startup scripts and modular configuration

This repository aims to validate and demonstrate how MARTe2 can be used for distributed real-time control systems, with integration support for [***Simulink***](https://nl.mathworks.com/products/simulink.html)-generated models and performance monitoring.

The project integrates a custom WaterTank GAM and a PID controller to enable accurate real-time simulation and control of the water tank height. Data communication is facilitated using UDP protocols to enable external monitoring and visualization.

## **Key Features**

- Non-linear water tank dynamics modeling with inflow control.
- Real-time control using tunable PID controller within MARTe2.
- Integration with Simulink generated code via Embedded Coder.
  - Compatibility with Simulink-generated shared libraries (.so) 
- Real-time data exchange via UDP sockets.
- Python scripts for data reception and plotting.

## **Repository Structure**
- `Configurations`: Configuration files (`.cfg`) containing component definitions and system parameters.
- `Startup`: Startup scripts (e.g., `Main.sh`), Python visualization tools, and plots generated from previous tests.
- `GAMs/WaterTankGAM`: Implementation of generic application modules used within the system, namely of the water tank model.
- - `MatlabLibs`: Shared object files (`.so`) generated from Simulink models for integration with MARTe2.
- `Simulink-models`: Simulink model files (`.slx`) corresponding to the shared libraries (`.so`) used for integration with MARTe2.
- `Build/x86-linux/Components/GAMs`: Generated binary files and libraries.
- `README.md`: Project/repository description.

### **Prerequisites**

- MARTe2 framework
- MATLAB with Simulink and Embedded Coder
- Python 3.x with required packages (`numpy`, `matplotlib`, etc.)



### **TO DO:**
- [ ] Write usage instructions

> **For more information, consult the documentation or contact the authors.**
