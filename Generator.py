from constants import MODES, DEFAULT_MODE, DEFAULT_ACCOMP_VOLUME
class Generator:
    '''Parent class for all generator algorithms.'''
    def __init__(self, velocity=DEFAULT_ACCOMP_VOLUME, mode_name=DEFAULT_MODE):
        self.velocity = velocity
        self.mode = MODES[mode_name]
        self.mode_name = mode_name

    def create_output(self):
        raise NotImplementedError("Each concrete Generator has its own create_output() implementation.")