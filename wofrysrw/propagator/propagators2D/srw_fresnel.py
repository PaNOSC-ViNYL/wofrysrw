# TODO: REMOVE THIS!!!!
try:
    from srwlib import *
    SRWLIB_AVAILABLE = True
except:
    SRWLIB_AVAILABLE = False
    print("SRW is not available")

import scipy.constants as codata
angstroms_to_eV = codata.h*codata.c/codata.e*1e10

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D
from wofry.propagator.propagator import Propagator2D

from wofrysrw.propagator.wavefront2D.srw_wavefront import WavefrontPropagationParameters
from wofrysrw.propagator.wavefront2D.srw_wavefront import SRWWavefront

class FresnelSRW(Propagator2D):

    HANDLER_NAME = "FRESNEL_SRW"

    def get_handler_name(self):
        return self.HANDLER_NAME

    """
    2D Fresnel propagator using convolution via Fourier transform
    :param wavefront:
    :param propagation_distance:
    :param srw_autosetting:set to 1 for automatic SRW redimensionate wavefront
    :return:
    """

    def do_specific_progation(self, wavefront, propagation_distance, parameters):
        if not SRWLIB_AVAILABLE: raise ImportError("SRW is not available")

        if not parameters.has_additional_parameter("srw_drift_wavefront_propagation_parameters"):
            wavefront_propagation_parameters = WavefrontPropagationParameters()
        else:
            wavefront_propagation_parameters = parameters.get_additional_parameter("srw_drift_wavefront_propagation_parameters")

            if not isinstance(wavefront_propagation_parameters, WavefrontPropagationParameters):
                raise ValueError("SRW Wavefront Propagation Parameters not present")

        is_generic_wavefront = isinstance(wavefront, GenericWavefront2D)

        if is_generic_wavefront:
            wavefront = SRWWavefront.fromGenericWavefront(wavefront)
        else:
            if not isinstance(wavefront, SRWWavefront): raise ValueError("wavefront cannot be managed by this propagator")

        #
        # propagation (simple wavefront drift
        #

        optBL = SRWLOptC([SRWLOptD(propagation_distance)], # drift space
                         [wavefront_propagation_parameters.to_SRW_array()])

        srwl.PropagElecField(wavefront, optBL)

        if is_generic_wavefront:
            return wavefront.toGenericWavefront()
        else:
            return wavefront