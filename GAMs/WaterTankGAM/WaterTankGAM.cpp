/**
 * @file WaterTankGAM.cpp
 * @brief Source file for class WaterTankGAM
 * @date 02/07/2025
 * @authors Bernardo Brotas de Carvalho & Felipe Tassari Aveiro (adapted from previous work by Andre Neto)
 *
 * @copyright Copyright 2015 F4E | European Joint Undertaking for ITER and
 * the Development of Fusion Energy ('Fusion for Energy').
 * Licensed under the EUPL, Version 1.1 or - as soon they will be approved
 * by the European Commission - subsequent versions of the EUPL (the "Licence")
 * You may not use this work except in compliance with the Licence.
 * You may obtain a copy of the Licence at: http://ec.europa.eu/idabc/eupl
 *
 * @warning Unless required by applicable law or agreed to in writing, 
 * software distributed under the Licence is distributed on an "AS IS"
 * basis, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
 * or implied. See the Licence permissions and limitations under the Licence.

 * @details This source file contains the definition of all the methods for
 * the class WaterTankGAM (public, protected, and private). Be aware that some 
 * methods, such as those inline could be defined on the header file, instead.
 * 
 * @note Compilation command:
 * 
 * $ make -C GAMs/WaterTankGAM -f Makefile.gcc
 * 
 */

/*---------------------------------------------------------------------------*/
/*                         Standard header includes                          */
/*---------------------------------------------------------------------------*/

/*---------------------------------------------------------------------------*/
/*                         Project header includes                           */
/*---------------------------------------------------------------------------*/

#include "AdvancedErrorManagement.h"
#include "WaterTankGAM.h"

/*---------------------------------------------------------------------------*/
/*                           Static definitions                              */
/*---------------------------------------------------------------------------*/

/*---------------------------------------------------------------------------*/
/*                           Method definitions                              */
/*---------------------------------------------------------------------------*/
//namespace MARTe2WaterTank {
namespace MARTe {
/**
 * The number of signals
 */
    const  uint32 EP_NUM_INPUTS  = 2u;
    const  uint32 EP_NUM_OUTPUTS = 2u;

WaterTankGAM::WaterTankGAM() {
    // Initialization
    lastUsecTime  = 0.0;
    // Parameters
    lastHeight    = 0.0;
    bFlowRate     = 0.0;
    aFlowRate     = 0.0;
    tankArea      = 0.0;
    maxVoltage    = 0.0;
    minVoltage    = 0.0;
    // GAM Inputs
    usecTime = NULL_PTR(MARTe::uint32 *);
    pumpVoltageRequest = NULL_PTR(MARTe::float64*);
    // GAM Outputs
    waterHeight = NULL_PTR(MARTe::float64 *);
    pumpVoltage = NULL_PTR(MARTe::float64 *);
}

WaterTankGAM::~WaterTankGAM() {
    // GAM Inputs
    usecTime = NULL_PTR(MARTe::uint32 *);
    pumpVoltageRequest = NULL_PTR(MARTe::float64 *);
    // GAM Outputs
    waterHeight = NULL_PTR(MARTe::float64 *);
    pumpVoltage = NULL_PTR(MARTe::float64 *);
}

bool WaterTankGAM::Initialise(MARTe::StructuredDataI & data) {
    // using namespace MARTe;
    bool ok = GAM::Initialise(data);
    if (!ok) {
        REPORT_ERROR(ErrorManagement::ParametersError, "Could not Initialise the GAM");
        return ok;
    }
    ok = data.MoveRelative("Parameters");
    if (!ok) {
        REPORT_ERROR(ErrorManagement::ParametersError, "The 'Parameters' node is missing in the configuration");
        return ok;
    }
    if (ok) {
        ok = data.Read("InitialHeight", lastHeight);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The parameter InitialHeight shall be set inside 'Parameters'");
        } else {
            REPORT_ERROR(ErrorManagement::Information, "Parameter InitialHeight set to %f", lastHeight);
        }
    }

