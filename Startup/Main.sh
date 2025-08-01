#!/bin/bash
#Arguments -f FILENAME -m MESSAGE | -s STATE [-d cgdb|strace]

MDS=0
DEBUG=""
INPUT_ARGS=$*
while test $# -gt 0
do
    case "$1" in
        -d|--debug)
        DEBUG="$2"
        ;;
        -mds)
        MDS=1
        ;;
    esac
    shift
done

export MARTe_DIR=/opt/marte
export MARTe2_DIR=$MARTe_DIR/MARTe2-dev
export MARTe2_Components_DIR=$MARTe_DIR/MARTe2-components
export MARTe2_Demos_DIR=$MARTe_DIR/MARTe2-demos-padova

LD_LIBRARY_PATH=$LD_LIBRARY_PATH:../Build/x86-linux/Components/GAMs/WaterTankGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:../Build/x86-linux/Components/GAMs/FloatPIDGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:../Build/x86-linux/Components/GAMs/MagneticRZPosGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:../Build/x86-linux/Components/GAMs/MagneticADCConversionGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:../Build/x86-linux/Components/GAMs/MagneticArrayADCConversionGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:../Build/x86-linux/Components/DataSources/UARTOutput
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:../MatlabLibs/

LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/DataSources/ADCSimulator/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/DataSources/MDSReaderNS/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/DataSources/MDSStream/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/DataSources/SimpleUDPSender/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/GAMs/FixedGAMExample1/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/GAMs/VariableGAMExample1/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/GAMs/TimeGeneratorGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/GAMs/VoltToDacGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/GAMs/AdcToVoltGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/GAMs/FilterDownsamplingGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/Interfaces/TCPSocketMessageProxyExample/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/Other/ControllerEx1/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Demos_DIR/Build/x86-linux/Components/Other/ControllerEx2/

LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_DIR/Build/x86-linux/Core/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/DataSources/EPICSCA/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/DataSources/EPICSPVA/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/DataSources/LinuxTimer/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/DataSources/LoggerDataSource/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/DataSources/FileDataSource/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/DataSources/LinkDataSource/
# LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/DataSources/OPCUADataSource/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/DataSources/UDP/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/DataSources/MDSReader/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/DataSources/MDSWriter/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/DataSources/RealTimeThreadSynchronisation/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/DataSources/RealTimeThreadAsyncBridge/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/GAMs/ConstantGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/GAMs/ConversionGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/GAMs/IOGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/GAMs/FilterGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/GAMs/HistogramGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/GAMs/MathExpressionGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/GAMs/PIDGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/GAMs/SimulinkWrapperGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/GAMs/SSMGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/GAMs/TriggerOnChangeGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/GAMs/WaveformGAM/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/Interfaces/BaseLib2Wrapper/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/Interfaces/EPICS/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/Interfaces/EPICSPVA/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/Interfaces/MemoryGate/
# LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/Interfaces/OPCUA/
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$MARTe2_Components_DIR/Build/x86-linux/Components/Interfaces/SysLogger/

#LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$SDN_CORE_LIBRARY_DIR
LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$EPICS_BASE/lib/$EPICS_HOST_ARCH
# LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$SDN_CORE_LIBRARY_DIR
# LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$CODAC_ROOT/lib/

echo $LD_LIBRARY_PATH
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH

export isttokmarte_path=/opt/mdsplus/trees

if [ "$DEBUG" = "cgdb" ]
then
    cgdb --args $MARTe2_DIR/Build/x86-linux/App/MARTeApp.ex $INPUT_ARGS
else
    $MARTe2_DIR/Build/x86-linux/App/MARTeApp.ex $INPUT_ARGS
fi

