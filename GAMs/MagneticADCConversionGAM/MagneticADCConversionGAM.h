/**
 * @file MagneticADCConversionGAM.h
 * @brief Header file for class MagneticADCConversionGAM
 * @date 18/07/2025
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

 * @details This header file contains the declaration of the class MagneticADCConversionGAM
 * with all of its public, protected and private members. It may also include
 * definitions for inline methods which need to be visible to the compiler.
 * 
 * @note Compilation command:
 * 
 * $ make -C GAMs/MagneticADCConversionGAM -f Makefile.gcc
 */

#ifndef MAGNETICADCCONVERSIONGAM_H_
#define MAGNETICADCCONVERSIONGAM_H_

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
 * @brief A GAM that converts integrated signals from Mirnov coils (ADC outputs in [V·s]) into magnetic fields [T].
 *
 * @details
 * This GAM applies the following transformation for each coil:
 * 
 * B(t) = (ADC(t) * Gain * Pol / EffArea) * (faradaySign / CLOCK_FREQ * RT_DECIM)
 *
 * Where:
 *  - ADC(t): Input integrated signal from each coil [V·s]
 *  - Gain: Calibration gain for the coil
 *  - Pol: Polarity factor (1.0 or -1.0)
 *  - EffArea: Effective coil area [m²]
 *  - faradaySign: Constant (-1.0) from Faraday's law
 *  - CLOCK_FREQ: Base sampling frequency of ADC system (10 kHz for ISTTOK)
 *  - RT_DECIM: Real-time decimation factor (00 for ISTTOK)
 *  - correctionCte = faradaySign / (CLOCK_FREQ * RT_DECIM)
 *
 * ### Key Features:
 * - Real-time conversion of ADC integrated Mirnov coil signals to magnetic field values
 * - Performs real-time processing for plasma control applications
 * - Allows per-coil calibration parameters (EffArea, Pol, Gain)
 * - Default values are applied if any parameter is missing
 *
 * ### Configuration Parameters:
 * - For each coil (1 to 12):
 *      - `EffArea`      [float64] : Effective coil area [m²]
 *      - `Pol`          [float64] : Polarity (1.0 or -1.0)
 *      - `Gain`         [float64] : Channel gain
 *
 * ### Configuration Example:
* ```
*       +MagneticADCConversionGAM = {
*            Class = MagneticADCConversionGAM
*            Coil1 = { EffArea = 2.793e-3 Gain = 17.3887e-6 Pol = -1 } // optional
*            ...
*            Coil12 = { EffArea = 2.442e-3 Gain = 17.4413e-6 Pol = 1 } // optional
*            InputSignals = {
*                AdcInteg0 = {DataSource = "DDB" Type = float32}
*                ...
*                AdcInteg11 = {DataSource = "DDB" Type = float32}
*            }
*            OutputSignals = {
*                inputMirnov0 = {DataSource = "DDB" Type = float32}
*                ...
*                inputMirnov11 = {DataSource = "DDB" Type = float32}
*            }
*        }
* ```
*/

class MagneticADCConversionGAM : public MARTe::GAM {
public:
    CLASS_REGISTER_DECLARATION()
    /**
     * @brief Constructor. Initializes internal pointers and default values.
     */
    MagneticADCConversionGAM();

    /**
     * @brief Destructor. Clears all internal pointers.
     */
    virtual ~MagneticADCConversionGAM();

    /**
     * @brief Reads configuration parameters and validates them.
     * @details Verifies coil calibration parameters.
     * @return true if all parameters are correctly initialized.
     */
    virtual bool Initialise(MARTe::StructuredDataI & data);

    /**
     * @brief Checks signal structure consistency.
     * @details Ensures that the number of input/output signals equals NUM_SIGNALS = 12u
     * and validates samples, elements, and dimensions (must be 1, 1, 0 respectively).
     * @return true if all conditions are satisfied.
     */
    virtual bool Setup();

    /**
     * @brief Converts ADC integrated signals to magnetic fields.
     * @details Applies the conversion formula using coil-specific calibration.
     */
    virtual bool Execute();

    /**
     * @brief Exports GAM parameters back to configuration tree.
     */
    virtual bool ExportData(MARTe::StructuredDataI & data);

private:

    /**
     * The input signals holder
     */
    MARTe::float32 *inputSignals[12u];
    /**
     * The output signals holder
     */
    MARTe::float32 *outputSignals[12u];
    
    /** Coil parameters */
    MARTe::float64 EffArea[12u];
    MARTe::float64 Pol[12u];
    MARTe::float64 Gain[12u];
    MARTe::float32 MagFieldConv[12u];

};
}
/*---------------------------------------------------------------------------*/
/*                        Inline method definitions                          */
/*---------------------------------------------------------------------------*/

#endif /* MAGNETICADCCONVERSIONGAM_H_ */