    if (ok) {
        ok = data.Read("InputFlowRate", bFlowRate);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The parameter InputFlowRate shall be set inside 'Parameters'");
        } else {
            REPORT_ERROR(ErrorManagement::Information, "Parameter InputFlowRate set to %f", bFlowRate);
        }
    }

    if (ok) {
        ok = data.Read("OutputFlowRate", aFlowRate);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The parameter OutputFlowRate shall be set inside 'Parameters'");
        } else {
            REPORT_ERROR(ErrorManagement::Information, "Parameter OutputFlowRate set to %f", aFlowRate);
        }
    }

    if (ok) {
        ok = data.Read("TankArea", tankArea);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The parameter TankArea shall be set inside 'Parameters'");
        } else {
            REPORT_ERROR(ErrorManagement::Information, "Parameter TankArea set to %f", tankArea);
        }
    }

    if (ok) {
        ok = data.Read("MaxVoltage", maxVoltage);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The parameter MaxVoltage shall be set inside 'Parameters'");
        } else {
            REPORT_ERROR(ErrorManagement::Information, "Parameter MaxVoltage set to %f", maxVoltage);
        }
    }

    if (ok) {
        ok = data.Read("MinVoltage", minVoltage);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The parameter MinVoltage shall be set inside 'Parameters'");
        } else {
            if (minVoltage < 0.0) {
                REPORT_ERROR(ErrorManagement::Information,
                             "MinVoltage cannot be negative due to physical constraints. "
                             "The pump cannot extract water; therefore MinVoltage is set to 0.0.");
                minVoltage = 0.0;
            } else {
                REPORT_ERROR(ErrorManagement::Information, "Parameter MinVoltage set to %f", minVoltage);
            }
        }
    }

    data.MoveToAncestor(1u);
    
    return ok;
}

bool WaterTankGAM::Setup() {
    // using namespace MARTe;
    // Input Signals
    uint32 numberOfInputSignals = GetNumberOfInputSignals();
    bool ok = (numberOfInputSignals == 2u);
    if (!ok) {
        REPORT_ERROR(ErrorManagement::ParametersError,
                "The number of input signals shall be equal to 2. numberOfInputSignals = %d ", numberOfInputSignals);
    }
    if (ok) {
            TypeDescriptor inputSignalType = GetSignalType(InputSignals, 0u);
            ok = (inputSignalType == UnsignedInteger32Bit);
            if (!ok) {
                const char8 * const inputSignalTypeStr = TypeDescriptor::GetTypeNameFromTypeDescriptor(inputSignalType);
                REPORT_ERROR(ErrorManagement::ParametersError,
                        "The UsecTime input signal type shall be uint32. inputSignalType = %s", inputSignalTypeStr);
                return ok;
            }
            inputSignalType = GetSignalType(InputSignals, 1u);
            ok = (inputSignalType == Float64Bit);
            if (!ok) {
                const char8 * const inputSignalTypeStr = TypeDescriptor::GetTypeNameFromTypeDescriptor(inputSignalType);
                REPORT_ERROR(ErrorManagement::ParametersError,
                        "The pumpVoltageRequest input signal type shall be float64. inputSignalType = %s", inputSignalTypeStr);
                return ok;
            }
    }

     if (ok) {
        usecTime = reinterpret_cast<uint32 *>(GetInputSignalMemory(0u));
        pumpVoltageRequest = reinterpret_cast<float64 *>(GetInputSignalMemory(1u));
        REPORT_ERROR(ErrorManagement::Information, "InputSignals reinterpret_cast OK");
    }

     // Output Signals
     uint32 numberOfOutputSignals = GetNumberOfOutputSignals();     
     ok = (numberOfOutputSignals == 2u);
     if (!ok) {
         REPORT_ERROR(ErrorManagement::ParametersError, "The number of output signals shall be equal to 2. numberOfOutputSignals = %d ", numberOfOutputSignals);
     }
     if (ok) {
            TypeDescriptor outputSignalType = GetSignalType(OutputSignals, 0u);
            ok = (outputSignalType == Float64Bit);
            if (!ok) {
                const char8 * const outputSignalTypeStr = TypeDescriptor::GetTypeNameFromTypeDescriptor(outputSignalType);
                REPORT_ERROR(ErrorManagement::ParametersError,
                        "The the WaterHeight output signal type shall be float64. outputSignalType = %s", outputSignalTypeStr);
                return ok;
            }
            outputSignalType = GetSignalType(OutputSignals, 1u);
            ok = (outputSignalType == Float64Bit);
            if (!ok) {
                const char8 * const outputSignalTypeStr = TypeDescriptor::GetTypeNameFromTypeDescriptor(outputSignalType);
                REPORT_ERROR(ErrorManagement::ParametersError,
                        "The PumpVoltage output signal type shall be float64. outputSignalType = %s", outputSignalTypeStr);
                return ok;
            }
    }

     if (ok) {
        waterHeight = reinterpret_cast<float64 *>(GetOutputSignalMemory(0u));
        pumpVoltage = reinterpret_cast<float64 *>(GetOutputSignalMemory(1u));
        REPORT_ERROR(ErrorManagement::Information, "OutputSignals reinterpret_cast OK");
    }

    if (ok) {
        uint32 numberOfInputSamples = 0u;
        uint32 numberOfOutputSamples = 0u;
        ok = GetSignalNumberOfSamples(InputSignals, 0u, numberOfInputSamples);
        if (ok) {
            ok = GetSignalNumberOfSamples(OutputSignals, 0u, numberOfOutputSamples);
        }
        if (ok) {
            ok = (numberOfInputSamples == numberOfOutputSamples);
        }
        if (ok) {
            ok = (numberOfInputSamples == 1u);
        }
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError,
                         "The number of input and output signals samples shall be equal to 1. numberOfInputSamples = %d | numberOfOutputSamples = %d",
                         numberOfInputSamples, numberOfOutputSamples);
            ok = false;
        }
    }
    if (ok) {
        uint32 numberOfInputDimensions = 0u;
        uint32 numberOfOutputDimensions = 0u;
        ok = GetSignalNumberOfDimensions(InputSignals, 0u, numberOfInputDimensions);
        if (ok) {
            ok = GetSignalNumberOfDimensions(OutputSignals, 0u, numberOfOutputDimensions);
        }
        if (ok) {
            ok = (numberOfInputDimensions == numberOfOutputDimensions);
        }
        if (ok) {
            ok = (numberOfInputDimensions == 0u);
        }
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError,
                         "The number of input and output signals dimensions shall be equal to 0. numberOfInputDimensions = %d | numberOfOutputDimensions = %d",
                         numberOfInputDimensions, numberOfOutputDimensions);
            ok = false;
        }
    }
    if (ok) {
        uint32 numberOfInputElements = 0u;
        uint32 numberOfOutputElements = 0u;
        ok = GetSignalNumberOfElements(InputSignals, 0u, numberOfInputElements);
        if (ok) {
            ok = GetSignalNumberOfElements(OutputSignals, 0u, numberOfOutputElements);
        }
        if (ok) {
            ok = (numberOfInputElements == numberOfOutputElements);
        }
        if (ok) {
            ok = (numberOfInputElements == 1u);
        }
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError,
                         "The number of input and output signals elements shall be equal to 1. numberOfInputElements = %d | numberOfOutputElements = %d",
                         numberOfInputElements, numberOfOutputElements);
            ok = false;
        }
    }

    return ok;

}

