/**
 * @file WaterTankGAM.h
 * @brief Header file for class WaterTankGAM
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

 * @details This header file contains the declaration of the class WaterTankGAM
 * with all of its public, protected and private members. It may also include
 * definitions for inline methods which need to be visible to the compiler.
 */

#ifndef WATERTANKGAM_H
#define WATERTANKGAM_H

/*---------------------------------------------------------------------------*/
/*                        Standard header includes                           */
/*---------------------------------------------------------------------------*/
#include <math.h>
//#include <random>
/*---------------------------------------------------------------------------*/
/*                        Project header includes                            */
/*---------------------------------------------------------------------------*/

#include "GAM.h"

/*---------------------------------------------------------------------------*/
/*                           Class declaration                               */
/*---------------------------------------------------------------------------*/
// namespace MARTe2Tutorial {
namespace MARTe {
/**
 * @brief An example of a GAM which has fixed inputs and outputs.
 *
 * @details This GAM multiplies the input signal by a Gain.
 * The configuration syntax is (names and types are only given as an example):
 *
 * +GAMWaterTank = {
 *      Class = WaterTankGAM
 *      InputFlowRate = 20.0 //Compulsory
 *      OutputFlowRate = 50.0 //Compulsory
 *      TankArea         = 20.0 //Compulsory
 *      MaxVoltage       = 5 //Compulsory
 *      MinVoltage       = 0 //Compulsory
 *     InputSignals = {
 *         UsecTime = {
 *            Type = "uint32"
 *         }
 *         PumpVoltageRequest = {
 *             Type = float
 *         }
 *     }
 *     OutputSignals = {
 *         WaterHeight = {
 *             Type = float
 *         }
 *         PumpVoltage = {
 *             Type = float
 *         }
 *     }
 * }
 */
class WaterTankGAM : public MARTe::GAM {
public:
    CLASS_REGISTER_DECLARATION()
    /**
     * @brief Constructor. NOOP.
     */
    WaterTankGAM();

    /**
     * @brief Destructor. NOOP.
     */
    virtual ~WaterTankGAM();

    /**
     * @brief Reads the Gain from the configuration file.
     * @param[in] data see GAM::Initialise. The parameter Gain shall exist and will be read as an uint32.
     * @return true if the parameter Gain can be read.
     */
    virtual bool Initialise(MARTe::StructuredDataI & data);

    /**
     * @brief Verifies correctness of the GAM configuration.
     * @details Checks that the number of input signals is equal to the number of output signals is equal to one and that the same type is used.
     * @return true if the pre-conditions are met.
     * @pre
     *   SetConfiguredDatabase() &&
     *   GetNumberOfInputSignals() == GetNumberOfOutputSignals() == 1 &&
     *   GetSignalType(InputSignals, 0) == GetSignalType(OutputSignals, 0) == uint32 &&
     *   GetSignalNumberOfDimensions(InputSignals, 0) == GetSignalNumberOfDimensions(OutputSignals, 0) == 0 &&
     *   GetSignalNumberOfSamples(InputSignals, 0) == GetSignalNumberOfSamples(OutputSignals, 0) == 1 &&
     *   GetSignalNumberOfElements(InputSignals, 0) == GetSignalNumberOfElements(OutputSignals, 0) == 1
     */
    virtual bool Setup();

    /**
     * @brief Multiplies the input signal by the Gain.
     * @return true.
     */
    virtual bool Execute();

    /**
     * @brief Export information about the component
     */
    virtual bool ExportData(MARTe::StructuredDataI & data);

private:

    /**
     * The input signals
     */
    //MARTe::uint32 *inputSignal;
    MARTe::uint32 *usecTime;
    MARTe::float64 *pumpVoltageRequest;

    /**
     * The output signal
     */
    MARTe::float64 *waterHeight;
    MARTe::float64 *pumpVoltage;
    //MARTe::uint32 *outputSignal;

    /**
     * The configured gain.
     */
    //MARTe::uint32 gain;
    /** Last usec time (for the integral) */
    uint32                                   lastUsecTime;
        /** Last water height (for the integral) */
    float                                   lastHeight;
    /** Last voltage value after saturation*/
    float                                   lastVoltage;
    /** The input flow rate constant*/
    float                                   bFlowRate;
    /** The output flow rate constant */
    float                                   aFlowRate;
    /** Tank area */
    float                                   tankArea;
    /** Maximum voltage that can be requested */
    float                                   maxVoltage;
    /** Minimum voltage that can be requested */
    float                                   minVoltage;
};
}
/*---------------------------------------------------------------------------*/
/*                        Inline method definitions                          */
/*---------------------------------------------------------------------------*/

#endif /* WATERTANKGAM_H */

