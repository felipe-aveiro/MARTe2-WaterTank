# **MARTe2-WaterTank**
###

> [!NOTE]
> This repository is part of the experimental setup and development of a **Master's thesis** in Mechanical Engineering. It explores real-time control and simulation using _MARTe2_ and _Simulink_-generated components.

## _Description_

MARTe2-WaterTank is a project built on top of the [***MARTe2***](https://vcis.f4e.europa.eu/marte2-docs/master/html/) framework, simulating and controlling the water level in a tank using real-time control techniques. The system includes:

- A non-linear water tank model implemented as a GAM (Generic Application Module)
- Configurable PID controllers
- UDP-based communication for monitoring and data acquisition
- Real-time data visualization in Python (matplotlib)
- Startup scripts and modular configuration

This repository demonstrates how _MARTe2_ can be used for distributed real-time control systems, with integration support for [***Simulink***](https://nl.mathworks.com/products/simulink.html)-generated models and performance monitoring.

## _Key Features_
> $\textsf{\color{white}{Non-linear water tank simulation with inflow control}}$
> 
> $\textsf{\color{white}{Tunable PID controller for water level regulation}}$
> 
> $\textsf{\color{white}{Real-time data exchange via UDP sockets}}$
> 
> $\textsf{\color{white}{Python scripts for plotting time vs. water height curves}}$
> 
> $\textsf{\color{white}{Compatibility with Simulink-generated shared libraries (.so)}}$

## _Repository Structure_
>`Configurations/: .cfg` $${\color{white}\text{- files with system setup and parameters}}$$
> 
> `Startup/:` $${\color{white}\text{- launch scripts}}$$  $${\color{white}\text{(}}$$ `Main.sh` $${\color{white}\text{)}}$$ $${\color{white}\text{and Python plotting utilities}}$$
> 
> `GAMs/:` $${\color{white}\text{- implementation of the custom Generic Application Modules}}$$
> 
> `Build/:` $${\color{white}\text{- compiled binaries and generated libraries}}$$
> 
> `README.md:` $${\color{white}\text{- project overview and usage}}$$
