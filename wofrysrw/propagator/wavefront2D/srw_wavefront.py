from srwlib import *

import copy
import numpy
import array
import scipy.constants as codata

m_to_eV = codata.h*codata.c/codata.e
#angstroms_to_eV = codata.h*codata.c/codata.e*1e10

from wofry.propagator.wavefront import WavefrontDimension

from wofry.propagator.wavefront2D.generic_wavefront import GenericWavefront2D
from wofry.propagator.decorators import WavefrontDecorator

class WavefrontPrecisionParameters(object):
    def __init__(self,
                 sr_method = 1,  #SR calculation method: 0- "manual", 1- "auto-undulator", 2- "auto-wiggler"
                 relative_precision = 0.01, # relative precision
                 start_integration_longitudinal_position = 0, # longitudinal position to start integration (effective if < zEndInteg)
                 end_integration_longitudinal_position = 0, # longitudinal position to finish integration (effective if > zStartInteg)
                 number_of_points_for_trajectory_calculation = 50000, #Number of points for trajectory calculation
                 use_terminating_terms = 1, # Use "terminating terms" (i.e. asymptotic expansions at zStartInteg and zEndInteg) or not (1 or 0 respectively)
                 sampling_factor_for_adjusting_nx_ny = 0.0 # sampling factor for adjusting nx, ny (effective if > 0)
                 ):
        self._sr_method = sr_method
        self._relative_precision = relative_precision
        self._start_integration_longitudinal_position = start_integration_longitudinal_position
        self._end_integration_longitudinal_position = end_integration_longitudinal_position
        self._number_of_points_for_trajectory_calculation = number_of_points_for_trajectory_calculation
        self._use_terminating_terms = use_terminating_terms
        self._sampling_factor_for_adjusting_nx_ny = sampling_factor_for_adjusting_nx_ny

    def to_SRW_array(self):
        return [int(self._sr_method),
                float(self._relative_precision),
                float(self._start_integration_longitudinal_position),
                float(self._end_integration_longitudinal_position),
                int(self._number_of_points_for_trajectory_calculation),
                int(self._use_terminating_terms),
                float(self._sampling_factor_for_adjusting_nx_ny)]

class WavefrontParameters(object):
    def __init__(self, 
                 photon_energy_min = 100,
                 photon_energy_max = 10100,
                 photon_energy_points = 51,
                 h_slit_gap = 0,
                 h_slit_points = 1,
                 v_slit_gap = 0,
                 v_slit_points = 1,
                 distance = 10.0,
                 wavefront_precision_parameters=WavefrontPrecisionParameters()):
        self._photon_energy_min         = photon_energy_min
        self._photon_energy_max         = photon_energy_max
        self._photon_energy_points      = photon_energy_points
        self._h_slit_gap                = h_slit_gap
        self._h_slit_points             = h_slit_points
        self._v_slit_gap                = v_slit_gap
        self._v_slit_points             = v_slit_points
        self._distance                  = distance
        self._wavefront_precision_parameters  = wavefront_precision_parameters

    def to_SRWRadMesh(self):
        return SRWLRadMesh(self._photon_energy_min,
                           self._photon_energy_max,
                           int(self._photon_energy_points),
                           -self._h_slit_gap/2, self._h_slit_gap/2, int(self._h_slit_points),
                           -self._v_slit_gap/2, self._v_slit_gap/2, int(self._v_slit_points),
                           self._distance)

    def to_SRWLStokes(self):
        stk = SRWLStokes()
        stk.allocate(int(self._photon_energy_points),
                     int(self._h_slit_points),
                     int(self._v_slit_points))
        stk.mesh = self.to_SRWRadMesh()

        return stk

#Meaning of Wavefront Propagation Parameters:
#[0]: Auto-Resize (1) or not (0) Before propagation
#[1]: Auto-Resize (1) or not (0) After propagation
#[2]: Relative Precision for propagation with Auto-Resizing (1. is nominal)
#[3]: Allow (1) or not (0) for semi-analytical treatment of the quadratic (leading) phase terms at the propagation
#[4]: Do any Resizing on Fourier side, using FFT, (1) or not (0)
#[5]: Horizontal Range modification factor at Resizing (1. means no modification)
#[6]: Horizontal Resolution modification factor at Resizing
#[7]: Vertical Range modification factor at Resizing
#[8]: Vertical Resolution modification factor at Resizing
#[9]: Type of wavefront Shift before Resizing (not yet implemented)
#[10]: New Horizontal wavefront Center position after Shift (not yet implemented)
#[11]: New Vertical wavefront Center position after Shift (not yet implemented)

