/**
 * @file FloatPIDGAM.h
 * @brief Header file for class FloatPIDGAM
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

 * @details This header file contains the declaration of the class FloatPIDGAM
 * with all of its public, protected and private members. It may also include
 * definitions for inline methods which need to be visible to the compiler.
 * 
 * @note Compilation command:
 * 
 * $ make -C GAMs/FloatPIDGAM -f Makefile.gcc
 */

#ifndef FLOATPIDGAM_H_
#define FLOATPIDGAM_H_

/*---------------------------------------------------------------------------*/
/*                        Standard header includes                           */
/*---------------------------------------------------------------------------*/

/*---------------------------------------------------------------------------*/
/*                        Project header includes                            */
/*---------------------------------------------------------------------------*/

#include "GAM.h"

/*---------------------------------------------------------------------------*/
/*                           Class declaration                               */
/*---------------------------------------------------------------------------*/

namespace MARTe {
/**
 * @brief A GAM that implements a generic PID with saturation and anti-windup
 * @details This GAM has two variants: single input or two inputs.
 * When a single input is defined, the input of the GAM should be either the error signal, computed subtracting
 * the feedback (also called measurement) from the reference signal, or the reference signal for feedforward control.
 * The PID transfer function in the Z domain using the backward Euler discretization method is:
 *
 * G_{PID} =  Kp + SampleTime *  Ki * z/(z - 1) + Kd/(SampleTime * (z-1)/z)
 * 
 * where:
 *  Kp is the proportional constant
 *  Ki is the integral constant
 *  Kd is the derivative term
 *  SampleTime is the time between samples
 * Hence, the differential equation is:
 * 
 * output = kp * error + ki * sampleTime * error + lastIntegral + kd/sampleTime * (error - lastError)
 * 
 * When two inputs are defined the behaviour is very similar to when the error signal is the sole input. But before applying the PID, the GAM computes the error from the two inputs.
 * <<The order of the inputs is very important for the correct functioning>>. The first input must be the reference and the second the measurement
 * (or feedback). See below the configuration syntax for the proper input definition.
 *
 * The GAM also provides a saturation output and anti-windup function.
 * When the output is saturated a flag is set to prevent the integral term from accumulating the error.
 * In saturation mode the output is computed as follows:
 *
 * output = Kp * error + Ki * SampleTime * error + Kd/SampleTime * (error - lastError)
 * 
 * [!] Notice that the lastIntegral is not added to the output
 *
 * The configuration syntax is (names and signal quantity are only given as an example):
 *
 * +FloatPIDGAM = {
 *     Class = FloatPIDGAM
 *     Kp = 10.0 // or kp or ki or kd must be defined, otherwise an error will occur
 *     Ki = 1.0
 *     Kd = 0.0
 *     SampleTime = 0.001
 *     MaxOutput = 500.0 //optional
 *     MinOutput = -500.0 //optional
 *     InputSignals = {
 *         Reference = {
 *             DataSource = "DDB"
 *             Type = float64 // Supported types: float32 or float64 only
 *         }
 *         Measurement = { //Notice that the measurement is the second signal.
 *             DataSource = "DDB"
 *             Type = float64 // Supported types: float32 or float64 only
 *         }
 *     }
 *     OutputSignals = {
 *         ControllerSignal = {
 *             DataSource = "DDB"
 *             Type = float64 // Supported types: float32 or float64 only
 *         }
 *     }
 * }
 *
 * @section Limitations
 * - Only float32 and float64 data types are supported.
 * - Only one element per signal (scalar), no vector or matrix support.
 */

class FloatPIDGAM : public MARTe::GAM {
public:
    CLASS_REGISTER_DECLARATION()

    /**
     * @brief Default constructor.
     * @post
     * kp = 0.0
     * proportional = 0.0
     * ki = 0.0
     * kid = 0.0
     * integral = 0.0
     * kd = 0.0
     * kdd = 0.0
     * derivative = 0.0
     * sampleTime = 0.0
     * maxOutput = MAX_FLOAT32
     * minOutput = -MAX_FLOAT32
     * maxOutput64 = MAX_FLOAT64
     * minOutput64 = -MAX_FLOAT64
     * enableIntegral = true
     * lastInput = 0.0
     * lastIntegral = 0.0
     * enableSubstraction = false
     * reference = NULL_PTR(float32 *)
     * measurement = NULL_PTR(float32 *)
     * output = NULL_PTR(float32 *)
     * reference64 = NULL_PTR(float64 *)
     * measurement64 = NULL_PTR(float64 *)
     * output64 = NULL_PTR(float64 *)
     * nOfInputSignals = 0u
     * nOfOutputSignals = 0u
     * nOfInputElementsReference = 0u
     * nOfInputElementsMeasurement = 0u
     * nOfOutputElements = 0u
     * nOfInputSamplesReference = 0u
     * nOfInputSamplesMeasurement = 0u
     * nOfOuputSamples = 0u
     * inputReferenceDimension = 0u
     * inputMeasurementDimension = 0u
     * outputDimension = 0u
     */

    FloatPIDGAM();

    /**
     * @brief Default destructor. Clears all internal pointers.
     * @post
     * reference = NULL_PTR(float32 *)
     * measurement = NULL_PTR(float32 *)
     * output = NULL_PTR(float32 *)
     * reference64 = NULL_PTR(float64 *)
     * measurement64 = NULL_PTR(float64 *)
     * output64 = NULL_PTR(float64 *)
     */
    virtual ~FloatPIDGAM();

