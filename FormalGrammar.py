from Generator import Generator
from mido import Message, MetaMessage, MidiFile
from pychord import Chord
from random import randint
from math import ceil
from utils import find_notes_in_key, Note, adjust_chord, subdivide
from constants import *


class FormalGrammar(Generator):
    '''
    -1<=octave<=4
    0<=tonic<=11
    '''
    def __init__(self,num_of_bars=DEFAULT_NUM_OF_BARS,tonic=DEFAULT_TONIC,octave=DEFAULT_OCTAVE):
        self.ticks_per_bar = 1920
        super().__init__()
        self.num_of_bars = num_of_bars
        self.tonic = tonic
        self.octave = octave

    def melody_constrained(self):
        """
        Rule/constraint-based monophonic melody generator.
        :param: 0<=mode<=6, 0<=tonic<=11, -1<=octave<=4
        :return:
        - monophonic melody represented as list of bars, i.e. lists of Notes; - list of notes in the key represented by ints; - the mode and octave
        """
        melody_bars = []
        allowed_notes = find_notes_in_key(self.tonic, self.mode_name)

        subdivision = subdivide([[1] for _ in range(self.num_of_bars)])
        for bar in subdivision:
            melody_bars.append([])
            for denominator in bar:
                note = allowed_notes[randint(0, 6)] + 36 + 12 * self.octave
                melody_bars[-1].append(Note(note, 0, "note_on", 0))
                melody_bars[-1].append(Note(note, ceil(self.ticks_per_bar / denominator), "note_off", 0))

        melody_bars[-1][-1].type = self.tonic + 36 + 12 * self.octave
        return melody_bars, allowed_notes

    def chords_grammar(self, melody_bars, allowed_notes) -> list[list[Note]]:
        """
        Formal grammar-based chord accompaniment generator.
        :param - monophonic melody represented as list of bars, i.e. lists of Notes; - mode of the melody
        :return: list of Chords
        """
        # accompaniment octave offset
        if self.octave <= 0:
            self.octave += 2
        elif self.octave == 1:
            self.octave += 1
        elif self.octave == 2:
            self.octave -= 1
        else:
            self.octave -= 2

        chords = []
        if self.mode in [0, 3, 4]:
            chord_types = CHORD_SEQ_MAJOR
        else:
            chord_types = CHORD_SEQ_MINOR
        progression_iter = 0
        chord_type_iter = 0
        cur_progression = PROGRESSIONS[randint(0, len(PROGRESSIONS) - 1)]
        for bar in melody_bars:
            chord_name = NUMBER_TO_NOTE[bar[randint(0, len(bar) - 1)].type % 12]
            if progression_iter + 1 >= len(cur_progression):
                cur_progression = PROGRESSIONS[randint(0, len(PROGRESSIONS) - 1)]

            if chord_types[chord_type_iter % len(chord_types)] == "DIMINISHED":
                chord_name += "dim"
            elif chord_types[chord_type_iter % len(chord_types)] == "MINOR":
                chord_name += "m"

            chords.append(adjust_chord(Chord(chord_name), allowed_notes, self.octave, self.ticks_per_bar))
            progression_iter += 1
            chord_type_iter += 1
        return chords

    def create_output(self):

        melody_bars, allowed_notes = self.melody_constrained()
        accomp = self.chords_grammar(melody_bars, allowed_notes)
        melody_track = [
            MetaMessage("time_signature", numerator=4, denominator=4),
            MetaMessage("track_name", name="generated melody"),
            Message("program_change", program=0, time=0)
        ]
        accomp_tracks = [[
            MetaMessage("time_signature", numerator=4, denominator=4),
            MetaMessage("track_name", name="chord track " + str(i)),
            Message("program_change", program=0, time=0)
        ] for i in range(3)]

        for bar in melody_bars:
            for note in bar:
                melody_track.append(Message(note.state, note=note.type, velocity=note.velocity, time=note.timestamp))

        for chord in accomp:
            for note in chord:
                accomp_tracks[note.track].append(
                    Message(note.state, note=note.type, velocity=note.velocity, time=note.timestamp))

        out_file = MidiFile()
        out_file.tracks.append(melody_track)
        for track in accomp_tracks:
            out_file.tracks.append(track)
        out_file.save("output.mid")
