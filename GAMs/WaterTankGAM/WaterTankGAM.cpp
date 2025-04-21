/**
 * @file WaterTankGAM.cpp
 * @brief Source file for class WaterTankGAM
 * @date 06/04/2018
 * @author Andre Neto
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
 * Compile command:
 *  make -C GAMs/WaterTankGAM -f Makefile.gcc
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
//namespace MARTe2Tutorial {
namespace MARTe {
/**
 * The number of signals
 */
    const  uint32 EP_NUM_INPUTS  = 2u;
    const  uint32 EP_NUM_OUTPUTS = 2u;

WaterTankGAM::WaterTankGAM() {
    //gain = 0u;
    lastHeight    = 0;
    lastVoltage   = 0;
    lastUsecTime  = 0;
    bFlowRate     = 0;
    aFlowRate     = 0;
    tankArea      = 0;
    maxVoltage    = 0;
    minVoltage    = 0;
    // GAM Inputs
    usecTime = NULL_PTR(MARTe::uint32 *);
    pumpVoltageRequest = NULL_PTR(MARTe::float64*);
    // Outputs
    waterHeight = NULL_PTR(MARTe::float64 *);
    pumpVoltage = NULL_PTR(MARTe::float64 *);
}

WaterTankGAM::~WaterTankGAM() {

}

bool WaterTankGAM::Initialise(MARTe::StructuredDataI & data) {
    //using namespace MARTe;
    bool ok = GAM::Initialise(data);
    if (!ok) {
        REPORT_ERROR(ErrorManagement::ParametersError, "Could not Initialise the GAM");
    }
    if (ok) {
        ok = data.Read("InputFlowRate", aFlowRate);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The parameter InputFlowRate shall be set");
        }
    }
    if (ok) {
        REPORT_ERROR(ErrorManagement::Information, "Parameter InputFlowRate set to %f", aFlowRate);
    }
    if (ok) {
        ok = data.Read("OutputFlowRate", bFlowRate);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The parameter OutputFlowRate shall be set");
        }
    }
    if (ok) {
        REPORT_ERROR(ErrorManagement::Information, "Parameter InputFlowRate set to %f", bFlowRate);
    }
    if (ok) {
        ok = data.Read("TankArea", tankArea);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The parameter TankArea shall be set");
        }
    }
    if (ok) {
        REPORT_ERROR(ErrorManagement::Information, "Parameter TankArea set to %f", tankArea);
    }
    if (ok) {
        ok = data.Read("MaxVoltage", maxVoltage);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The parameter MaxVoltage shall be set");
        }
    }
    if (ok) {
        REPORT_ERROR(ErrorManagement::Information, "Parameter MaxVoltage set to %f", maxVoltage);
    }
    if (ok) {
        ok = data.Read("MinVoltage", minVoltage);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The parameter MinVoltage shall be set");
        }
    }
    if (ok) {
        REPORT_ERROR(ErrorManagement::Information, "Parameter MinVoltage set to %f", minVoltage);
    }
    return ok;
}

