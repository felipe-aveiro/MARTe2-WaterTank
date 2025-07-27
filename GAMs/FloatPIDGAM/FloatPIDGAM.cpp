/**
 * @file FloatPIDGAM.cpp
 * @brief Source file for class FloatPIDGAM
 * @date 27/07/2025
 * @author Felipe Tassari Aveiro (adapted from the work of Llorenc Capella)
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
 * the class FloatPIDGAM (public, protected, and private). Be aware that some 
 * methods, such as those inline could be defined on the header file, instead.
 * 
 * @note Compilation command:
 * 
 * $ make -C GAMs/FloatPIDGAM -f Makefile.gcc
 */

#define DLL_API

/*---------------------------------------------------------------------------*/
/*                         Standard header includes                          */
/*---------------------------------------------------------------------------*/

#include <math.h>

/*---------------------------------------------------------------------------*/
/*                         Project header includes                           */
/*---------------------------------------------------------------------------*/

#include "AdvancedErrorManagement.h"
#include "TypeCharacteristics.h"
#include "FastMath.h"
#include "FloatPIDGAM.h"

/*---------------------------------------------------------------------------*/
/*                           Static definitions                              */
/*---------------------------------------------------------------------------*/

/*---------------------------------------------------------------------------*/
/*                           Method definitions                              */
/*---------------------------------------------------------------------------*/
namespace MARTe {

FloatPIDGAM::FloatPIDGAM() {
    // Initialization
    kp = 0.0;
    kp64 = 0.0;
    proportional = 0.0;
    proportional64 = 0.0;
    ki = 0.0;
    ki64 = 0.0;
    kid = 0.0;
    kid64 = 0.0;
    integral = 0.0;
    integral64 = 0.0;
    kd = 0.0;
    kd64 = 0.0;
    kdd = 0.0;
    kdd64 = 0.0;
    derivative = 0.0;
    derivative64 = 0.0;
    sampleTime = 0.0;
    maxOutput = MAX_FLOAT32;
    minOutput = -MAX_FLOAT32;
    maxOutput64 = MAX_FLOAT64;
    minOutput64 = -MAX_FLOAT64;
    enableIntegral = true;
    lastInput = 0.0;
    lastInput64 = 0.0;
    lastIntegral = 0.0;
    lastIntegral64 = 0.0;
    enableSubstraction = false;
    reference = NULL_PTR(float32 *);
    measurement = NULL_PTR(float32 *);
    output = NULL_PTR(float32 *);
    reference64 = NULL_PTR(float64 *);
    measurement64 = NULL_PTR(float64 *);
    output64 = NULL_PTR(float64 *);
    nOfInputSignals = 0u;
    nOfOutputSignals = 0u;
    nOfInputElementsReference = 0u;
    nOfInputElementsMeasurement = 0u;
    nOfOutputElements = 0u;
    nOfInputSamplesReference = 0u;
    nOfInputSamplesMeasurement = 0u;
    nOfOuputSamples = 0u;
    inputReferenceDimension = 0u;
    inputMeasurementDimension = 0u;
    outputDimension = 0u;

}

FloatPIDGAM::~FloatPIDGAM() {
    reference = NULL_PTR(float32 *);
    measurement = NULL_PTR(float32 *);
    output = NULL_PTR(float32 *);
    reference64 = NULL_PTR(float64 *);
    measurement64 = NULL_PTR(float64 *);
    output64 = NULL_PTR(float64 *);

}

bool FloatPIDGAM::Initialise(MARTe::StructuredDataI & data) {
    using namespace MARTe;
    bool ok = GAM::Initialise(data);
    if (ok) {
        bool okp, oki, okd;
        okp = data.Read("Kp", kp);
        if (okp) {
            REPORT_ERROR(ErrorManagement::Information, "Proportional gain set to Kp = %.5f", kp);
        }
        if (!okp) {
            kp = 0.0;
            REPORT_ERROR(ErrorManagement::Warning, "Kp was not set. Defaulting to Kp = %.1f", kp);
        }
        oki = data.Read("Ki", ki);
        if (oki) {
            REPORT_ERROR(ErrorManagement::Information, "Integral gain set to Ki = %.5f", ki);
        }
        if (!oki) {
            ki = 0.0;
            REPORT_ERROR(ErrorManagement::Warning, "Ki was not set. Defaulting to Ki = %.1f", ki);
        }
        okd = data.Read("Kd", kd);
        if (okd) {
            REPORT_ERROR(ErrorManagement::Information, "Derivative gain set to Kd = %.5f", kd);
        }
        if (!okd) {
            kd = 0.0;
            REPORT_ERROR(ErrorManagement::Warning, "Kd was not set. Defaulting to Kd = %.1f", kd);
        }
        if (!okp && !oki && !okd) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "Kp, Ki and Kd missing! At least one gain parameter must be declared");
            return false;
        }
    }
    if (ok) {
        ok = data.Read("SampleTime", sampleTime);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "Error reading SampleTime");
        }
    }
    if (ok) {
        if (IsEqual(sampleTime, 0.0) || sampleTime < 0.0) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "SampleTime must be positive");
            ok = false;
        }
    }
    if (ok) {   
        kid = ki * sampleTime;
        kdd = kd / sampleTime;

        kp64 = static_cast<float64>(kp);
        ki64 = static_cast<float64>(ki);
        kd64 = static_cast<float64>(kd);
        kid64 = ki64 * static_cast<float64>(sampleTime);
        kdd64 = kd64 / static_cast<float64>(sampleTime);
    }
    if (ok) {
        float64 tmpMax, tmpMin;
        ok = data.Read("MaxOutput", tmpMax);
        if (!ok) {
            tmpMax = MAX_FLOAT64;
        }
        ok = data.Read("MinOutput", tmpMin);
        if (!ok) {
            tmpMin = -MAX_FLOAT64;
        }
        maxOutput64 = tmpMax;
        minOutput64 = tmpMin;
        maxOutput = static_cast<float32>(tmpMax);
        minOutput = static_cast<float32>(tmpMin);
        ok = true;
        if (IsEqual(maxOutput64, minOutput64) || maxOutput64 < minOutput64) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "MaxOutput must be larger than MinOutput (MaxOutput > MinOutput)");
            ok = false;
        }
    }

    return ok;
}