class WavefrontPropagationParameters(object):
    def __init__(self,
                 auto_resize_before_propagation                         = 0,
                 auto_resize_after_propagation                          = 0,
                 relative_prevision_for_propagation_with_autoresizing   = 1.0,
                 allow_semianalytical_treatment_of_quadratic_phase_term = 0,
                 do_any_resizing_on_fourier_side_using_fft              = 0,
                 horizontal_range_modification_factor_at_resizing       = 1.0,
                 horizontal_resolution_modification_factor_at_resizing  = 1.0,
                 vertical_range_modification_factor_at_resizing         = 1.0,
                 vertical_resolution_modification_factor_at_resizing    = 1.0,
                 type_of_wavefront_shift_before_resizing                = 0,
                 new_horizontal_wavefront_center_position_after_shift   = 0,
                 new_vertical_wavefront_center_position_after_shift     = 0):
            self._auto_resize_before_propagation                         = auto_resize_before_propagation
            self._auto_resize_after_propagation                          = auto_resize_after_propagation
            self._relative_prevision_for_propagation_with_autoresizing   = relative_prevision_for_propagation_with_autoresizing
            self._allow_semianalytical_treatment_of_quadratic_phase_term = allow_semianalytical_treatment_of_quadratic_phase_term
            self._do_any_resizing_on_fourier_side_using_fft              = do_any_resizing_on_fourier_side_using_fft
            self._horizontal_range_modification_factor_at_resizing       = horizontal_range_modification_factor_at_resizing
            self._horizontal_resolution_modification_factor_at_resizing  = horizontal_resolution_modification_factor_at_resizing
            self._vertical_range_modification_factor_at_resizing         = vertical_range_modification_factor_at_resizing
            self._vertical_resolution_modification_factor_at_resizing    = vertical_resolution_modification_factor_at_resizing
            self._type_of_wavefront_shift_before_resizing                = type_of_wavefront_shift_before_resizing
            self._new_horizontal_wavefront_center_position_after_shift   = new_horizontal_wavefront_center_position_after_shift
            self._new_vertical_wavefront_center_position_after_shift     = new_vertical_wavefront_center_position_after_shift

    def to_SRW_array(self):
        return [int(self._auto_resize_before_propagation),
                int(self._auto_resize_after_propagation),
                float(self._relative_prevision_for_propagation_with_autoresizing),
                int(self._allow_semianalytical_treatment_of_quadratic_phase_term),
                int(self._do_any_resizing_on_fourier_side_using_fft),
                float(self._horizontal_range_modification_factor_at_resizing),
                float(self._horizontal_resolution_modification_factor_at_resizing),
                float(self._vertical_range_modification_factor_at_resizing),
                float(self._vertical_resolution_modification_factor_at_resizing),
                int(self._type_of_wavefront_shift_before_resizing),
                float(self._new_horizontal_wavefront_center_position_after_shift),
                float(self._new_vertical_wavefront_center_position_after_shift)]


class PolarizationComponent:
    LINEAR_HORIZONTAL  = 0
    LINEAR_VERTICAL    = 1
    LINEAR_45_DEGREES  = 2
    LINEAR_135_DEGREES = 3
    CIRCULAR_RIGHT     = 4
    CIRCULAR_LEFT      = 5
    TOTAL              = 6

class CalculationType:
    SINGLE_ELECTRON_INTENSITY = 0
    MULTI_ELECTRON_INTENSITY = 1
    SINGLE_ELECTRON_FLUX = 2
    MULTI_ELECTRON_FLUX = 3
    SINGLE_ELECTRON_PHASE = 4
    SINGLE_ELECTRON_RE_E = 5
    SINGLE_ELECTRON_IM_E = 6
    SINGLE_ELECTRON_FLUENCE = 7