bool WaterTankGAM::Setup() {
    //using namespace MARTe;
    uint32 numberOfInputSignals = GetNumberOfInputSignals();
    bool ok = (numberOfInputSignals == 2u);
    if (!ok) {
        REPORT_ERROR(ErrorManagement::ParametersError,
                "The number of input signals shall be equal to 2. numberOfInputSignals = %d ", numberOfInputSignals);
    }

    if (ok) {

            StreamString inputSignalName;
            ok = GetSignalName(InputSignals, 0u, inputSignalName);
            TypeDescriptor inputSignalType = GetSignalType(InputSignals, 0u);
            ok = (inputSignalType == UnsignedInteger32Bit);
            if (!ok) {
                const char8 * const inputSignalTypeStr = TypeDescriptor::GetTypeNameFromTypeDescriptor(inputSignalType);
                REPORT_ERROR(ErrorManagement::ParametersError,
                        "The type of the input signals shall be uint32. inputSignalType = %s", inputSignalTypeStr);
            }
            ok = GetSignalName(InputSignals, 1u, inputSignalName);
            inputSignalType = GetSignalType(InputSignals, 1u);
            ok = (inputSignalType == Float64Bit);
            if (!ok) {
                const char8 * const inputSignalTypeStr = TypeDescriptor::GetTypeNameFromTypeDescriptor(inputSignalType);
                REPORT_ERROR(ErrorManagement::ParametersError,
                        "The type of the input signals shall be float64. inputSignalType = %s", inputSignalTypeStr);
            }
    }

     if (ok) {
        usecTime = reinterpret_cast<uint32 *>(GetInputSignalMemory(0u));
        pumpVoltageRequest = reinterpret_cast<float64 *>(GetInputSignalMemory(1u));
        REPORT_ERROR(ErrorManagement::Information, "InputSignals reinterpret_cast OK");
    }

     // OutputSignals
     uint32 numberOfOutputSignals = GetNumberOfOutputSignals();
     ok = (numberOfOutputSignals == 2u);
     if (!ok) {
         REPORT_ERROR(ErrorManagement::ParametersError, "The number of output signals shall be equal to 2. numberOfOutputSignals = %d ", numberOfOutputSignals);
     }
/*  TODO: check type, elements, etc 


    if (ok) {
        TypeDescriptor outputSignalType = GetSignalType(OutputSignals, 0u);
        ok = (inputSignalType == outputSignalType);
        if (ok) {
            ok = (inputSignalType == UnsignedInteger32Bit);
        }
        if (!ok) {
            const char8 * const outputSignalTypeStr = TypeDescriptor::GetTypeNameFromTypeDescriptor(outputSignalType);
            REPORT_ERROR(ErrorManagement::ParametersError,
                         "The type of the input and output signal shall be uint32. inputSignalType = %s outputSignalType = %s", inputSignalTypeStr,
                         outputSignalTypeStr);
        }
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
                         "The number of input and output signals samples shall be equal to 1. numberOfInputSamples = %d numberOfOutputSamples = %d",
                         numberOfInputSamples, numberOfOutputSamples);
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
                         "The number of input and output signals dimensions shall be equal to 0. numberOfInputDimensions = %d numberOfOutputDimensions = %d",
                         numberOfInputDimensions, numberOfOutputDimensions);
        }
    }
    if (ok) {
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
                         "The number of input and output signals elements shall be equal to 1. numberOfInputElements = %d numberOfOutputElements = %d",
                         numberOfInputElements, numberOfOutputElements);
        }
    }
*/
    if (ok) {
        waterHeight = reinterpret_cast<float64 *>(GetOutputSignalMemory(0u));
        pumpVoltage = reinterpret_cast<float64 *>(GetOutputSignalMemory(1u));
        REPORT_ERROR(ErrorManagement::Information, "OutputSignals reinterpret_cast OK");
    }
    return ok;

}

bool WaterTankGAM::Execute() {
    // This fucntion executes every MARTe2 cycle
    float64 voltage = *pumpVoltageRequest;
    //Saturate voltage
    if(voltage > maxVoltage){
        voltage = maxVoltage;
    }
    if(voltage < minVoltage){
        voltage = minVoltage;
    }            
    //simple Euler method
    float64 height  = (voltage * bFlowRate - aFlowRate * sqrt(lastHeight)) / tankArea * (*usecTime - lastUsecTime) * 1e-6 + lastHeight;
    if(height < 0){
        REPORT_ERROR(ErrorManagement::Warning, "Tank height is negative: %f", height);
        height = 0;
    }
    lastHeight      = height;
    lastUsecTime    = *usecTime;
    lastVoltage     = voltage;
    // Output values
            *waterHeight     = height;
            *pumpVoltage = voltage;
    //*outputSignal = *inputSignal;
    return true;
}


bool WaterTankGAM::ExportData(MARTe::StructuredDataI & data) {
    //using namespace MARTe;
    bool ok = GAM::ExportData(data);
    if (ok) {
        ok = data.CreateRelative("Parameters");
    }
    if (ok) {
        ok = data.Write("InputFlowRate", aFlowRate);
    }
    if (ok) {
        ok = data.Write("OuputFlowRate", bFlowRate);
    }
    if (ok) {
        ok = data.MoveToAncestor(1u);
    }
    return ok;
}

CLASS_REGISTER(WaterTankGAM, "")
}
