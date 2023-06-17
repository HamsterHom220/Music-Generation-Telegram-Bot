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

INPUT_FILENAME = "input.mid"

# MIDI note values: 0,1,...,127
INPUT_FILE = MidiFile(INPUT_FILENAME)

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

'''Parent class for all generator algorithms.'''
class Generator:
    # data to be extracted from input
    notes = []
    durations = []
    lowest_octave = 7
    lowest_octave_per_quarter_of_bar = []
    key = None  # features a tonic note and its corresponding chords
    tonic = None  # base note of a mode

    # lowest_note_offset: choose even lowest note offset for modes 1,2,4,5,6, and odd for 3,7
    def __init__(self, accomp_volume=30, mode_name="IONIAN", lowest_note_offset=-4):
        self.accomp_volume = accomp_volume
        self.mode = MODES[mode_name]
        self.lowest_note_offset = lowest_note_offset


class Parser:
    def __init__(self, generator):
        # The recipient of processed data
        self.generator = generator

    def extract_notes(self):
        total_duration = 0
        for track in INPUT_FILE.tracks:
            for token in track:
                # token.time is the time that elapsed since the previous token's time value
                # note_on with time=0 is equivalent to note_off
                if not token.is_meta:
                    if token.type=="note_off" or (token.type=="note_on" and token.time == 0):
                        self.generator.notes.append(token.note%12)
                        self.generator.durations.append(token.time)
                        total_duration += token.time

                        octave = (token.note // 12) - 1
                        if octave < self.generator.lowest_octave:
                            self.generator.lowest_octave = octave

                        if total_duration >= TICKS_PER_QUARTER_OF_BAR:
                            for i in range(total_duration // TICKS_PER_QUARTER_OF_BAR):
                                self.generator.lowest_octave_per_quarter_of_bar.append(self.generator.lowest_octave)
                            total_duration = total_duration % TICKS_PER_QUARTER_OF_BAR
                            self.generator.lowest_octave = 7
                    #elif token.type == "note_on":
                    #    pass
    def identify_key(self):
        key = music21.converter.parse(INPUT_FILENAME).analyze('key')
        self.generator.key = key.name
        self.generator.tonic = key.tonic.name

    # TODO output file creation


class EvolutionaryAlgorithm(Generator):
    def __init__(self, population_size, generations):
        super().__init__()
        self.population_size = population_size
        self.generations = generations

    def generate_chords(self):
        chords = []
        tonic_num = NOTE_TO_NUMBER[self.tonic]
        chord_types = CHORD_SEQ_MINOR
        if self.key.split(" ")[-1]=="major":
            chord_types = CHORD_SEQ_MAJOR
            
        i = 0
        for chord_type in chord_types:
            chord_name = NUMBER_TO_NOTE[tonic_num]
            if chord_type=="DIMINISHED":
                chord_name += "dim"
            elif chord_type=="MINOR":
                chord_name += "m"
            chords.append(Chord(chord_name))
            
            tonic_num = (tonic_num + self.mode[i])%12
            i += 1
        return chords
            

    # TODO evolution methods: get initial population, crossover, mutation
    # TODO fitness calculation (adaptation measures: chord validation, progression validation, repetition check)
    # TODO runner


g = Generator()
p = Parser(g)
p.extract_notes()
p.identify_key()
print("key:",g.key,", tonic:",g.tonic)