class TypeOfDependence:
    VS_E = 0
    VS_X = 1
    VS_Y = 2
    VS_XY = 3
    VS_EX = 4
    VS_EY = 5
    VS_EXY = 6
'''
:param polarization_component_to_be_extracted:
               =0 -Linear Horizontal;
               =1 -Linear Vertical;
               =2 -Linear 45 degrees;
               =3 -Linear 135 degrees;
               =4 -Circular Right;
               =5 -Circular Left;
               =6 -Total
:param calculation_type:
               =0 -"Single-Electron" Intensity;
               =1 -"Multi-Electron" Intensity;
               =2 -"Single-Electron" Flux;
               =3 -"Multi-Electron" Flux;
               =4 -"Single-Electron" Radiation Phase;
               =5 -Re(E): Real part of Single-Electron Electric Field;
               =6 -Im(E): Imaginary part of Single-Electron Electric Field;
               =7 -"Single-Electron" Intensity, integrated over Time or Photon Energy (i.e. Fluence)
:param type_of_dependence:
               =0 -vs e (photon energy or time);
               =1 -vs x (horizontal position or angle);
               =2 -vs y (vertical position or angle);
               =3 -vs x&y (horizontal and vertical positions or angles);
               =4 -vs e&x (photon energy or time and horizontal position or angle);
               =5 -vs e&y (photon energy or time and vertical position or angle);
               =6 -vs e&x&y (photon energy or time, horizontal and vertical positions or angles);
:param fixed_input_photon_energy_or_time: input photon energy [eV] or time [s] to keep fixed (to be taken into account for dependences vs x, y, x&y)
:param fixed_horizontal_position: input horizontal position [m] to keep fixed (to be taken into account for dependences vs e, y, e&y)
:param fixed_vertical_position: input vertical position [m] to keep fixed (to be taken into account for dependences vs e, x, e&x)
'''
class FluxCalculationParameters(object):
    def __init__(self,
                 polarization_component_to_be_extracted=PolarizationComponent.TOTAL,
                 calculation_type=CalculationType.SINGLE_ELECTRON_INTENSITY,
                 type_of_dependence=TypeOfDependence.VS_E,
                 fixed_input_photon_energy_or_time = 0.0,
                 fixed_horizontal_position = 0.0,
                 fixed_vertical_position = 0.0):
    
        self._polarization_component_to_be_extracted = polarization_component_to_be_extracted
        self._calculation_type                       = calculation_type                      
        self._type_of_dependence                     = type_of_dependence                    
        self._fixed_input_photon_energy_or_time      = fixed_input_photon_energy_or_time     
        self._fixed_horizontal_position              = fixed_horizontal_position             
        self._fixed_vertical_position                = fixed_vertical_position     