bool FloatPIDGAM::Setup() {
    bool ok = true;
    nOfInputSignals = GetNumberOfInputSignals();
    if (nOfInputSignals == 0u) {
        REPORT_ERROR(ErrorManagement::ParametersError, "No input signals were declared. Declare 1 input for feedforward control and 2 for feedback control (1st signal => reference | 2nd signal => measurement)");
        ok = false;
    }
    else if (nOfInputSignals == 1u) {
        enableSubstraction = false;
    }
    else if (nOfInputSignals == 2u) {
        enableSubstraction = true;
    }
    else {
        REPORT_ERROR(ErrorManagement::ParametersError, "Maximum nOfInputSignals = 2. nOfInputSignals = %u", nOfInputSignals);
        ok = false;
    }
    if (ok) {
        nOfOutputSignals = GetNumberOfOutputSignals();
        if (nOfOutputSignals != 1u) {
            REPORT_ERROR(ErrorManagement::ParametersError, "nOfOutputSignals must be 1. nOfOutputSignals = %u", nOfOutputSignals);
            ok = false;
        }
    }
    if (ok) {
        ok = GetSignalNumberOfElements(InputSignals, 0u, nOfInputElementsReference);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "Error reading nOfInputElementsReference");
        }
        if (ok) {
            if (!(nOfInputElementsReference == 1u)) {
                REPORT_ERROR(ErrorManagement::InitialisationError, "nOfInputElementsReference must be 1. nOfInputElementsReference = %u",
                             nOfInputElementsReference);
                ok = false;
            }
        }
        if (ok) {
            if (enableSubstraction) {
                //The order of the input is very important
                //First input is the reference
                ok = GetSignalNumberOfElements(InputSignals, 1u, nOfInputElementsMeasurement);
                if (!ok) {
                    REPORT_ERROR(ErrorManagement::InitialisationError, "Error reading nOfInputElementsMeasurement");
                }
                if (nOfInputElementsMeasurement != nOfInputElementsReference) {
                    REPORT_ERROR(ErrorManagement::InitialisationError, "nOfInputElementsReference is different from nOfInputElementsMeasurement. nOfInputElementsReference = %u | nOfInputElementsMeasurement = %u",
                                                                        nOfInputElementsReference, nOfInputElementsMeasurement);
                    ok = false;
                }
            }
        }
    }

    if (ok) {
        ok = GetSignalNumberOfElements(OutputSignals, 0u, nOfOutputElements);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "Error reading nOfOutputElements");
        }
        if (nOfOutputElements != nOfInputElementsReference) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "The number of output elements must be the same as the number of input elements. nOfOutputElements = %u | nOfInputElements = %u",
                                                                nOfOutputElements, nOfInputElementsReference);
            ok = false;
        }
    }

    if (ok) {
        ok = GetSignalNumberOfSamples(InputSignals, 0u, nOfInputSamplesReference);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "Error reading nOfInputSamplesReference");
        }
        if (ok) {
            ok = (nOfInputSamplesReference == 1u);
            if (!ok) {
                REPORT_ERROR(ErrorManagement::InitialisationError, "nOfInputSamplesReference must be 1. nOfInputSamplesReference = %u", nOfInputSamplesReference);
            }
        }
        if (ok) {
            if (enableSubstraction) {
                ok = GetSignalNumberOfSamples(InputSignals, 1u, nOfInputSamplesMeasurement);
                if (!ok) {
                    REPORT_ERROR(ErrorManagement::InitialisationError, "Error reading nOfInputSamplesMeasurement");
                }
                if (ok) {
                    ok = (nOfInputSamplesMeasurement == 1u);
                    if (!ok) {
                        REPORT_ERROR(ErrorManagement::InitialisationError, "nOfInputSamplesMeasurement must be 1. nOfInputSamplesMeasurement = %u",
                                     nOfInputSamplesMeasurement);
                    }
                }
            }
        }
    }
    if (ok) {
        ok = GetSignalNumberOfSamples(OutputSignals, 0u, nOfOuputSamples);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "Error reading nOfOuputSamples");
        }
        if (ok) {
            ok = (nOfOuputSamples == 1u);
            if (!ok) {
                REPORT_ERROR(ErrorManagement::InitialisationError, "nOfOuputSamples must be 1. nOfOuputSamples = %u", nOfOuputSamples);
            }
        }
    }
    if (ok) {
        ok = GetSignalNumberOfDimensions(InputSignals, 0u, inputReferenceDimension);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "Error reading inputReferenceDimension");
        }
        if (ok) {
            ok = (inputReferenceDimension == 0u);
            if (!ok) {
                REPORT_ERROR(ErrorManagement::InitialisationError, "inputReferenceDimension must be 0. inputReferenceDimension = %u",
                             inputReferenceDimension);
            }
        }
        if (ok) {
            if (enableSubstraction) {
                ok = GetSignalNumberOfDimensions(InputSignals, 1u, inputMeasurementDimension);
                if (!ok) {
                    REPORT_ERROR(ErrorManagement::InitialisationError, "Error reading inputMeasurementDimension");
                }
                if (ok) {
                    ok = (inputMeasurementDimension == 0u);
                    if (!ok) {
                        REPORT_ERROR(ErrorManagement::InitialisationError, "inputMeasurementDimension must be 0. inputMeasurementDimension = %u", inputMeasurementDimension);
                    }
                }
            }
        }
    }
    if (ok) {
        ok = GetSignalNumberOfDimensions(OutputSignals, 0u, outputDimension);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "Error reading outputDimension");
        }
        if (ok) {
            ok = (outputDimension == 0u);
            if (!ok) {
                REPORT_ERROR(ErrorManagement::InitialisationError, "outputDimension must be 0. outputDimension = %u", outputDimension);
            }
        }
    }
    if (ok) {
        referencedType = GetSignalType(InputSignals, 0u);
        ok = (referencedType == Float32Bit || referencedType == Float64Bit);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "The reference data type must be either float32 or float64.");
        }
        if (ok && enableSubstraction) {
            measurementdType = GetSignalType(InputSignals, 1u);
            ok = (measurementdType == Float32Bit || measurementdType == Float64Bit);
            if (!ok) {
                REPORT_ERROR(ErrorManagement::InitialisationError, "The measurement data type must be either float32 or float64.");
            }
            if (ok && (measurementdType != referencedType)) {
                REPORT_ERROR(ErrorManagement::InitialisationError, "Type mismatch between reference and measurement signals. reference = %s | measurement = %s",
                                                                    TypeDescriptor::GetTypeNameFromTypeDescriptor(referencedType),
                                                                    TypeDescriptor::GetTypeNameFromTypeDescriptor(measurementdType));
                ok = false;
            }
        }
    }
    if (ok) {
        outputdType = GetSignalType(OutputSignals, 0u);
        ok = (outputdType == Float32Bit || outputdType == Float64Bit);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "The data type must be either float32 or float64.");
        }
        if (ok && (outputdType != referencedType)) {
            REPORT_ERROR(ErrorManagement::InitialisationError, "Type mismatch between input(s) and output signals. input(s) = %s | output = %s",
                                                                TypeDescriptor::GetTypeNameFromTypeDescriptor(referencedType),
                                                                TypeDescriptor::GetTypeNameFromTypeDescriptor(outputdType));
            ok = false;
        }
    }

    if (ok) {
        if (outputdType == Float32Bit) {
            reference = static_cast<float32 *>(GetInputSignalMemory(0u));
            if (enableSubstraction) {
                measurement = static_cast<float32 *>(GetInputSignalMemory(1u));
            }
            output = static_cast<float32 *>(GetOutputSignalMemory(0u));
            REPORT_ERROR(ErrorManagement::Information, "Signals static_cast to float32 OK!");
        }
        else { // Float64Bit
            reference64 = static_cast<float64 *>(GetInputSignalMemory(0u));
            if (enableSubstraction) {
                measurement64 = static_cast<float64 *>(GetInputSignalMemory(1u));
            }
            output64 = static_cast<float64 *>(GetOutputSignalMemory(0u));
            REPORT_ERROR(ErrorManagement::Information, "Signals static_cast to float64 OK!");
        }
    }

    return ok;
}

