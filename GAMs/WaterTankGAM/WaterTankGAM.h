/**
 * @file WaterTankGAM.h
 * @brief Header file for class WaterTankGAM
 * @date 02/07/2025
 * @authors Bernardo Brotas Carvalho & Felipe Tassari Aveiro (adapted from previous work by Andre Neto)
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
 * 
 * @note Compilation command:
 * 
 * $ make -C GAMs/WaterTankGAM -f Makefile.gcc
 * 
 */

#ifndef WATERTANKGAM_H
#define WATERTANKGAM_H

/*---------------------------------------------------------------------------*/
/*                        Standard header includes                           */
/*---------------------------------------------------------------------------*/

#include <math.h>
// Introduction of noise for future applications
// #include <random>

/*---------------------------------------------------------------------------*/
/*                        Project header includes                            */
/*---------------------------------------------------------------------------*/

#include "GAM.h"

/*---------------------------------------------------------------------------*/
/*                           Class declaration                               */
/*---------------------------------------------------------------------------*/
// namespace MARTe2WaterTank {
namespace MARTe {
/**
 * @brief A GAM that simulates the dynamics of a water tank based on the forward Euler integration method.
 *
 * @details This GAM numerically integrates the height of water in a tank over time.
 * based on a simplified physical model. The evolution of the water level is governed by:
 * 
 *      dh(t)/dt = (Qin(t) - Qout(t)) / A
 * 
 * where:
 * - h(t) is the water height [m]
 *     - A is the tank cross-sectional area [m²]
 *     - Qin is the inflow rate [m³/s], modeled as a linear function of the pump voltage
 *        • Qin = b * V(t), where b is a constant related to proportional relationship
 *          between the input voltage and the inlet flow rate [m³/s/V]
 *     - Qout is the outflow rate [m³/s], modeled as a nonlinear function of the water height
 *       using Torricelli’s law:
 *        • Qout = a * sqrt(h), where a is a constant related to
 *          the physical characteristics of the outlet (orifice area * sqrt(2 * g)) [m**{2.5}/s]
 * 
 * The inflow is controlled by an input voltage command, and both the voltage and the water height are clamped to
 * avoid unphysical values. The integration is carried out explicitly using the forward Euler method with the timestep
 * derived from the time delta between executions of the GAM (based on a microsecond timestamp input).
 * The configuration syntax is (names and types are only given as an example):
 *
 * This module is useful for testing feedback control systems (e.g., PID controllers) in a closed-loop simulation,
 * particularly when evaluating real-time control frameworks like MARTe2.
 * 
 * ### Parameters:
 * The following parameters must be defined in the configuration:
 *  - `InitialHeight`    [float64] : Initial height of the water in the tank [m]
 *  - `InputFlowRate`    [float64] : Inflow coefficient, i.e., flow per volt [m³/s/V]
 *  - `OutputFlowRate`   [float64] : Outflow coefficient `a` in Qout = a * sqrt(h) [m**{2.5}/s]
 *  - `TankArea`         [float64] : Cross-sectional area of the tank [m²]
 *  - `MaxVoltage`       [float64] : Maximum allowed voltage to the pump [V]
 *  - `MinVoltage`       [float64] : Minimum allowed voltage to the pump [V] 
 * 
 * ### Configuration syntax (example):
 * +GAMWaterTank = {
 *     Class = WaterTankGAM
 *     InitialHeight = 0.0 // [m] Initial water level (Compulsory)
 *     InputFlowRate = 0.01 // [m³/s/V] Flow into the tank per volt (Compulsory)
 *     OutputFlowRate = 0.001 // [m**{2.5}/s] Flow out per sqrt(h) (Compulsory)
 *     TankArea         = 2.0 // [m²] Tank cross-sectional area (Compulsory)
 *     MaxVoltage       = 12.0 // [V] Maximum voltage to pump (Compulsory)
 *     MinVoltage       = 0.0 // [V] Minimum voltage to pump (Compulsory)
 * 
 *     InputSignals = {
 *         UsecTime = { // Time in microseconds
 *            Type = uint32
 *         }
 *         PumpVoltageRequest = { // Requested pump voltage [V]
 *             Type = float64
 *         }
 *     }
 *     OutputSignals = {
 *         WaterHeight = { // Resulting water height [m]
 *             Type = float64
 *         }
 *         PumpVoltage = { // Saturated voltage applied [V]
 *             Type = float64
 *         }
 *     }
 * }
 * 
 * @warning This model assumes positive-only water height and does not simulate overflow behavior.
 * Proper controller tuning and initial conditions are essential for stable simulations.
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
     * @brief Verifies correctness of the GAM configuration.
     * @details Checks if the parameters are correctly configured.
     * @return true if the parameters can be read.
     */
    virtual bool Initialise(MARTe::StructuredDataI & data);

    /**
     * @brief Verifies correctness of the GAM configuration.
     * @details Checks if the number of input signals and output signals is 2 in each case, and if the corresponding correct signal types are used.
     * @return true if the pre-conditions are met.
     */
    virtual bool Setup();

    /**
     * @brief Computes the next water height using forward Euler integration.
     * @details Applies flow equations and voltage saturation to simulate tank dynamics.
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
    MARTe::uint32 *usecTime;
    MARTe::float64 *pumpVoltageRequest;

    /**
     * The output signals
     */
    MARTe::float64 *waterHeight;
    MARTe::float64 *pumpVoltage;


    /** Last usec time (for the integral) */
    MARTe::uint32                                   lastUsecTime;
    /**
     * The parameters.
     */
    /** Last water height (for the integral) and set in parameter 
     *  InitialHeight to bootstrap GAM with pre-established water level */
    MARTe::float64                                   lastHeight;
    /** The input flow rate constant*/
    MARTe::float64                                   bFlowRate;
    /** The output flow rate constant */
    MARTe::float64                                   aFlowRate;
    /** Tank area */
    MARTe::float64                                   tankArea;
    /** Maximum voltage that can be requested */
    MARTe::float64                                   maxVoltage;
    /** Minimum voltage that can be requested */
    MARTe::float64                                   minVoltage;
};
}
/*---------------------------------------------------------------------------*/
/*                        Inline method definitions                          */
/*---------------------------------------------------------------------------*/

#endif /* WATERTANKGAM_H */

