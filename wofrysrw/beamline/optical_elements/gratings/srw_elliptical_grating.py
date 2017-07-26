from wofrysrw.beamline.optical_elements.srw_optical_element import SRWOpticalElement
from wofrysrw.beamline.optical_elements.mirrors.srw_mirror import Orientation, ApertureShape, SimulationMethod, TreatInputOutput
from wofrysrw.beamline.optical_elements.gratings.srw_grating import SRWGrating

from srwlib import SRWLOptMirEl

class SRWEllipticalGrating(SRWGrating, SRWOpticalElement):
    def __init__(self,
                 name                                       = "Undefined",
                 tangential_size                            = 1.2,
                 sagittal_size                              = 0.01,
                 grazing_angle                              = 0.003,
                 orientation_of_reflection_plane            = Orientation.UP,
                 distance_from_first_focus_to_mirror_center =1,
                 distance_from_mirror_center_to_second_focus=1,
                 height_profile_data_file                   = "mirror.dat",
                 height_profile_data_file_dimension         = 1,
                 height_amplification_coefficient           = 1.0,
                 diffraction_order                  =1,
                 grooving_density_0                 =800,
                 grooving_density_1                 =0.0,
                 grooving_density_2                 =0.0,
                 grooving_density_3                 =0.0,
                 grooving_density_4                 =0.0):


        super().__init__(name=name,
                         tangential_size=tangential_size,
                         sagittal_size=sagittal_size,
                         grazing_angle=grazing_angle,
                         orientation_of_reflection_plane=orientation_of_reflection_plane,
                         height_profile_data_file=height_profile_data_file,
                         height_profile_data_file_dimension=height_profile_data_file_dimension,
                         height_amplification_coefficient=height_amplification_coefficient,
                         diffraction_order=diffraction_order,
                         grooving_density_0=grooving_density_0,
                         grooving_density_1=grooving_density_1,
                         grooving_density_2=grooving_density_2,
                         grooving_density_3=grooving_density_3,
                         grooving_density_4=grooving_density_4)

        self.distance_from_first_focus_to_mirror_center  = distance_from_first_focus_to_mirror_center
        self.distance_from_mirror_center_to_second_focus = distance_from_mirror_center_to_second_focus

    def get_SRWLOptMir(self, nvx, nvy, nvz, tvx, tvy):
        return SRWLOptMirEl(_size_tang=self.tangential_size,
                            _size_sag=self.sagittal_size,
                            _p=self.distance_from_first_focus_to_mirror_center,
                            _q=self.distance_from_mirror_center_to_second_focus,
                            _ang_graz=self.grazing_angle,
                            _ap_shape=ApertureShape.RECTANGULAR,
                            _sim_meth=SimulationMethod.THICK,
                            _treat_in_out=TreatInputOutput.WAVEFRONT_INPUT_CENTER_OUTPUT_CENTER,
                            _nvx=nvx,
                            _nvy=nvy,
                            _nvz=nvz,
                            _tvx=tvx,
                            _tvy=tvy)
