/**
 * @file MagneticArrayADCConversionGAM.cpp
 * @brief Source file for class MagneticArrayADCConversionGAM
 * @date 19/07/2025
 * @author Felipe Tassari Aveiro
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
 * the class MagneticArrayADCConversionGAM (public, protected, and private). Be aware that some 
 * methods, such as those inline could be defined on the header file, instead.
 * 
 * @note Compilation command:
 * 
 * $ make -C GAMs/MagneticArrayADCConversionGAM -f Makefile.gcc
 */

/*---------------------------------------------------------------------------*/
/*                         Standard header includes                          */
/*---------------------------------------------------------------------------*/

#include <math.h>

/*---------------------------------------------------------------------------*/
/*                         Project header includes                           */
/*---------------------------------------------------------------------------*/

#include "AdvancedErrorManagement.h"
#include "FastMath.h"
#include "MagneticArrayADCConversionGAM.h"

/*---------------------------------------------------------------------------*/
/*                           Static definitions                              */
/*---------------------------------------------------------------------------*/

/*---------------------------------------------------------------------------*/
/*                           Method definitions                              */
/*---------------------------------------------------------------------------*/
namespace MARTe {
    /**
     * The number of signals
     */
    const MARTe::uint32 NUM_SIGNALS  = 12u;
    const MARTe::uint32 INPUT_ELEMENTS = 16u;
    const MARTe::float64 CLOCK_FREQ = 10000.0;
    const MARTe::float64 RT_DECIM = 200.0;
    const MARTe::float64 faradaySign = -1.0;
    const MARTe::float64 correctionCte =
        faradaySign / (CLOCK_FREQ * RT_DECIM);

MagneticArrayADCConversionGAM::MagneticArrayADCConversionGAM() {
    // Initialization
    // GAM Inputs
    // GAM Outputs
    inputSignal = NULL_PTR(MARTe::float32 *);
    for (MARTe::uint32 i = 0u; i < NUM_SIGNALS; i++) {
        outputSignals[i] = NULL_PTR(MARTe::float32 *);
    }
}

MagneticArrayADCConversionGAM::~MagneticArrayADCConversionGAM() {
    inputSignal = NULL_PTR(MARTe::float32 *);
    for (MARTe::uint32 i = 0u; i < NUM_SIGNALS; i++) {
        outputSignals[i] = NULL_PTR(MARTe::float32 *);
    }
}

bool MagneticArrayADCConversionGAM::Initialise(MARTe::StructuredDataI & data) {
    using namespace MARTe;
    bool ok = GAM::Initialise(data);
    if (!ok) {
        REPORT_ERROR(ErrorManagement::ParametersError, "Could not Initialise the GAM");
    }
    if (ok) {
        static const float64 defaultEffArea[NUM_SIGNALS] = {
            2.793e-3, 2.814e-3, 2.839e-3, 2.635e-3,
            2.579e-3, 2.202e-3, 2.183e-3, 2.218e-3,
            2.305e-3, 1.686e-3, 2.705e-3, 2.442e-3
        };
        static const float64 defaultPol[NUM_SIGNALS] = {
            -1.0, -1.0, 1.0, -1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, -1.0, 1.0
        };
        static const float64 defaultGain[NUM_SIGNALS] = {
            17.3887e-6, 17.3938e-6, 17.4276e-6, 17.4994e-6,
            17.3827e-6, 17.4440e-6, 17.4532e-6, 17.3724e-6,
            17.1925e-6, 17.2739e-6, 17.3810e-6, 17.4413e-6
        };

        MARTe::StreamString coilNode;
            
        for (MARTe::uint32 i = 0u; i < NUM_SIGNALS; i++) {

            coilNode.Printf("Coil%d", i + 1u);

            ok = data.MoveRelative(coilNode.Buffer());

            if (ok) {
                ok = data.Read("EffArea", EffArea[i]);
                if (!ok || EffArea[i] <= 0.0) {
                    REPORT_ERROR(ErrorManagement::Warning,
                        "Invalid or missing EffArea for Coil%d. Using default %.4e", i + 1u, defaultEffArea[i]);
                    EffArea[i] = defaultEffArea[i];
                }

                ok = data.Read("Pol", Pol[i]);
                if (!ok || (Pol[i] != -1.0 && Pol[i] != 1.0)) {
                    REPORT_ERROR(ErrorManagement::Warning,
                        "Invalid or missing Pol for Coil%d. Using default %.1f", i + 1u, defaultPol[i]);
                    Pol[i] = defaultPol[i];
                }

                ok = data.Read("Gain", Gain[i]);
                if (!ok || Gain[i] <= 0.0) {
                    REPORT_ERROR(ErrorManagement::Warning,
                        "Invalid or missing Gain for Coil%d. Using default %.6e", i + 1u, defaultGain[i]);
                    Gain[i] = defaultGain[i];
                }

                REPORT_ERROR(ErrorManagement::Information,
                    "Coil%d parameters set: EffArea=%.4e, Pol=%.1f, Gain=%.6e",
                    i + 1u, EffArea[i], Pol[i], Gain[i]);

                data.MoveToAncestor(1u);
            }
            else {
                EffArea[i] = defaultEffArea[i];
                Pol[i] = defaultPol[i];
                Gain[i] = defaultGain[i];

                REPORT_ERROR(ErrorManagement::Warning,
                    "Coil%d parameters node not found. Using default values: EffArea=%.4e, Pol=%.1f, Gain=%.6e",
                    i + 1u, EffArea[i], Pol[i], Gain[i]);
                ok = true;
            }
        }
    }
    if (ok) {
        for (MARTe::uint32 i = 0u; i < NUM_SIGNALS; i++) {
            MARTe::float64 factor = (Gain[i] * Pol[i] / EffArea[i]) * correctionCte;
            MagFieldConv[i] = static_cast<MARTe::float32>(factor);
        }
    }
    
    return ok;
}

bool MagneticArrayADCConversionGAM::Setup() {
    using namespace MARTe;
    uint32 numberOfInputSignals = GetNumberOfInputSignals();
    uint32 numberOfOutputSignals = GetNumberOfOutputSignals();
    bool ok = (numberOfInputSignals == 1u);
    if (!ok) {
        REPORT_ERROR(ErrorManagement::ParametersError,
                "The number of input signals shall be equal to 1. numberOfInputSignals = %d ", numberOfInputSignals);
    }
    if (ok) {
        ok = (numberOfOutputSignals == NUM_SIGNALS); // if ok numberOfOutputSignals == 12u
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError,
                         "The number of output signals shall be equal to %d. numberOfOutputSignals = %d",
                         NUM_SIGNALS, numberOfOutputSignals);
        }
    }
    if (ok) {
        MARTe::StreamString inputName;
        MARTe::StreamString outputName;
        TypeDescriptor inputType;
        TypeDescriptor outputType;
        uint32 numberOfInputSamples = 0u;
        uint32 numberOfInputElements = 0u;
        uint32 numberOfInputDimensions = 0u;
        uint32 numberOfOutputSamples = 0u;
        uint32 numberOfOutputElements = 0u;
        uint32 numberOfOutputDimensions = 0u;

        GetSignalName(InputSignals, 0u, inputName);

        inputType = GetSignalType(InputSignals, 0u);

        ok = (inputType == Float32Bit);

        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError,
                        "The %s input signal type shall be float32. inputSignalType = %s",
                        inputName,
                        TypeDescriptor::GetTypeNameFromTypeDescriptor(inputType));
            return ok;
        }

        if (ok) {
            inputSignal = reinterpret_cast<MARTe::float32 *>(GetInputSignalMemory(0u));
            REPORT_ERROR(ErrorManagement::Information, "Input signal %s reinterpret_cast OK",
                        inputName);
        }

        if (ok) {
            ok = GetSignalNumberOfSamples(InputSignals, 0u, numberOfInputSamples);
            if (ok) {
                ok = (numberOfInputSamples == 1u);
            }
            if (!ok) {
                REPORT_ERROR(ErrorManagement::ParametersError,
                            "The number of input signals samples shall be equal to 1. numberOfInputSamples = %d",
                            numberOfInputSamples);
                return ok;
            }
        }

        if (ok) {
            ok = GetSignalNumberOfElements(InputSignals, 0u, numberOfInputElements);
            if (ok) {
                ok = (numberOfInputElements == INPUT_ELEMENTS);
            }
            if (!ok) {
                    REPORT_ERROR(ErrorManagement::ParametersError,
                            "The number of input signal elements shall be equal to %d. numberOfInputElements = %d",
                            INPUT_ELEMENTS, numberOfInputElements);
                return ok;
            }
        }

        if (ok) {
                ok = GetSignalNumberOfDimensions(InputSignals, 0u, numberOfInputDimensions);
                if (ok) {
                    ok = (numberOfInputDimensions == 1u);
                }
                if (!ok) {
                    REPORT_ERROR(ErrorManagement::ParametersError,
                                "The number of input signals dimensions shall be equal to 1. numberOfInputDimensions = %d",
                                numberOfInputDimensions);
                    return ok;
                }
            }

        if (ok) {
            for (MARTe::uint32 i = 0u; i < NUM_SIGNALS; i++) {
                outputName = "";

                GetSignalName(OutputSignals, i, outputName);

                outputType = GetSignalType(OutputSignals, i);

                ok = (outputType == Float32Bit);

                if (!ok) {
                    REPORT_ERROR(ErrorManagement::ParametersError,
                                "The %s output signal type shall be float32. inputSignalType = %s",
                                outputName.Buffer(),
                                TypeDescriptor::GetTypeNameFromTypeDescriptor(outputType));
                    return ok;
                }
                

                if (ok) {
                    outputSignals[i] = reinterpret_cast<MARTe::float32 *>(GetOutputSignalMemory(i));
                    REPORT_ERROR(ErrorManagement::Information, "Output signal %s reinterpret_cast OK",
                                outputName.Buffer());
                }


                if (ok) {
                    ok = GetSignalNumberOfSamples(OutputSignals, i, numberOfOutputSamples);
                    if (ok) {
                        ok = (numberOfOutputSamples == 1u);
                    }
                    if (!ok) {
                        REPORT_ERROR(ErrorManagement::ParametersError,
                                    "The number of output signals samples shall be equal to 1. numberOfOutputSamples = %d",
                                    numberOfOutputSamples);
                        return ok;
                    }
                }
                
                if (ok) {
                    ok = GetSignalNumberOfElements(OutputSignals, i, numberOfOutputElements);
                    if (ok) {
                        ok = (numberOfOutputElements == 1u);
                    }
                    if (!ok) {
                        REPORT_ERROR(ErrorManagement::ParametersError,
                                    "The number of output signals elements shall be equal to 1. numberOfOutputElements = %d",
                                    numberOfOutputElements);
                        return ok;
                    }
                }

                if (ok) {
                    ok = GetSignalNumberOfDimensions(OutputSignals, i, numberOfOutputDimensions);
                    if (ok) {
                        ok = (numberOfOutputDimensions == 0u);
                    }
                    if (!ok) {
                        REPORT_ERROR(ErrorManagement::ParametersError,
                                    "The number of output signals dimensions shall be equal to 0. numberOfOutputDimensions = %d",
                                    numberOfOutputDimensions);
                        return ok;
                    }
                }
            }
        }
    }

    return ok;

}

bool MagneticArrayADCConversionGAM::Execute() {
    for (MARTe::uint32 i = 0u; i < NUM_SIGNALS; i++) {
        *outputSignals[i] = inputSignal[i] * MagFieldConv[i];
    }
    return true;
}

bool MagneticArrayADCConversionGAM::ExportData(MARTe::StructuredDataI & data) {
    using namespace MARTe;
    bool ok = GAM::ExportData(data);
    if (ok) {
        MARTe::StreamString coilNode;
        for (MARTe::uint32 i = 0u; (i < NUM_SIGNALS) && ok; i++) {
            coilNode.Printf("Coil%d", i + 1u);
            ok = data.CreateRelative(coilNode.Buffer());
            if (ok) {
                ok = data.Write("EffArea", EffArea[i]);
            }
            if (ok) {
                ok = data.Write("Pol", Pol[i]);
            }
            if (ok) {
                ok = data.Write("Gain", Gain[i]);
            }
            if (ok) {
                ok = data.MoveToAncestor(1u);
            }
        }
    }
    if (ok) {
        ok = data.MoveToAncestor(1u);
    }
    return ok;
}

CLASS_REGISTER(MagneticArrayADCConversionGAM, "")
}