class SRWWavefront(SRWLWfr, WavefrontDecorator):

    def __init__(self,
                 _arEx=None,
                 _arEy=None,
                 _typeE='f',
                 _eStart=0,
                 _eFin=0,
                 _ne=0,
                 _xStart=0,
                 _xFin=0,
                 _nx=0,
                 _yStart=0,
                 _yFin=0,
                 _ny=0,
                 _zStart=0,
                 _partBeam=None):
        SRWLWfr.__init__(self,
                         _arEx=_arEx,
                         _arEy=_arEy,
                         _typeE=_typeE,
                         _eStart=_eStart,
                         _eFin=_eFin,
                         _ne=_ne,
                         _xStart=_xStart,
                         _xFin=_xFin,
                         _nx=_nx,
                         _yStart=_yStart,
                         _yFin=_yFin,
                         _ny=_ny,
                         _zStart=_zStart,
                         _partBeam=_partBeam)


    def get_wavelength(self):
        if (self.mesh.eFin + self.mesh.eStart) == 0:
            return 0.0
        else:
            return m_to_eV/((self.mesh.eFin + self.mesh.eStart)*0.5)

    def get_dimension(self):
        return WavefrontDimension.TWO

    def toGenericWavefront(self):
        wavefront = GenericWavefront2D.initialize_wavefront_from_range(self.mesh.xStart,
                                                                       self.mesh.xFin,
                                                                       self.mesh.yStart,
                                                                       self.mesh.yFin,
                                                                       number_of_points=(self.mesh.nx, self.mesh.ny),
                                                                       wavelength=self.get_wavelength())

        wavefront.set_complex_amplitude(SRWEFieldAsNumpy(srwwf=self)[0, :, :, 0])

        return wavefront

    @classmethod
    def fromGenericWavefront(cls, wavefront):
        return SRWWavefrontFromElectricField(wavefront.get_coordinate_x()[0],
                                             wavefront.get_coordinate_x()[-1],
                                             wavefront.get_complex_amplitude(),
                                             wavefront.get_coordinate_y()[0],
                                             wavefront.get_coordinate_y()[-1],
                                             numpy.zeros_like(wavefront.get_complex_amplitude()),
                                             m_to_eV*wavefront.get_wavelength(),
                                             m_to_eV*wavefront.get_wavelength()*1e10,
                                             1,
                                             1.0,
                                             1.0,
                                             1e-3,
                                             1.0,
                                             1e-3)
    @classmethod
    def decorateSRWWF(self, srwwf):
        dim_x = srwwf.mesh.nx
        dim_y = srwwf.mesh.ny
        number_energies = srwwf.mesh.ne

        x_polarization = SRWArrayToNumpy(srwwf.arEx, dim_x, dim_y, number_energies)
        y_polarization = SRWArrayToNumpy(srwwf.arEy, dim_x, dim_y, number_energies)

        wavefront = SRWWavefrontFromElectricField(horizontal_start=srwwf.mesh.xStart,
                                                  horizontal_end=srwwf.mesh.xFin,
                                                  horizontal_efield=x_polarization,
                                                  vertical_start=srwwf.mesh.yStart,
                                                  vertical_end=srwwf.mesh.yFin,
                                                  vertical_efield=y_polarization,
                                                  energy_min=srwwf.mesh.eStart,
                                                  energy_max=srwwf.mesh.eFin,
                                                  energy_points=srwwf.mesh.ne,
                                                  z=srwwf.mesh.zStart,
                                                  Rx=srwwf.Rx,
                                                  dRx=srwwf.dRx,
                                                  Ry=srwwf.Ry,
                                                  dRy=srwwf.dRy)


        wavefront.numTypeElFld=srwwf.numTypeElFld
        wavefront.partBeam=srwwf.partBeam

        return wavefront

    def duplicate(self):
        wavefront = SRWWavefront(_arEx=copy.deepcopy(self.arEx),
                         _arEy=copy.deepcopy(self.arEy),
                         _typeE=self.numTypeElFld,
                         _eStart=self.mesh.eStart,
                         _eFin=self.mesh.eFin,
                         _ne=self.mesh.ne,
                         _xStart=self.mesh.xStart,
                         _xFin=self.mesh.xFin,
                         _nx=self.mesh.nx,
                         _yStart=self.mesh.yStart,
                         _yFin=self.mesh.yFin,
                         _ny=self.mesh.ny,
                         _zStart=self.mesh.zStart,
                         _partBeam=self.partBeam)

        wavefront.mesh = copy.deepcopy(self.mesh)
        wavefront.Rx  = self.Rx
        wavefront.Ry  = self.Ry
        wavefront.dRx  = self.dRx
        wavefront.dRy  = self.dRy
        wavefront.xc  = self.xc
        wavefront.yc = self.yc
        wavefront.avgPhotEn  = self.avgPhotEn
        wavefront.presCA = self.presCA
        wavefront.presFT  = self.presFT
        wavefront.unitElFld  = self.unitElFld
        wavefront.arElecPropMatr  = copy.deepcopy(self.arElecPropMatr)
        wavefront.arMomX  = copy.deepcopy(self.arMomX)
        wavefront.arMomY  = copy.deepcopy(self.arMomY)
        wavefront.arWfrAuxData  = copy.deepcopy(self.arWfrAuxData)

        return wavefront
        
    def get_intensity(self, multi_electron=True):
        if multi_electron:
            flux_calculation_parameters=FluxCalculationParameters(calculation_type   = CalculationType.MULTI_ELECTRON_INTENSITY,
                                                                  type_of_dependence = TypeOfDependence.VS_XY)
        else:
            flux_calculation_parameters=FluxCalculationParameters(calculation_type   = CalculationType.SINGLE_ELECTRON_INTENSITY,
                                                                  type_of_dependence = TypeOfDependence.VS_XY)

        mesh = copy.deepcopy(self.mesh)

        h_array=numpy.linspace(mesh.xStart, mesh.xFin, mesh.nx)
        v_array=numpy.linspace(mesh.yStart, mesh.yFin, mesh.ny)
        e_array=numpy.linspace(mesh.eStart, mesh.eFin, mesh.ne)

        intensity_array = numpy.zeros((e_array.size, h_array.size, v_array.size))

        for ie in range(e_array.size):
            output_array = array.array('f', [0]*mesh.nx*mesh.ny) #"flat" array to take 2D intensity data

            flux_calculation_parameters._fixed_input_photon_energy_or_time = e_array[ie]

            SRWWavefront.get_intensity_from_electric_field(output_array, self, flux_calculation_parameters)

            tot_len = int(mesh.ny*mesh.nx)
            len_output_array = len(output_array)

            if len_output_array > tot_len:
                output_array = numpy.array(output_array[0:tot_len])
            elif len_output_array < tot_len:
                aux_array = array('d', [0]*len_output_array)
                for i in range(len_output_array): aux_array[i] = output_array[i]
                output_array = numpy.array(array.array(aux_array))
            else:
                output_array = numpy.array(output_array)

            output_array = output_array.reshape(mesh.ny, mesh.nx)

            for ix in range(mesh.nx):
                for iy in range(mesh.ny):
                    intensity_array[ie, ix, iy] = output_array[iy, ix]

        print(intensity_array[0, int(mesh.nx/2), int(mesh.ny/2)])

        return (e_array, h_array, v_array, intensity_array)

    def get_flux(self, multi_electron=True):
        if multi_electron:
            flux_calculation_parameters=FluxCalculationParameters(calculation_type   = CalculationType.MULTI_ELECTRON_FLUX,
                                                                  type_of_dependence = TypeOfDependence.VS_E)
        else:
            flux_calculation_parameters=FluxCalculationParameters(calculation_type   = CalculationType.SINGLE_ELECTRON_FLUX,
                                                                  type_of_dependence = TypeOfDependence.VS_E)

        output_array = array.array('f', [0]*self.mesh.ne)

        SRWWavefront.get_intensity_from_electric_field(output_array, self, flux_calculation_parameters)
        
        data = numpy.ndarray(buffer=output_array, shape=self.mesh.ne, dtype=output_array.typecode)

        energy_array=numpy.linspace(self.mesh.eStart,
                                    self.mesh.eFin,
                                    self.mesh.ne)
        spectral_flux_array = numpy.zeros(energy_array.size)

        for ie in range(energy_array.size):
            spectral_flux_array[ie] = data[ie]

        return (energy_array, spectral_flux_array)

    #TODO: must be defined
    def get_power_density(self):
        hArray = numpy.zeros(self.mesh.nx)
        vArray = numpy.zeros(self.mesh.ny)
        powerArray = numpy.zeros((self.mesh.nx,self.mesh.ny))

        return (hArray, vArray, powerArray)

    @classmethod
    def get_intensity_from_electric_field(cls,
                                          output_array,
                                          srw_wavefront,
                                          flux_calculation_parameters = FluxCalculationParameters()):

        srwl.CalcIntFromElecField(output_array,
                                  srw_wavefront,
                                  flux_calculation_parameters._polarization_component_to_be_extracted,
                                  flux_calculation_parameters._calculation_type,
                                  flux_calculation_parameters._type_of_dependence,
                                  flux_calculation_parameters._fixed_input_photon_energy_or_time,
                                  flux_calculation_parameters._fixed_horizontal_position,
                                  flux_calculation_parameters._fixed_vertical_position)

        return output_array

