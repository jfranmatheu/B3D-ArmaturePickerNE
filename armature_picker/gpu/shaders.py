from ..utils.gpu import load_shader as new_sh


class SHADERS:
    ARR_ANG_90 = new_sh('BASIC', 'ARR_ANG_90') # ADVANCE_POINT_GRAPHIC
    COLOR_UNIFORM = new_sh('BASIC', 'COLOR_UNIFORM')
    IMA = new_sh('IMA', 'IMA')
    IMA_OPA = new_sh('IMA', 'IMA_OPA')
    IMA_OUTLINE = new_sh('IMA', 'IMA_OUTLINE')
    WG = new_sh('UV', 'WG')
    WG_GRID = new_sh('UV', 'WG_GRID')
    WG_SLD = new_sh('UV', 'WG_SLD')
    WG_SLD_RNG = new_sh('UV', 'WG_SLD_RNG')
    NODE = new_sh('UV', 'NODE')