    /**
     * @brief Initialise the parameters of the GAM according to the configuration file
     * @param[in] data GAM configuration
     * @details Load the following parameters from a predefined configuration
     * Kp
     * Ki
     * Kd
     * SampleTime
     * MaxOutput (optional)
     * MinOutput (optional)
     * @post
     * !(Kp = 0.0 && Ki = 0.0 && Kd = 0.0)
     * SampleTime > 0.0
     * MaxOutput > MinOutput
     * @return true if all postconditions are met
     */
    virtual bool Initialise(MARTe::StructuredDataI & data);

    /**
     * @brief Setup the input/output variables.
     * @details Initialise the input and output pointers and verify the number of elements, number
     * of samples and dimension. Moreover, a flag is set to 1 if the error must be calculated internally.
     * @post
     * nOfInputSignals = 1 (reference) || nOfInputSignals = 2 (reference and measurement)
     * nOfOutputSignals = 1
     * nOfInputElementsReference = 1 (no support for vectors)
     * nOfInputElementsMeasurement = 1 (no support for vectors)
     * nOfOutputElements = 1 (no support for vectors)
     * nOfInputSamplesReference = 1
     * nOfInputSamplesMeasurement = 1
     * nOfOuputSamples = 1
     * inputReferenceDimension = 0
     * inputMeasurementDimension = 0
     * outputDimension = 0
     * reference != NULL
     * if enableSubstraction == true => measurement != NULL
     * output != NULL
     * @return true if all postconditions are met.
     */
    virtual bool Setup();

    /**
     * @brief Implements the PID.
     * @details First computes the PID, then saturates the output if needed. If the output
     * is saturated a flag prevents the integral term to continuing growing.
     * @return true.
     */
    virtual bool Execute();

    /**
     * @brief Exports GAM parameters back to configuration tree.
     */
    virtual bool ExportData(MARTe::StructuredDataI & data);

private:

    /**
     * proportional coefficient in the time domain
     */
    float32 kp;
    float64 kp64;

    /**
     * contribution of the proportional term
     */
    float32 proportional;
    float64 proportional64;

    /**
     * integral coefficient in the time domain
     */
    float32 ki;
    float64 ki64;

    /**
     * integral coefficient in the discrete domain. kid = ki * sampleTime. It is used to speed up the operations
     */
    float32 kid;
    float64 kid64;

    /**
     * contribution of the integral term
     */
    float32 integral;
    float64 integral64;

    /**
     * derivative coefficient in the time domain
     */
    float32 kd;
    float64 kd64;

    /**
     * derivative coefficient in the discrete domain. kdd = kd / sampleTime. It is used to speed up the operations
     */
    float32 kdd;
    float64 kdd64;

    /**
     * contribution of the derivative term
     */
    float32 derivative;
    float64 derivative64;

    /**
     * indicates the time between samples
     */
    float32 sampleTime;

    /**
     * upper limit saturation
     */
    float32 maxOutput;
    float64 maxOutput64;

    /**
     * lower limit saturation
     */
    float32 minOutput;
    float64 minOutput64;

    /**
     * enables/disables the integral term when saturation is acting (anti-windup function)
     */
    bool enableIntegral;

    /**
     * saves the last input value
     */
    float32 lastInput;
    float64 lastInput64;

    /**
     * saves the last integrated term
     */
    float32 lastIntegral;
    float64 lastIntegral64;

    /**
     * when enableSubstraction is TRUE the GAM expects two inputs: reference value and the feedback value (the actual measurement).
     * if enableSubstraction is FALSE the GAM expects one input: the error value (reference - measurement) or the reference value for pure feedforward control
     */
    bool enableSubstraction;

    /**
     * points to the input reference array of the GAM
     */
    float32 *reference;
    float64 *reference64;

    /**
     * points to the input measurement array of the GAM
     */
    float32 *measurement;
    float64 *measurement64;

    /**
     * points to the output array of the GAM (which is the output of the PID controller)
     */
    float32 *output;
    float64 *output64;

    /**
     * data type holders
     */
    TypeDescriptor referencedType;
    TypeDescriptor measurementdType;
    TypeDescriptor outputdType;

    /**
     * number of input signals (1 or 2)
     */
    uint32 nOfInputSignals;

    /**
     * number of output signals (1)
     */
    uint32 nOfOutputSignals;

    /**
     * number of input elements of the reference signal. Indicates the input array size (1)
     */
    uint32 nOfInputElementsReference;

    /**
     * number of input elements for the feedback signal. Indicates the input array size (1)
     */
    uint32 nOfInputElementsMeasurement;

    /**
     * number of output elements (1)
     */
    uint32 nOfOutputElements;

    /**
     * number of input samples of the reference signal (1)
     */
    uint32 nOfInputSamplesReference;

    /**
     * number of input samples of the feedback signal (1)
     */
    uint32 nOfInputSamplesMeasurement;

    /**
     * number of output samples (1)
     */
    uint32 nOfOuputSamples;

    /**
     * input reference dimension (0)
     */
    uint32 inputReferenceDimension;

    /**
     * input measurement dimension (0)
     */
    uint32 inputMeasurementDimension;

    /**
     * output dimension (0)
     */
    uint32 outputDimension;

    /**
     * @brief Implements the PID
     */
    inline void GetValue();

    /**
     * @brief Saturates the output of the PID if needed
     */
    inline void Saturation();

};
}
/*---------------------------------------------------------------------------*/
/*                        Inline method definitions                          */
/*---------------------------------------------------------------------------*/

#endif /* FLOATPIDGAM_H_ */

