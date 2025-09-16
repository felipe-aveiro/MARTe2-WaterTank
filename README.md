# **MARTe2-WaterTank**

> [!NOTE]  
> This repository is part of the experimental setup and development of a Master's thesis in Mechanical Engineering - 'Real-Time Control of Vertical Plasma Position in ISTTOK: A Simulink-based Modeling Approach with MARTe2 Integration'. It explores real-time control and simulation using MARTe2, with applications ranging from a non-linear water tank system to plasma control studies at ISTTOK.

## **Overview**

MARTe2-WaterTank is a project built on top of the [***MARTe2***](https://vcis.f4e.europa.eu/marte2-docs/master/html/) framework, initially developed to simulate and control a non-linear water tank system in real-time. The work has since been extended to support plasma control studies, data acquisition, and visualization, integrating multiple tools such as Simulink and Python in ISTTOK. 

<table>
  <tr>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/2283fd95-8595-4a74-bf4a-034530c7f49e" 
           alt="ISTTOK tokamak at IPFN (Instituto Superior Técnico)" width="800" height="400"/>
    </td>
  </tr>
  <tr>
    <td align="center">
      <div style="font-size:14px; margin-top:6px;">
        <b>ISTTOK tokamak</b><br/>
        Photo credit: 
        <a href="https://isttok.tecnico.ulisboa.pt/~isttok.daemon/index.php?title=ISTTOK_-_Wiki" target="_blank">
        IPFN — Instituto de Plasmas e Fusão Nuclear (IST, Portugal)</a>.
      </div>
    </td>
  </tr>
</table>

## **Repository Structure**

The repository includes:

- [**_Configurations_**](Configurations)
  - [**RTApp-1-1.cfg**](Configurations/RTApp-1-1.cfg) | [**RTApp-1-1-statemachine.cfg**](Configurations/RTApp-1-1-statemachine.cfg) | [**RTApp-1-2-statemachine.cfg**](Configurations/RTApp-1-2-statemachine.cfg)
    - Tutorial configurations imported from MARTe2 documentation, used as references and for initial validation of the framework
  - [**RTApp-AtcaIop-EKF-Control.cfg**](Configurations/RTApp-AtcaIop-EKF-Control.cfg)
    - **Final configuration of the thesis work**
    - Implements EKFs for plasma state estimation and closes the loop with the plasma position controller, running on ATCA hardware. This setup represents the integrated control framework studied in the dissertation
  - [**RTApp-FloatPIDGAM-test.cfg**](Configurations/RTApp-FloatPIDGAM-test.cfg)
    - Dedicated configuration to validate the custom FloatPIDGAM, ensuring correct float32 signal handling across the pipeline
  - [**WaterTank_PID.cfg**](Configurations/WaterTank_PID.cfg)
    - Closed-loop configuration with the native MARTe2 PID controlling the WaterTankGAM, including UDP streaming for monitoring
  - [**WaterTank_Pid_udp.cfg**](Configurations/WaterTank_Pid_udp.cfg)
    - Configuration with the native MARTe2 PID and WaterTankGAM, featuring UDP streaming and multiple selectable reference signals (constant, ramp, sine)
  - [**WaterTank_Simulink_PID.cfg**](Configurations/WaterTank_Simulink_PID.cfg)
    - Configuration where the Simulink-generated PID regulates the WaterTankGAM, with UDP streaming enabled
  - [**WaterTank_Pid_udp_SimulinkModel.cfg**](Configurations/WaterTank_Pid_udp_SimulinkModel.cfg)
    - Configuration where the tank dynamics are modeled in Simulink, including both the native MARTe2 PID and the Simulink-generated PID, with UDP streaming
  - [**WaterTank_SDAS_DataFusion.cfg**](Configurations/WaterTank_SDAS_DataFusion.cfg) | [**WaterTank_SDAS_DataFusion_PID.cfg**](Configurations/WaterTank_SDAS_DataFusion_PID.cfg) | [**WaterTank_SDAS_DataFusion_PID_Atca_float32.cfg**](Configurations/WaterTank_SDAS_DataFusion_PID_Atca_float32.cfg)
    - Configurations for data fusion pipelines from SDAS data. The ATCA float32 version extends compatibility with real hardware channels
  - [**WaterTank_Magnetics_GAM.cfg**](Configurations/WaterTank_Magnetics_GAM.cfg) | [**WaterTank_Magnetics_Simulink.cfg**](Configurations/WaterTank_Magnetics_Simulink.cfg)
    - Magnetics processing pipelines: one built with user-created GAM, the other with Simulink-generated model. Used to benchmark unit handling and consistency
  - [**WaterTank_uart.cfg**](Configurations/WaterTank_uart.cfg) | [**WaterTank_uart_float32.cfg**](Configurations/WaterTank_uart_float32.cfg)
    - Test configurations for the custom UART DataSource, validating signal transmission (float64 vs float32)
  - [**WaterTank_waveform.cfg**](Configurations/WaterTank_waveform.cfg) | [**WaterTank_waveform_UDP.cfg**](Configurations/WaterTank_waveform_UDP.cfg)
    - Use an internal waveform generator as excitation source. The UDP version streams data to external Python visualisation scripts
- [**_DataSources_**](DataSources)
  - [_UARTOutput_](DataSources/UARTOutput)
    - Custom MARTe2 DataSource developed to enable UART communication with external hardware
      - Supports sending float32 and float64 signals
      - Provides a configurable interface for transmitting control or diagnostic data streams in real-time
      - Designed for integration with ATCA boards and other hardware paths where UART links are required
- [**_DataVisualization_**](DataVisualization)
  - [_CSVScripts_](DataVisualization/CSVScripts)
    - Utilities to load, clean, and export experiment data in CSV format from MDSplus and SDAS databases
  - [_ComparisonScripts_](DataVisualization/ComparisonScripts)
    - Scripts dedicated to signal comparison across diagnostics and reconstructions
    - [**SDAS-mirnov_comparison.py**](DataVisualization/ComparisonScripts/SDAS-mirnov_comparison.py)
      - Compares Mirnov coil signals obtained from SDAS database against CSV-extracted data for validation
    - [**fused-langmuir-mirnov_comparison.py**](DataVisualization/ComparisonScripts/fused-langmuir-mirnov_comparison.py)
      - Visualizes results from the fused state estimation versus standalone Langmuir and Mirnov reconstructions
    - [**langmuir-mirnov_comparison.py**](DataVisualization/ComparisonScripts/langmuir-mirnov_comparison.py)
      - Direct comparison of plasma position reconstructions from Langmuir probes and Mirnov coils
    - [**plasma-position-domenica_comparison.py**](DataVisualization/ComparisonScripts/plasma-position-domenica_comparison.py)
      - Benchmarks current work against plasma position estimation from [Domenica’s thesis](https://www.ipfn.tecnico.ulisboa.pt/news-and-events/news/281663955271747)
    - [**rogowski-mirnovReconstruction_comparison.py**](DataVisualization/ComparisonScripts/rogowski-mirnovReconstruction_comparison.py)
      - Compares plasma current from Rogowski coil measurements against Mirnov-based reconstruction
    - [**rogowski-mirnovReconstruction_metrics.py**](DataVisualization/ComparisonScripts/rogowski-mirnovReconstruction_metrics.py)
      - Extends the previous comparison by computing error metrics (quantitative validation)
  - [_CovarianceScripts_](DataVisualization/CovarianceScripts)
    - Scripts to compute/adjust covariance values used in estimators
    - Plots for inspecting diagonal terms and unit consistency
  - [_HistogramScripts_](DataVisualization/HistogramScripts)
    - Cycle-time histograms and timing diagnostics (paired with HistogramGAM outputs)
    - CSV → figure exporters for latency/jitter analysis
  - [_ISTTOK_shots_CSV_files_](DataVisualization/ISTTOK_shots_CSV_files)
    - [csv](DataVisualization/ISTTOK_shots_CSV_files/csv)
      - CSV exports of ISTTOK shot data pulled directly from SDAS or MDSplus. Organized by shot/diagnostic; meant as inputs, not derived results
  - [_LangmuirConstantsScripts_](DataVisualization/LangmuirConstantsScripts)
    - Scripts dedicated to the derivation and adjustment of Langmuir reconstruction constants from Mirnov-based reconstruction, focusing on regression analysis, weighting strategies, and visualization of fitted curves
    - [**huber-regression_langmuir_cte.py**](DataVisualization/LangmuirConstantsScripts/huber-regression_langmuir_cte.py)
      - Applies Huber regression to estimate Langmuir-related constants, providing robustness against outliers
    - [**interactive-huber-regressor_langmuir_cte.py**](DataVisualization/LangmuirConstantsScripts/interactive-huber-regressor_langmuir_cte.py)
      - Interactive variant of the Huber regression, allowing runs over specified intervals
    - [**langmuir-metrics.py**](DataVisualization/LangmuirConstantsScripts/langmuir-metrics.py)
      - Computes performance metrics for regression models and fitted constants
    - [**langmuir_optimization.py**](DataVisualization/LangmuirConstantsScripts/langmuir_optimization.py)
      - Optimization routines for refining Langmuir constants across different shots
    - [**regression-vis.py**](DataVisualization/LangmuirConstantsScripts/regression-vis.py)
      - Generates visualizations of regression fits and adjusted curves for analysis
    - [**weights.py**](DataVisualization/LangmuirConstantsScripts/weights.py)
      - Defines and computes weighting schemes used in regression and optimization processes
  - [_Outputs_](DataVisualization/Outputs)
    - [_CovarianceScatterPlots_](DataVisualization/Outputs/CovarianceScatterPlots)
      - Scatter/diagnostic plots from covariance tuning and sweeps
    - [_MARTe2-Engine_](DataVisualization/Outputs/MARTe2-Engine)
      - Plots and figures produced from MARTe2 executions of the WaterTank system
      - Includes runs with the WaterTankGAM (non-linear model implemented directly in C++)
      - Includes runs with the Simulink-generated WaterTank model integrated via SimulinkWrapperGAM
      - Used to compare MARTe2-native execution paths and validate consistency across models
    - [_Simulink-Engine_](DataVisualization/Outputs/Simulink-Engine)
      - Plots and figures generated by running the Water Tank model purely in Simulink, without MARTe2
      - Serves as an external reference to benchmark MARTe2 runs
    - [_PlasmaCurrentPlots_](DataVisualization/Outputs/PlasmaCurrentPlots)
      - Plasma current traces and comparisons: Rogowski measurements vs Mirnov-based reconstruction
    - [_PlasmaPositionPlots_](DataVisualization/Outputs/PlasmaPositionPlots)
      - Plasma position reconstructions: standalone diagnostics and fused results
    - [_PositionComparison_](DataVisualization/Outputs/PositionComparison)
      - Plots showing the time evolution of plasma position reconstructions from different diagnostics or references
      - Overlays radial and vertical position traces
      - Used to visually validate consistency and highlight discrepancies between independent reconstruction methods
    - [_VerticalControlPlots_](DataVisualization/Outputs/VerticalControlPlots)
      - Figures from simulated control scenarios focused on vertical plasma position control based on arbitrary references and previously acquired discharge data
      - Each plot combines two panels:
        - **Top panel**: vertical position (Zp) compared to the applied reference trajectory
        - **Bottom panel**: corresponding simulated vertical control current request
      - Used to evaluate controller effort under different excitation profiles
    - [_pyqtCSV-plots_](DataVisualization/Outputs/pyqtCSV-plots)
      - Static exports generated from [pyqt-CSV-shot_visualizer.py](DataVisualization/pyqt-CSV-shot_visualizer.py)
    - [**langmuir_coeficients.csv**](DataVisualization/Outputs/langmuir_coeficients.csv)
      - Collection of Langmuir-based reconstruction coefficients derived from Huber regression calculations and corresponding error metrics obtained for each analyzed shot
    - **Various CSV shot files**
      - Collection of outputs generated from different MARTe2 runs, produced for multiple purposes (e.g., DataFusion tests, ADC conversion validation, ISTTOK outputs). They serve as raw numerical results feeding the visualization and comparison scripts
  - [_UDPScripts_](DataVisualization/UDPScripts)
    - Python tools for real-time visualization and handling of UDP streams sent by MARTe2
    - [**udpFixedPlot.py**](DataVisualization/UDPScripts/udpFixedPlot.py)
      - Plots a fixed-length window of received UDP signals for quick inspection and exporting images
    - [**udpMirnovPlot.py**](DataVisualization/UDPScripts/udpMirnovPlot.py)
      - Real-time viewer tailored for Mirnov coil signals, displaying them as scrolling traces
    - [**udpPlot.py**](DataVisualization/UDPScripts/udpPlot.py)
      - Generic UDP plotting tool for arbitrary signals, using a scrolling time window
    - [**udpServer.py**](DataVisualization/UDPScripts/udpServer.py)
      - Simple UDP server to receive and display incoming packets, useful for debugging MARTe2 UDP outputs
    - [**udpwaveformPlot.py**](DataVisualization/UDPScripts/udpwaveformPlot.py)
      - Real-time single-channel UDP viewer for waveform outputs from MARTe2
  - [**SDASDynamicChannelViewer.py**](DataVisualization/SDASDynamicChannelViewer.py)
    - Interactive pyqtgraph viewer that connects to the SDAS server (via ``SDASClient(HOST, PORT)``) and plots signals directly from the database
    - Default shot: 46241; default channel: 228 (Rogowski)
    - UI supports Next/Previous channel, type-to-jump (channels 0–254) and type-to-jump shot
  - [**pyqt-CSV-shot_visualizer.py**](DataVisualization/pyqt-CSV-shot_visualizer.py)
    - Rich PyQtGraph viewer for shot CSVs (SDAS/MDS exports) with multi-view navigation and export
    - **Robust CSV loading**: file dialog; auto–delimiter detection (, / ;); infers dtype (float32 if filename contains “Atca”, else float64); extracts shot number from the filename
    - **Time handling**: builds time in ms; optionally crops all plots by ``chopper_trigger==3`` while keeping a separate chopper panel in full-time (the chopper plot always spans the full range)
    - **Views** (switch via on-screen arrow buttons):
      - **Main**: all 12 Mirnov traces + plasma current from Mirnov-based reconstruction panels (x-linked)
      - **Positions**: two stacked panels with white center lines and red limits
      - **Rogowski comparison**: Rogowski measurement comparison against plasma current obtained via Mirnov-based reconstruction
      - **PID requests**: stacked Radial and Vertical voltage request panels
      - **Fusion comparison**: overlays Mirnov- and Langmuir-based, and fused reconstructions for radial and vertical positions
    - **Interactive annotations**: click two points on any plot to mark them and display Δt and Δy (dashed guides + label); click a third time to clear
    - **Stateful zoom**: preserves the current x-range when changing between views
    - **One-click export**: buttons to save the current figure as PNG, with suggested names including shot and dtype suffix
  - [**vertical-position&reference-PID-requests_visualizer.py**](DataVisualization/vertical-position&reference-PID-requests_visualizer.py)
    - Two-panel PyQtGraph viewer to assess controller effort from a simulated control scenario (no actuation, only previous shot data considered) based on a single shot CSV
    - **Robust CSV loading**: file dialog; auto–delimiter detection (, / ;); infers dtype (float32 if filename contains “Atca”, else float64); extracts shot number from the filename
    - **Top panel**: fused reconstruction and reference overlay
    - **Bottom panel**: plots controller effort over time
    - **Bidirectional zoom/pan synchronization**: scaling or shifting one panel propagates proportionally to the other, preserving initial center and relative height
    - **Export**: saves both plots as PNG images with default names
- [**_GAMs_**](GAMs)
  - [**FloatPIDGAM**](GAMs/FloatPIDGAM)
    - Custom PID controller GAM supporting both float32 and float64 dtypes. Provides tunable parameters (Kp, Ki, Kd, limits) for real-time control within MARTe2
  - [**MagneticADCConversionGAM**](GAMs/MagneticADCConversionGAM)
    - Utility GAM for conversion of raw ADC signals from magnetic diagnostics into calibrated physical units. Ensures consistency of magnetic input channels used in reconstructions
  - [**MagneticArrayADCConversionGAM**](GAMs/MagneticArrayADCConversionGAM)
    - GAM designed to convert ADC-integrated float32 signals from magnetic coil arrays into a format compatible with MARTe2 processing (e.g., scaling and restructuring 16-channel data)
  - [**MagneticRZPosGAM**](GAMs/MagneticRZPosGAM)
    - Implements magnetic plasma position reconstruction (R, Z) using Mirnov coil signals
    - **Not functional! (incomplete)**
  - [**WaterTankGAM**](GAMs/WaterTankGAM)
    - Non-linear water tank dynamic model based on Torricelli’s law, developed as the main validation tool for this project. Supports real-time Euler integration with parameter validation and saturation handling
- [**_ISTTOK-model_**](ISTTOK-model)
  - Contains a simplistic CAD model of the ISTTOK tokamak, used for documentation purposes within the project
- [**_MatlabLibs_**](MatlabLibs)
  - Shared object libraries (``.so``) generated from Simulink models via Embedded Coder
  - Directly imported into MARTe2 configurations for hybrid simulations with Simulink-based components
- [**_Python_**](Python)
  - General-purpose Python utilities and MARTe2 extensions
  - Includes a UART visualization script to read outputs from ``/dev/ttyLoopRd`` at 921600 baud and log/print values in real-time for debugging and validation of UART communication
- [**_Simulink-models_**](Simulink-models)
  - Original Simulink (``.slx``) models used to generate the shared libraries in [MatlabLibs](MatlabLibs)
- [**_Startup_**](Startup)
  - Initialization and helper scripts to launch MARTe2 sessions

## **Key Features**

- Real-time modeling and control with MARTe2
- Non-linear water tank simulation for validation
- Plasma state estimation and control framework for ISTTOK
- Seamless integration with Simulink (models and controllers)
- Real-time data streaming via UDP and UART
- Comprehensive Python visualization ecosystem

## **Prerequisites**

### MARTe2 framework
- A working installation of [MARTe2](https://vcis-gitlab.f4e.europa.eu/aneto/MARTe2) and [MARTe2-components](https://vcis-gitlab.f4e.europa.eu/aneto/MARTe2-components)  
- GNU Make/CMake toolchain  
- C++11 (or later) compliant compiler  

### MATLAB / Simulink
- MATLAB R2025b (or later recommended)  
- Simulink + Embedded Coder toolboxes  
- Compiler configured for **Simulink/Embedded Coder → shared libraries (`.so`)** generation  

### Python
- Python ≥ 3.8  
- Required packages:  
  - `numpy`  
  - `pandas`  
  - `matplotlib`  
  - `pyqtgraph`  
  - `PySide2` (or `PyQt5`)  
  - `scipy`  

### External Dependencies
- **MDSplus/SDAS client** (required for ISTTOK data access)  
- **ATCA hardware interface** (needed for configurations such as `RTApp-AtcaIop-EKF-Control.cfg`)  
- Linux system with UART support (`/dev/ttyLoopRd` tested)  

> **For more information, consult the documentation or contact the authors.**
