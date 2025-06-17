/**
 * @file MagneticRZPosGAM.cpp
 * @brief Source file for class MagneticRZPosGAM
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
 * the class MagneticRZPosGAM (public, protected, and private). Be aware that some 
 * methods, such as those inline could be defined on the header file, instead.
 */

/*---------------------------------------------------------------------------*/
/*                         Standard header includes                          */
/*---------------------------------------------------------------------------*/

/*---------------------------------------------------------------------------*/
/*                         Project header includes                           */
/*---------------------------------------------------------------------------*/
#include "AdvancedErrorManagement.h"
#include "CLASSMETHODREGISTER.h"

#include "MagneticRZPosGAM.h"
// #include "RegisteredMethodsMessageFilter.h"

/*---------------------------------------------------------------------------*/
/*                           Static definitions                              */
/*---------------------------------------------------------------------------*/

//namespace MARTeIsttok {
namespace MARTe {
/**
 * The number of signals and definition of PI
 */
    const  uint32 EP_NUM_INPUTS  = 12u;
    const  uint32 EP_NUM_OUTPUTS = 3u;
    const float32 PI = 3.1415927;

/*---------------------------------------------------------------------------*/
/*                           Method definitions                              */
/*---------------------------------------------------------------------------*/
//namespace MARTeIsttok {
    /*
    MagneticRZPosGAM::MagneticRZPosGAM() : 
                GAM(),
                MessageI() // Should the method be registered as a messageable function?
                {
    */
    MagneticRZPosGAM::MagneticRZPosGAM() : 
                GAM() {
        /*
        gain = 0u; // necessary?
        numberOfSamplesAvg = 1u; // necessary?
        */
        numberOfInputElements = 0u; // necessary?
        

        //--------------Inputs----------------
        //for (k=0u; k<EP_NUM_INPUTS-1; k++) {
        //    inputMirnov[k] = NULL_PTR(MARTe::float32 *);
        //}
        inputMirnov0    = NULL_PTR(MARTe::float32 *);
        inputMirnov1  = NULL_PTR(MARTe::float32 *);
        inputMirnov2  = NULL_PTR(MARTe::float32 *);
        inputMirnov3 = NULL_PTR(MARTe::float32 *);
        inputMirnov4    = NULL_PTR(MARTe::float32 *);
        inputMirnov5  = NULL_PTR(MARTe::float32 *);
        inputMirnov6  = NULL_PTR(MARTe::float32 *);
        inputMirnov7 = NULL_PTR(MARTe::float32 *);
        inputMirnov8    = NULL_PTR(MARTe::float32 *);
        inputMirnov9  = NULL_PTR(MARTe::float32 *);
        inputMirnov10  = NULL_PTR(MARTe::float32 *);
        inputMirnov11 = NULL_PTR(MARTe::float32 *);
        //--------------------------------------
        
        // triggerSdas = NULL_PTR(MARTe::uint32 *); // necessary?

        /*
        inputSignal = NULL; // NULL_PTR(MARTe::float32*); // necessary?
        */

        //--------------Outputs----------------
        outputMpIp = NULL_PTR(MARTe::float32 *);
        outputMpR = NULL_PTR(MARTe::float32 *);
        outputMpZ = NULL_PTR(MARTe::float32 *);
        //--------------------------------------
        
        /*
        outputSignals = NULL_PTR(MARTe::float32 **);
        */
       
    }

    MagneticRZPosGAM::~MagneticRZPosGAM() {                         // |
        
        /* -------- Signal Declaration --------------------------------
        inputSignal =  NULL; //NULL_PTR(MARTe::float32*);           // | } -> necessary?
        */

        inputMirnov0    = NULL_PTR(MARTe::float32 *);
        inputMirnov1  = NULL_PTR(MARTe::float32 *);
        inputMirnov2  = NULL_PTR(MARTe::float32 *);
        inputMirnov3 = NULL_PTR(MARTe::float32 *);
        inputMirnov4    = NULL_PTR(MARTe::float32 *);
        inputMirnov5  = NULL_PTR(MARTe::float32 *);
        inputMirnov6  = NULL_PTR(MARTe::float32 *);
        inputMirnov7 = NULL_PTR(MARTe::float32 *);
        inputMirnov8    = NULL_PTR(MARTe::float32 *);
        inputMirnov9  = NULL_PTR(MARTe::float32 *);
        inputMirnov10  = NULL_PTR(MARTe::float32 *);
        inputMirnov11 = NULL_PTR(MARTe::float32 *);

        outputMpIp = NULL_PTR(MARTe::float32 *);
        outputMpR = NULL_PTR(MARTe::float32 *);
        outputMpZ = NULL_PTR(MARTe::float32 *);

    }                                                               // |

