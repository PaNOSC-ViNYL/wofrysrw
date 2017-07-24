import numpy

from srwlib import SRWLPartBeam

from syned.storage_ring.electron_beam import ElectronBeam

class SRWElectronBeamDecorator():

    def to_SRWLPartBeam(self):
        pass

    @classmethod
    def from_SRWLPartBeam(cls, srw_part_beam, number_of_bunches = 400):
        pass

class SRWElectronBeamGeometricalProperties(object):
    def __init__(self,
                 electron_beam_size_h = 0.0,
                 electron_beam_divergence_h = 0.0,
                 electron_beam_size_v = 0.0,
                 electron_beam_divergence_v = 0.0):
        self._electron_beam_size_h = electron_beam_size_h
        self._electron_beam_divergence_h = electron_beam_divergence_h
        self._electron_beam_size_v = electron_beam_size_v
        self._electron_beam_divergence_v = electron_beam_divergence_v

    def to_info(self):
        info = 'Electron beam : \n'
        info += '   RMS size H/V [um]: '+ repr(self._electron_beam_size_h*1e6) + '  /  ' + repr(self._electron_beam_size_v*1e6) + '\n'
        info += '   RMS divergence H/V [urad]: '+ repr(self._electron_beam_divergence_h*1e6) + '  /  ' + repr(self._electron_beam_divergence_v*1e6) + '\n\n'

        return info

class SRWElectronBeam(ElectronBeam, SRWElectronBeamDecorator):
    def __init__(self,
                 energy_in_GeV = 1.0,
                 energy_spread = 0.0,
                 current = 0.1,
                 number_of_bunches = 400,
                 moment_xx=0.0,
                 moment_xxp=0.0,
                 moment_xpxp=0.0,
                 moment_yy=0.0,
                 moment_yyp=0.0,
                 moment_ypyp=0.0,
                 drift_distance=0.0):
        super().__init__(energy_in_GeV, energy_spread, current, number_of_bunches, moment_xx, moment_xxp, moment_xpxp, moment_yy, moment_yyp, moment_ypyp)

        self._drift_distance = drift_distance

    def set_moments_from_electron_beam_geometrical_properties(self, electron_beam_geometrical_properties = SRWElectronBeamGeometricalProperties()):
        self.set_sigmas_all(sigma_x=electron_beam_geometrical_properties._electron_beam_size_h,
                            sigma_xp=electron_beam_geometrical_properties._electron_beam_divergence_h,
                            sigma_y=electron_beam_geometrical_properties._electron_beam_size_v,
                            sigma_yp=electron_beam_geometrical_properties._electron_beam_divergence_v)

    def set_drift_distance(self, drift_distance):
        self._drift_distance = drift_distance

    def get_electron_beam_geometrical_properties(self):
        x, xp, y, yp = self.get_sigmas_all()

        return SRWElectronBeamGeometricalProperties(electron_beam_size_h=x,
                                                    electron_beam_divergence_h=xp,
                                                    electron_beam_size_v=y,
                                                    electron_beam_divergence_v=yp)
    def to_SRWLPartBeam(self):
        srw_electron_beam = SRWLPartBeam()
        srw_electron_beam.Iavg = self._current
        srw_electron_beam.partStatMom1.x = 0.0
        srw_electron_beam.partStatMom1.y = 0.0

        srw_electron_beam.partStatMom1.z = 0
        srw_electron_beam.partStatMom1.xp = 0
        srw_electron_beam.partStatMom1.yp = 0
        srw_electron_beam.partStatMom1.gamma = self.gamma()

        #2nd order statistical moments:
        srw_electron_beam.arStatMom2[0] = self._moment_xx   # <(x-x0)^2> [m^2]
        srw_electron_beam.arStatMom2[1] = self._moment_xxp  # <(x-x0)*(x'-x'0)> [m]
        srw_electron_beam.arStatMom2[2] = self._moment_xpxp # <(x'-x'0)^2>
        srw_electron_beam.arStatMom2[3] = self._moment_yy   #<(y-y0)^2>
        srw_electron_beam.arStatMom2[4] = self._moment_yyp  #<(y-y0)*(y'-y'0)> [m]
        srw_electron_beam.arStatMom2[5] = self._moment_ypyp #<(y'-y'0)^2>
        srw_electron_beam.arStatMom2[10] = self._energy_spread**2 #<(E-E0)^2>/E0^2

        srw_electron_beam.drift(self._drift_distance)

        return srw_electron_beam

    @classmethod
    def from_SRWLPartBeam(cls, srw_part_beam, number_of_bunches = 400):
        srw_electron_beam = SRWElectronBeam(energy_spread = numpy.sqrt(srw_part_beam.arStatMom2[10]),
                                            current = srw_part_beam.Iavg,
                                            number_of_bunches = number_of_bunches,
                                            moment_xx  = srw_part_beam.arStatMom2[0],
                                            moment_xxp = srw_part_beam.arStatMom2[1],
                                            moment_xpxp= srw_part_beam.arStatMom2[2],
                                            moment_yy  = srw_part_beam.arStatMom2[3],
                                            moment_yyp = srw_part_beam.arStatMom2[4],
                                            moment_ypyp= srw_part_beam.arStatMom2[5],
                                            drift_distance=srw_part_beam.z)

        srw_electron_beam.set_energy_from_gamma(srw_part_beam.partStatMom1.gamma)

        return srw_electron_beam