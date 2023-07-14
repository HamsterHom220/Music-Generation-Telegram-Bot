from constants import *
import music21
from math import floor,ceil
from mido import second2tick
from pychord import Chord
from random import randint,shuffle

class Note:
    """
    A class for temporary storage of MIDI message data in mutable form.
    Type ~ pitch
    """

    def __init__(self, type: int, timestamp, state:str, track, velocity=50):
        self.type = type
        self.timestamp = timestamp
        self.velocity = velocity
        self.state = state
        self.track = track


def find_notes_in_key(tonic:int,mode:str):
    notes_in_key = [tonic]
    for interval in MODES[mode]:
        tonic = (tonic + interval) % 12
        notes_in_key.append(tonic)
    return notes_in_key


def adjust_chord(chord: Chord, allowed_notes, octave, ticks_per_bar) -> list[Note]:
    filtered = []
    chord_notes = chord.components()
    for i in range(len(chord.components())):
        if NOTE_TO_NUMBER[chord_notes[i]] in allowed_notes:
            note = NOTE_TO_NUMBER[chord_notes[i]] + 36 + 12 * octave
            filtered.append(Note(note, 0, 'note_on', i,30))
            filtered.append(Note(note, ticks_per_bar, 'note_off', i,30))
    return filtered


class Parser:
    '''
    Processes the input file for generators that require it.
    '''
    def __init__(self, generator,input_file,ticks_per_bar):
        # The recipient of processed data
        self.generator = generator
        self.input_file = input_file
        self.ticks_per_bar = ticks_per_bar

    # def update_input(self):
    #     self.input_file = MidiFile(INPUT_FILENAME, type=1)

    def extract_notes(self):
        cur_duration = 0
        for track in self.input_file.tracks:
            prev_time = -1
            for token in track:
                # token.time is the time that elapsed since the previous token's time value
                # note_on with time=0 is equivalent to note_off
                if not token.is_meta:
                    # if at some moment there are multiple notes played simultaneously,
                    # consider only such one of them that appears the most early in the input file
                    if (token.time!=prev_time) and (token.type == "note_off" or (token.type == "note_on" and token.time != 0)):
                        self.generator.notes.append(token.note % 12)
                        self.generator.durations.append(token.time)
                        cur_duration += token.time

                        octave = (token.note // 12) - 1
                        if octave < self.generator.lowest_octave:
                            self.generator.lowest_octave = octave

                        if cur_duration >= self.ticks_per_bar//4:
                            for i in range(cur_duration // self.ticks_per_bar//4):
                                self.generator.lowest_octave_per_quarter_of_bar.append(self.generator.lowest_octave)
                            cur_duration %= self.ticks_per_bar//4
                            self.generator.lowest_octave = 7

                        prev_time = token.time

        self.generator.total_duration = ceil(second2tick(self.input_file.length,tempo=TEMPO,ticks_per_beat=self.ticks_per_bar))
        self.generator.bar_quarters = floor(self.generator.total_duration / (self.ticks_per_bar // 4) / 4)

    def identify_key(self):
        key = music21.converter.parse(INPUT_FILENAME).analyze('key')
        self.generator.key = key.name
        self.generator.tonic = key.tonic.name


def subdivide(bars: list[list[int]]) -> list[list[int]]:
    '''
    Function for subdividing a whole note into a random sequence of notes >= 1/8.
    Initial undivided notes sequence is represented as the array [[1]..[1]] with length==num of bars.
    :param bars: list of ordered lists with note duration denominators for each bar
    :return: bars: list of ordered lists with note duration denominators for each bar
    '''
    if bars[0][0] == 8:
        return bars
    divide = randint(0, 1)
    if divide:
        bars[0][0] *= 2
        bars[0].insert(0, bars[0][0])
        shuffle(bars[0])
        shuffle(bars)
    return subdivide(bars)