# ------------------------------------------------------------------
# ------------------------------------------------------------------
# ------------------------------------------------------------------
# ACCESSORIES
# ------------------------------------------------------------------
# ------------------------------------------------------------------

def SRWEFieldAsNumpy(srwwf):
    """
    Extracts electrical field from a SRWWavefront
    :param srw_wavefront: SRWWavefront to extract electrical field from.
    :return: 4D numpy array: [energy, horizontal, vertical, polarisation={0:horizontal, 1: vertical}]
    """

    dim_x = srwwf.mesh.nx
    dim_y = srwwf.mesh.ny
    number_energies = srwwf.mesh.ne

    x_polarization = SRWArrayToNumpy(srwwf.arEx, dim_x, dim_y, number_energies)
    y_polarization = SRWArrayToNumpy(srwwf.arEy, dim_x, dim_y, number_energies)

    e_field = numpy.concatenate((x_polarization, y_polarization), 3)

    return e_field

def SRWWavefrontFromElectricField(horizontal_start,
                                  horizontal_end,
                                  horizontal_efield,
                                  vertical_start,
                                  vertical_end,
                                  vertical_efield,
                                  energy_min,
                                  energy_max,
                                  energy_points,
                                  z,
                                  Rx,
                                  dRx,
                                  Ry,
                                  dRy):
    """
    Creates a SRWWavefront from pi and sigma components of the electrical field.
    :param horizontal_start: Horizontal start position of the grid in m
    :param horizontal_end: Horizontal end position of the grid in m
    :param horizontal_efield: The pi component of the complex electrical field
    :param vertical_start: Vertical start position of the grid in m
    :param vertical_end: Vertical end position of the grid in m
    :param vertical_efield: The sigma component of the complex electrical field
    :param energy: Energy in eV
    :param z: z position of the wavefront in m
    :param Rx: Instantaneous horizontal wavefront radius
    :param dRx: Error in instantaneous horizontal wavefront radius
    :param Ry: Instantaneous vertical wavefront radius
    :param dRy: Error in instantaneous vertical wavefront radius
    :return: A wavefront usable with SRW.
    """

    horizontal_size = horizontal_efield.shape[0]
    vertical_size = horizontal_efield.shape[1]

    if horizontal_size % 2 == 1 or \
       vertical_size % 2 == 1:
        # raise Exception("Both horizontal and vertical grid must have even number of points")
        print("NumpyToSRW: WARNING: Both horizontal and vertical grid must have even number of points")

    horizontal_field = numpyArrayToSRWArray(horizontal_efield)
    vertical_field = numpyArrayToSRWArray(vertical_efield)

    srwwf = SRWWavefront(_arEx=horizontal_field,
                         _arEy=vertical_field,
                         _typeE='f',
                         _eStart=energy_min,
                         _eFin=energy_max,
                         _ne=energy_points,
                         _xStart=horizontal_start,
                         _xFin=horizontal_end,
                         _nx=horizontal_size,
                         _yStart=vertical_start,
                         _yFin=vertical_end,
                         _ny=vertical_size,
                         _zStart=z)

    srwwf.Rx = Rx
    srwwf.Ry = Ry
    srwwf.dRx = dRx
    srwwf.dRy = dRy

    return srwwf

