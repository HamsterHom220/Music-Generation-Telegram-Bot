"""
Rationale: while it is hard to achieve useful results in pure music generation nowadays,
    accompaniment generation is quite promising and is widely practically applicable.
    Existing research shows that the most suitable generation approach for this task is to
    use Evolutionary Algorithms.
Aim: to provide a tool that helps composers write music (instead of generating music completely),
    because research shows that such an approach is more efficient due to the limitations of
    state-of-the-art solutions.
Limitations: only the most common time signature (4/4) is supported.
"""
import random
import math
from operator import itemgetter
import music21
from mido import Message, MidiFile, MidiTrack
from pychord import Chord
from time import time

# MIDI note values: 0,1,...,127

INPUT_FILE = "input.mid"
OUTPUT_FILE = "output - "

# Pairs "mode:scale" (scale - interval pattern to build a mode from a tonic)
# A mode in music theory is determined by the tonic note and the scale used
MODE = {
    "IONIAN" : [2, 2, 1, 2, 2, 2, 1], # natural major
    "DORIAN" : [2, 1, 2, 2, 2, 1, 2],
    "PHRYGIAN" : [1, 2, 2, 2, 1, 2, 2],
    "LYDIAN" : [2, 2, 2, 1, 2, 2, 1],
    "MIXOLYDIAN" : [2, 2, 1, 2, 2, 1, 2],
    "AEOLIAN" : [2, 1, 2, 2, 1, 2, 2], # natural minor
    "LOCRIAN" : [1, 2, 2, 1, 2, 2, 2]
}

# Number of ticks representing note and quarter of note in MIDI file
TICKS_PER_BAR = 1536
TICKS_PER_QUARTER_OF_BAR = 384

CHORD_PROGRESSIONS = [
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


class Generator:
    #inp = MidiFile()
    # data to be extracted from input
    lowest_octave_per_quarter_of_bar = []
    note_duration = []
    notes = []
    chords = []
    key = None # features a tonic note and its corresponding chords
    tonic = None # base note of a mode

    # lowest_note_offset: choose even lowest note offset for modes 1,2,4,5,6, and odd for 3,7
    def __init__(self,inp,accomp_volume=30,mode="IONIAN",lowest_note_offset=-4,lowest_octave=7):
        self.inp = inp
        self.accomp_volume = accomp_volume
        self.mode = mode
        self.lowest_note_offset = lowest_note_offset
        self.lowest_octave = lowest_octave

class Parser:
    def parse(self, generator):
        total_duration = 0
        for track in generator.inp.tracks:
            for token in track:
                if token.time != 0 and token.type == "note_on":
                    generator.notes.append(-1)
                if token.type == "note_off":
                    generator.notes.append(token.note%12)
                if token.type=="note_off" or (token.type=="note_on" and token.time != 0):
                    ...
    # TODO finish input file parsing

    # TODO output file creation
    pass

class EvolutionaryAlgorithm(Generator):
    #TODO generate chord sequence
    #TODO evolve melody (adaptation measure - to choose)
    #TODO insert rhythmical info
    #TODO create accomp
    pass