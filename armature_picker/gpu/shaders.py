from ..utils.gpu import load_shader as new_sh


class SHADERS:
    COLOR_UNIFORM = new_sh('BASIC', 'COLOR_UNIFORM')
    IMA = new_sh('IMA', 'IMA')
    IMA_OPA = new_sh('IMA', 'IMA_OPA')
    WG = new_sh('UV', 'WG')
    WG_SLD = new_sh('UV', 'WG_SLD')
    WG_SLD_RNG = new_sh('UV', 'WG_SLD_RNG')
    NODE = new_sh('UV', 'NODE')