bool WaterTankGAM::Execute() {
    // This function executes every MARTe2 cycle
    float64 voltage = *pumpVoltageRequest;
    
    // Saturate voltage

    if(voltage > maxVoltage){
        voltage = maxVoltage;
    }
    if(voltage < minVoltage){
        voltage = minVoltage;
    }            

    // Simple forward Euler method (1e-3 due to 1 kHz)
    float64 height  = ((voltage * bFlowRate - (aFlowRate * sqrt(lastHeight))) / tankArea) * (*usecTime - lastUsecTime) * 1e-6 + lastHeight;
    
    // Introduction of noise for future applications
    /*
    std::default_random_engine gen;
    std::normal_distribution<double> dist(0.0,1.0);
   
    height += dist(gen);
    */

    // Even when tank empties outplut flow rate is still lowering water level
    // values, therefore impose this condition to maitain coherence
    if(height < 0.0){
        REPORT_ERROR(ErrorManagement::Warning, "Tank height is negative: %f", height);
        height = 0.0;
    }

    // Persistent values
    lastHeight      = height;
    lastUsecTime    = *usecTime;

    // Output values
    *waterHeight = height;
    *pumpVoltage = voltage;

    return true;
}


bool WaterTankGAM::ExportData(MARTe::StructuredDataI & data) {
    //using namespace MARTe;
    bool ok = GAM::ExportData(data);
    if (ok) {
        ok = data.CreateRelative("Parameters");
    }
    if (ok) {
        ok = data.Write("InitialHeight", lastHeight);
    }
    if (ok) {
        ok = data.Write("InputFlowRate", bFlowRate);
    }
    if (ok) {
        ok = data.Write("OutputFlowRate", aFlowRate);
    }
    if (ok) {
        ok = data.Write("TankArea", tankArea);
    }
    if (ok) {
        ok = data.Write("MaxVoltage", maxVoltage);
    }
    if (ok) {
        ok = data.Write("MinVoltage", minVoltage);
    }
    if (ok) {
        ok = data.MoveToAncestor(1u);
    }
    return ok;
}

CLASS_REGISTER(WaterTankGAM, "")
}
