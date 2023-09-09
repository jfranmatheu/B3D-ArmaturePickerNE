from pathlib import Path as _Path


src_path = _Path(__file__).parent

class Paths:
    SRC = src_path
    IMAGES = src_path / 'images'
