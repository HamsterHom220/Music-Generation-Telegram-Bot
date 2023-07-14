from mido import bpm2tempo

# MIDI note values: 0,1,...,127

INPUT_FILENAME = "input.mid"
DEFAULT_MODE = 'AEOLIAN'
DEFAULT_ACCOMP_VOLUME = 40

DEFAULT_NUM_OF_BARS = 32
DEFAULT_TONIC = 0
DEFAULT_OCTAVE = 1

DEFAULT_POPULATION = 200
DEFAULT_GENERATIONS = 100
DEFAULT_MUTATION_PROBABILITY = 10
DEFAULT_OCTAVE_W = 1
DEFAULT_PROGRESSION_W = 3
DEFAULT_REPETITION_W = 1
DEFAULT_RADIUS = 2
DEFAULT_OFFSET = -2

TEMPO = bpm2tempo(120)

# Pairs "mode:scale" (scale - interval pattern to build a mode from a tonic)
# A mode in music theory is determined by the tonic note and the scale used
MODES = {
    "IONIAN": [2, 2, 1, 2, 2, 2, 1],  # natural major
    "DORIAN": [2, 1, 2, 2, 2, 1, 2],
    "PHRYGIAN": [1, 2, 2, 2, 1, 2, 2],
    "LYDIAN": [2, 2, 2, 1, 2, 2, 1],
    "MIXOLYDIAN": [2, 2, 1, 2, 2, 1, 2],
    "AEOLIAN": [2, 1, 2, 2, 1, 2, 2],  # natural minor
    "LOCRIAN": [1, 2, 2, 1, 2, 2, 2]
}

MODES_LIST = [
    [2, 2, 1, 2, 2, 2, 1],  # 0 IONIAN ~MAJ
    [2, 1, 2, 2, 2, 1, 2],  # 1 DORIAN ~min
    [1, 2, 2, 2, 1, 2, 2],  # 2 PHRYGIAN ~min
    [2, 2, 2, 1, 2, 2, 1],  # 3 LYDIAN ~maj
    [2, 2, 1, 2, 2, 1, 2],  # 4 MIXOLYDIAN ~maj
    [2, 1, 2, 2, 1, 2, 2],  # 5 AEOLIAN ~MIN
    [1, 2, 2, 1, 2, 2, 2],  # 6 LOCRIAN ~min
]

MODE_NUM_TO_NAME = ["IONIAN","DORIAN","PHRYGIAN","LYDIAN","MIXOLYDIAN","AEOLIAN","LOCRIAN"]


PROGRESSIONS = [
    [1, 4, 5, 5],
    [1, 1, 4, 5],
    [1, 4, 1, 5],
    [1, 6, 2, 5],
    [1, 5, 4, 1],
    [1, 5, 6, 4],
    [1, 4, 5, 4],
    [1, 3, 6, 5],
    [1, 5, 6, 3],
    [1, 5, 1, 4],
    [1, 3, 4, 5],
    [1, 6, 4, 7],
    [1, 6, 3, 7],
    [6, 4, 1, 5],
]

# CHORD TYPE SEQUENCES
CHORD_SEQ_MAJOR = ["MAJOR", "MINOR", "MINOR", "MAJOR", "MAJOR", "MINOR", "DIMINISHED"]
CHORD_SEQ_MINOR = ["MINOR", "DIMINISHED", "MAJOR", "MINOR", "MINOR", "MAJOR", "MAJOR"]

# Structures to convert number representing a note in MIDI to string representing a note
NUMBER_TO_NOTE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
NOTE_TO_NUMBER = {
    "C": 0, "B#": 0,
    "D-": 1, "C#": 1, "Db": 1,
    "D": 2,
    "E-": 3, "D#": 3, "Eb": 3,
    "E": 4, "F-": 4, "Fb": 4,
    "F": 5, "E#": 5,
    "G-": 6, "F#": 6, "Gb": 6,
    "G": 7,
    "A-": 8, "G#": 8, "Ab": 8,
    "A": 9,
    "B-": 10, "A#": 10, "Bb": 10,
    "B": 11, "C-": 11, "Cb": 11
}
