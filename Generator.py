from constants import MODES
class Generator:
    '''Parent class for all generator algorithms.'''
    # lowest_note_offset: choose even lowest note offset for modes 1,2,4,5,6, and odd for 3,7
    # lowest_note_offset < 0: accomp will be lower than the input, otherwise higher
    def __init__(self, velocity=40, mode_name="IONIAN", lowest_note_offset=-2):
        self.velocity = velocity
        self.mode = MODES[mode_name]
        self.lowest_note_offset = lowest_note_offset

        self.inp_data_init()

    def inp_data_init(self):
        """
        Use before the first generation to create generator cache and for cleaning the cache after each generation.
        """
        # data to be extracted from input
        self.notes = []
        self.durations = []
        self.total_duration = 0
        self.lowest_octave = 7
        self.lowest_octave_per_quarter_of_bar = []
        self.key = None  # features a tonic note and its corresponding chords
        self.tonic = None  # base note of a mode
        self.output_info = ""
        self.bar_quarters = 0

    def create_output(self,input_file):
        raise NotImplementedError("Each concrete Generator has its own create_output() implementation.")