bool FloatPIDGAM::Execute() {
    GetValue();
    Saturation();
    return true;
}

//lint -e{613} The Setup() function guarantee that the pointers are not NULL.
void FloatPIDGAM::GetValue() {
    if (outputdType == Float32Bit) {
        float32 error;
        if (enableSubstraction) {
            error = *reference - *measurement;
        } else {
            error = *reference;
        }
        proportional = kp * error;
        if (enableIntegral) {
            integral = error * kid + lastIntegral;
        } else {
            integral = error * kid;
        }
        derivative = (error - lastInput) * kdd;
        lastInput = error;
        output[0] = proportional + integral + derivative;
        lastIntegral = integral;
    } else { // Float64Bit
        float64 error;
        if (enableSubstraction) {
            error = *reference64 - *measurement64;
        } else {
            error = *reference64;
        }
        float64 proportional64 = kp64 * error;
        float64 integral64;
        if (enableIntegral) {
            integral64 = error * kid64 + lastIntegral64;
        } else {
            integral64 = error * kid64;
        }
        float64 derivative64 = (error - lastInput64) * kdd64;
        lastInput64 = error;
        output64[0] = proportional64 + integral64 + derivative64;
        lastIntegral64 = integral64;
    }
}

//lint -e{613} The Setup() function guarantee that the pointers are not NULL.
void FloatPIDGAM::Saturation() {
    if (outputdType == Float32Bit) {
        if (output[0] > maxOutput) {
            output[0] = maxOutput;
            enableIntegral = false;
        }
        else if (output[0] < minOutput) {
            output[0] = minOutput;
            enableIntegral = false;
        }
        else {
            enableIntegral = true;
        }
    } else { // Float64Bit
        if (output64[0] > maxOutput64) {
            output64[0] = maxOutput64;
            enableIntegral = false;
        }
        else if (output64[0] < minOutput64) {
            output64[0] = minOutput64;
            enableIntegral = false;
        }
        else {
            enableIntegral = true;
        }
    }
}