    bool MagneticRZPosGAM::Initialise(MARTe::StructuredDataI & data) {
        using namespace MARTe;
        bool ok = GAM::Initialise(data);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "Could not Initialise the GAM");
        }
        return ok;
    }

    bool MagneticRZPosGAM::Setup() {
        using namespace MARTe;

        /* *************************************************** */
        //-------------------InputSignals-----------------------
        uint32 numberOfInputSignals = GetNumberOfInputSignals();
        bool ok = (numberOfInputSignals == 12u);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The number of input signals shall be equal to 12. numberOfInputSignals = %d ", numberOfInputSignals);
        }
        if (ok) {
            StreamString inputSignalName;
            ok = GetSignalName(InputSignals, 0u, inputSignalName);
            TypeDescriptor inputSignalType = GetSignalType(InputSignals, 0u);
            ok = (inputSignalType == Float32Bit); 
            if (!ok) {
                const char8 * const inputSignalTypeStr = TypeDescriptor::GetTypeNameFromTypeDescriptor(inputSignalType);
                REPORT_ERROR(ErrorManagement::ParametersError,
                        "The type of the input signals shall be float32. inputSignalType = %s", inputSignalTypeStr);
            }
            uint32 numberOfInputSamples = 0u;
            if (ok) {
                ok = GetSignalNumberOfSamples(InputSignals, 0u, numberOfInputSamples);
            }

            if (ok) {
                ok = (numberOfInputSamples == 1u);
            }
            if (!ok) {
                REPORT_ERROR(ErrorManagement::ParametersError,
                        "The number of input signals samples shall be equal to 1. numberOfInputSamples = %d", numberOfInputSamples);
            }
            uint32 numberOfInputDimensions = 0u;
            if (ok) {
                ok = GetSignalNumberOfDimensions(InputSignals, 0u, numberOfInputDimensions);
            }

            if (ok) {
                ok = (numberOfInputDimensions == 0u);
                if (!ok) {
                    REPORT_ERROR(
                            ErrorManagement::ParametersError,
                            "The number of input signals dimensions shall be equal to 0. numberOfInputDimensions(%s) = %d", inputSignalName.Buffer(), numberOfInputDimensions);
                }
            }
            if (ok) {
                ok = GetSignalNumberOfElements(InputSignals, 0u, numberOfInputElements);
            }
            if (ok) {
                ok = (numberOfInputElements == 1u);
            }
            if (!ok) {
                REPORT_ERROR(ErrorManagement::ParametersError,
                        "The number of input signal elements shall be equal to 1. numberOfInputElements(%s) = %d", inputSignalName.Buffer(), numberOfInputElements);
            }
            ok = GetSignalName(InputSignals, 1u, inputSignalName);
            inputSignalType = GetSignalType(InputSignals, 1u);
            ok = (inputSignalType == Float32Bit);
            if (!ok) {
                const char8 * const inputSignalTypeStr = TypeDescriptor::GetTypeNameFromTypeDescriptor(inputSignalType);
                REPORT_ERROR(ErrorManagement::ParametersError,
                        "The type of the input signals shall be float32. inputSignalType = %s", inputSignalTypeStr);
            }
            numberOfInputSamples = 0u;
            if (ok) {
                ok = GetSignalNumberOfSamples(InputSignals, 1u, numberOfInputSamples);
            }

            if (ok) {
                ok = (numberOfInputSamples == 1u);
            }
            if (!ok) {
                REPORT_ERROR(ErrorManagement::ParametersError,
                        "The number of input signals samples shall be equal to 1. numberOfInputSamples = %d", numberOfInputSamples);
            }
            numberOfInputDimensions = 0u;
            if (ok) {
                ok = GetSignalNumberOfDimensions(InputSignals, 1u, numberOfInputDimensions);
            }

            if (ok) {
                ok = (numberOfInputDimensions == 0u);
                if (!ok) {
                    REPORT_ERROR(
                            ErrorManagement::ParametersError,
                            "The number of input signals dimensions shall be equal to 0. numberOfInputDimensions(%s) = %d", inputSignalName.Buffer(), numberOfInputDimensions);
                }
            }
            if (ok) {
                ok = GetSignalNumberOfElements(InputSignals, 1u, numberOfInputElements);
            }
            if (ok) {
                ok = (numberOfInputElements == 1u);
            }
            if (!ok) {
                REPORT_ERROR(ErrorManagement::ParametersError,
                        "The number of input signal elements shall be equal to 1. numberOfInputElements(%s) = %d", inputSignalName.Buffer(), numberOfInputElements);
            }


        }

        if (ok) {
            /*
            inputSignal   = reinterpret_cast<float32 *>(GetInputSignalMemory(xu));
            */

           /*---------------------------------------------------------------------------*/
           /*      DEFINE WHICH MIRNOV INPUTS CORRELATE TO Corona, 2021 FIG. 4.16A      */
           /*---------------------------------------------------------------------------*/
            
           //for (k=0u; k<EP_NUM_INPUTS-1; k++) {
            //    inputMirnov[k] = reinterpret_cast<float32 *>(GetInputSignalMemory(k));
            //}
            inputMirnov0    = reinterpret_cast<float32 *>(GetInputSignalMemory(0u));
            inputMirnov1  = reinterpret_cast<float32 *>(GetInputSignalMemory(1u));
            inputMirnov2  = reinterpret_cast<float32 *>(GetInputSignalMemory(2u));
            inputMirnov3 = reinterpret_cast<float32 *>(GetInputSignalMemory(3u));
            inputMirnov4    = reinterpret_cast<float32 *>(GetInputSignalMemory(4u));
            inputMirnov5  = reinterpret_cast<float32 *>(GetInputSignalMemory(5u));
            inputMirnov6  = reinterpret_cast<float32 *>(GetInputSignalMemory(6u));
            inputMirnov7 = reinterpret_cast<float32 *>(GetInputSignalMemory(7u));
            inputMirnov8    = reinterpret_cast<float32 *>(GetInputSignalMemory(8u));
            inputMirnov9  = reinterpret_cast<float32 *>(GetInputSignalMemory(9u));
            inputMirnov10  = reinterpret_cast<float32 *>(GetInputSignalMemory(10u));
            inputMirnov11 = reinterpret_cast<float32 *>(GetInputSignalMemory(11u));
            

            // triggerSdas = reinterpret_cast<uint32 *>(GetInputSignalMemory(12u)); // necessary?

            REPORT_ERROR(ErrorManagement::Information, "InputSignals reinterpret_cast OK!");
        }

        /* *************************************************** */
        //-------------------OutputSignals-----------------------
        uint32 numberOfOutputSignals = GetNumberOfOutputSignals();
        ok = (numberOfOutputSignals == 3u);
        if (!ok) {
            REPORT_ERROR(ErrorManagement::ParametersError, "The number of output signals shall be equal to 3. numberOfOutputSignals = %d ", numberOfOutputSignals);
        }
        if (ok) {
            uint32 n;
            for (n = 0u; (n < numberOfOutputSignals) && (ok); n++) {
                StreamString outputSignalName;
                ok = GetSignalName(OutputSignals, n, outputSignalName);
                TypeDescriptor outputSignalType = GetSignalType(OutputSignals, n);
                ok = (outputSignalType == Float32Bit);
                if (!ok) {
                    const char8 * const outputSignalTypeStr = TypeDescriptor::GetTypeNameFromTypeDescriptor(outputSignalType);
                    REPORT_ERROR(ErrorManagement::ParametersError,
                            "The type of the output signals shall be float32. outputSignalType = %s", outputSignalTypeStr);
                }
                uint32 numberOfOutputSamples = 0u;
                if (ok) {
                    ok = GetSignalNumberOfSamples(OutputSignals, n, numberOfOutputSamples);
                }

                if (ok) {
                    ok = (numberOfOutputSamples == 1u);
                }
                if (!ok) {
                    REPORT_ERROR(ErrorManagement::ParametersError,
                            "The number of output signals samples shall be equal to 1. numberOfOutputSamples = %d", numberOfOutputSamples);
                }
                uint32 numberOfOutputDimensions = 0u;
                if (ok) {
                    ok = GetSignalNumberOfDimensions(OutputSignals, n, numberOfOutputDimensions);
                }

                if (ok) {
                    ok = (numberOfOutputDimensions == 0u);
                    if (!ok) {
                        REPORT_ERROR(ErrorManagement::ParametersError,
                                "The number of output signals dimensions shall be equal to 0.  numberOfOutputDimensions (%s) = %d", outputSignalName.Buffer(), numberOfOutputDimensions);
                    }
                }
                uint32 numberOfOutputElements = 0u;
                if (ok) {
                    ok = GetSignalNumberOfElements(OutputSignals, n, numberOfOutputElements);
                }
                if (ok) {
                    ok = (numberOfOutputElements == 1u);
                }
                if (!ok) {
                    REPORT_ERROR(ErrorManagement::ParametersError,
                                 "The number of output signals elements shall be equal to 1. (%s) numberOfOutputElements = %d", outputSignalName.Buffer(), numberOfOutputElements);
                }
                
                if (ok) {
                    outputMpIp = reinterpret_cast<float32 *>(GetOutputSignalMemory(0u));
                    outputMpR = reinterpret_cast<float32 *>(GetOutputSignalMemory(1u));
                    outputMpZ = reinterpret_cast<float32 *>(GetOutputSignalMemory(2u));

                    REPORT_ERROR(ErrorManagement::Information, "OutputSignals reinterpret_cast OK!");
                }
            }

            if (ok){
                    ok = (inputMirnov0 != NULL_PTR(float32 *)) &&
                    (inputMirnov1 != NULL_PTR(float32 *)) &&
                    (inputMirnov2 != NULL_PTR(float32 *)) &&
                    (inputMirnov3 != NULL_PTR(float32 *)) &&
                    (inputMirnov4 != NULL_PTR(float32 *)) &&
                    (inputMirnov5 != NULL_PTR(float32 *)) &&
                    (inputMirnov6 != NULL_PTR(float32 *)) &&
                    (inputMirnov7 != NULL_PTR(float32 *)) &&
                    (inputMirnov8 != NULL_PTR(float32 *)) &&
                    (inputMirnov9 != NULL_PTR(float32 *)) &&
                    (inputMirnov10 != NULL_PTR(float32 *)) &&
                    (inputMirnov11 != NULL_PTR(float32 *)) &&
                    (outputMpIp != NULL_PTR(float32 *)) &&
                    (outputMpR != NULL_PTR(float32 *)) &&
                    (outputMpZ != NULL_PTR(float32 *));
            }
            if (!ok)
            {
                REPORT_ERROR(ErrorManagement::FatalError, "One or more signal memory pointers are NULL.");
                ok = false;
            }
            
            return ok;

        }
        return ok;
    }
    bool MagneticRZPosGAM::Execute() {

        float32 sumMirnov = 0.0f;

        MARTe::float32* inputMirnovArray[12] = {
            inputMirnov0, inputMirnov1, inputMirnov2, inputMirnov3,
            inputMirnov4, inputMirnov5, inputMirnov6, inputMirnov7,
            inputMirnov8, inputMirnov9, inputMirnov10, inputMirnov11
        };

        for (MARTe::uint32 i = 0u; i <= numberOfInputElements; i++){ // Sums all Mirnov coils measurements
            sumMirnov += *inputMirnovArray[i];
        }

        *outputMpIp = sumMirnov;

        const float32 mirnovRadius = 0.093f; // [m]
        const float32 mu0 = 4.0f * PI * 1.0e-7f; // Permeability of vacuum [H/m]

        // Single Current Filament Plasma Model
        *outputMpIp *= ((2.0f * PI * mirnovRadius) / 12.0f) * (1.0f / mu0);  // TO DO: confirm Mirnov probe radius (9.3cm according to Valcárcel, 2006 - Fast Feedback Control for Plasma Positioning With a PCI Hybrid DSP/FPGA Board);
                                                                     // confirm mu0 value (4.0*PI*1E-7 H/m)

        // Additional safety check for extremely small Ip
        const float32 ipThreshold = 500.0f; // minIp = 500.0 A
        if (fabsf(*outputMpIp) < ipThreshold) {
            REPORT_ERROR(ErrorManagement::Warning, "Plasma current is under threshold; magnetic reconstruction is inoperative: outputMpIp = %f", *outputMpIp);
            // Use Rogowski coil values for Ip (?)
            *outputMpR = 0.0f;
            *outputMpZ = 0.0f;
        }
        else {
            // Placeholder for R and Z calculations (to be implemented)
            *outputMpR = 0.0f;
            *outputMpZ = 0.0f;
    }


        /*
        R_0 = 0.46 m - major radius
        
        --/ Define Mirnov probes radii according to Corona, 2021 Fig. 4.16A /--
        // r_probe = 93 mm from the vacuum chamber's center
        R_1 = R_12 = (R_1&12) = ?
        R_2 = R_11 = (R_2&11) = ?
        R_3 = R_10 = (R_3&10) = ?
        R_4 = R_9 = (R_4&9) = ?
        R_5 = R_8 = (R_5&8) = ?
        R_6 = R_7 = (R_6&7) = ?
        -----------------------------------------------------------------------

        */
        /* For example 

        *outputMpR += inputSignal[1u]*(R_1&12 - 0.46);
        *outputMpR += inputSignal[13u]*(R_1&12 - 0.46);
        .
        .
        .
        *outputMpR *= (2.0 * PI* 0.055)/12.0;
        *outputMpR *= 1.0/ *outputMpIp;  
        
        This calculation will introduce errors during AC operation, consider defining either a
        'default value' for *outputMpR or use 'previous *outputMpR' if «abs(*outputMpIp) < threshold_Ip»
         
        */
        
        /*
        z_0 = 0.0 m - nominal vertical position
        
        --/ Define Mirnov probes radii according to Corona, 2021 Fig. 4.16A /--
        z_1 = z_6 = (z_1&6) = ?
        z_2 = z_5 = (z_2&15) = ?
        z_3 = z_4 = (z_3&4) = ?
        z_7 = z_12 = (z_7&12) = ?
        z_8 = z_11 = (z_8&11) = ?
        z_9 = z_10 = (z_9&10) = ?
        -----------------------------------------------------------------------

        */
        /* For example 

        *outputMpZ += inputSignal[1u]*(z_1&6 - 0.0);
        *outputMpZ += inputSignal[6u]*(z_1&6 - 0.0);
        .
        .
        .
        *outputMpZ *= (2.0 * PI* 0.055)/12.0;
        *outputMpZ *= 1.0/ *outputMpIp; 
        This calculation will introduce errors during AC operation, consider defining either a
        'default value' for *outputMpZ or use 'previous *outputMpZ' if «abs(*outputMpIp) < threshold_Ip» 
        */
        
        /*
        =  inputSignal[0] - inputOffset[0];
        */

        /*
        *outputMpZ =  inputSignal[0] - inputSignal[3];
        */
    
        return true;
    }


    bool MagneticRZPosGAM::ExportData(MARTe::StructuredDataI & data) {
        using namespace MARTe;
        bool ok = GAM::ExportData(data);
        if (ok) {
            ok = data.CreateRelative("Parameters");
        }
        if (ok) {
            ok = data.MoveToAncestor(1u);
        }
        return ok;
    }

    CLASS_REGISTER(MagneticRZPosGAM, "0.1")

    // CLASS_METHOD_REGISTER(MagneticRZPosGAM)

} /* namespace MARTeIsttok */

//  vim: syntax=cpp ts=4 sw=4 sts=4 sr et
