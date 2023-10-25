from ..paths import Paths

from gpu.types import GPUShader


libcode_cache: dict[str, str] = {}


def load_shader(vert_id: str, frag_id: str, lib_id: str | None = None) -> GPUShader:
    with open(Paths.LIB_SHADERS('vert', vert_id.lower() + '.vert'), 'r') as f_vert,\
         open(Paths.LIB_SHADERS('frag', frag_id.lower() + '.frag'), 'r') as f_frag:
        if lib_id is not None:
            libcode = libcode_cache.get(lib_id, None)
            if libcode is None:
                with open(Paths.LIB_SHADERS('lib', lib_id.lower() + '.glsl'), 'r', encoding='utf-8') as f_lib:
                    libcode_cache[lib_id] = libcode = f_lib.read()
        else:
            libcode = None
        return GPUShader(f_vert.read(), f_frag.read(), libcode=libcode)
