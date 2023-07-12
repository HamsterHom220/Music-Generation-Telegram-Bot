from constants import *
import music21
from math import floor,ceil
from mido import second2tick, MidiFile

class Parser:
    '''
    Processes the input file for generators that require it.
    '''
    def __init__(self, generator,input_file):
        # The recipient of processed data
        self.generator = generator
        self.input_file = input_file

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

                        if cur_duration >= TICKS_PER_BAR//4:
                            for i in range(cur_duration // TICKS_PER_BAR//4):
                                self.generator.lowest_octave_per_quarter_of_bar.append(self.generator.lowest_octave)
                            cur_duration %= TICKS_PER_BAR//4
                            self.generator.lowest_octave = 7

                        prev_time = token.time

        self.generator.total_duration = ceil(second2tick(self.input_file.length,tempo=TEMPO,ticks_per_beat=TICKS_PER_BAR))
        self.generator.bar_quarters = floor(self.generator.total_duration / (TICKS_PER_BAR // 4) / 4)

    def identify_key(self):
        key = music21.converter.parse(INPUT_FILENAME).analyze('key')
        self.generator.key = key.name
        self.generator.tonic = key.tonic.name