bool FloatPIDGAM::ExportData(MARTe::StructuredDataI & data) {
    using namespace MARTe;
    bool ok = GAM::ExportData(data);
    if (ok) {
        if (outputdType == Float32Bit) {
            if (ok) {
                ok = data.Write("Kp", kp);
            }
            if (ok) {
                ok = data.Write("Ki", ki);
            }
            if (ok) {
                ok = data.Write("Kd", kd);
            }
            if (ok) {
                ok = data.Write("SampleTime", sampleTime);
            }
            if (ok) {
                ok = data.Write("MaxOutput", maxOutput);
            }
            if (ok) {
                ok = data.Write("MinOutput", minOutput);
            }
        }
        else { // Float64Bit
            if (ok) {
                ok = data.Write("Kp", kp64);
            }
            if (ok) {
                ok = data.Write("Ki", ki64);
            }
            if (ok) {
                ok = data.Write("Kd", kd64);
            }
            if (ok) {
                ok = data.Write("SampleTime", sampleTime);
            }
            if (ok) {
                ok = data.Write("MaxOutput", maxOutput64);
            }
            if (ok) {
                ok = data.Write("MinOutput", minOutput64);
            }
        }
    }
    return ok;
}

CLASS_REGISTER(FloatPIDGAM, "1.0")
}