def numpyArrayToSRWArray(numpy_array):
    """
    Converts a numpy.array to an array usable by SRW.
    :param numpy_array: a 2D numpy array
    :return: a 2D complex SRW array
    """
    elements_size = numpy_array.size

    r_horizontal_field = numpy_array[:, :].real.transpose().flatten().astype(numpy.float)
    i_horizontal_field = numpy_array[:, :].imag.transpose().flatten().astype(numpy.float)

    tmp = numpy.zeros(elements_size * 2, dtype=numpy.float32)
    for i in range(elements_size):
        tmp[2*i] = r_horizontal_field[i]
        tmp[2*i+1] = i_horizontal_field[i]

    return array('f', tmp)

def SRWArrayToNumpy(srw_array, dim_x, dim_y, number_energies):
    """
    Converts a SRW array to a numpy.array.
    :param srw_array: SRW array
    :param dim_x: size of horizontal dimension
    :param dim_y: size of vertical dimension
    :param number_energies: Size of energy dimension
    :return: 4D numpy array: [energy, horizontal, vertical, polarisation={0:horizontal, 1: vertical}]
    """
    re = numpy.array(srw_array[::2], dtype=numpy.float)
    im = numpy.array(srw_array[1::2], dtype=numpy.float)

    e = re + 1j * im
    e = e.reshape((dim_y,
                   dim_x,
                   number_energies,
                   1)
                  )

    e = e.swapaxes(0, 2)

    return e.copy()
