from ..paths import Paths

from gpu.types import GPUShader


def load_shader(vert_id: str, frag_id: str) -> GPUShader:
    with open(Paths.LIB_SHADERS('vert', vert_id.lower() + '.vert'), 'r') as f_vert,\
         open(Paths.LIB_SHADERS('frag', frag_id.lower() + '.frag'), 'r') as f_frag:
        return GPUShader(f_vert.read(), f_frag.read())
