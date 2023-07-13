from mido import Message, MetaMessage, MidiFile
from pychord import Chord
from random import randint, shuffle
from math import ceil
from utils import find_notes_in_key, Note, adjust_chord
from constants import *

NUM_OF_BARS = 32


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


def melody_constrained(mode=MODE_NUM_TO_NAME[randint(0, 6)], tonic=randint(0, 11), octave=randint(-1, 4)):
    """
    Rule/constraint-based monophonic melody generator.
    :param: 0<=mode<=6, 0<=tonic<=11, -1<=octave<=4
    :return:
    - monophonic melody represented as list of bars, i.e. lists of Notes; - list of notes in the key represented by ints; - the mode and octave
    """
    melody_bars = []
    allowed_notes = find_notes_in_key(tonic,mode)

    subdivision = subdivide([[1] for _ in range(NUM_OF_BARS)])
    for bar in subdivision:
        melody_bars.append([])
        for denominator in bar:
            note = allowed_notes[randint(0, 6)] + 36 + 12 * octave
            melody_bars[-1].append(Note(note, 0, "note_on",0))
            melody_bars[-1].append(Note(note, ceil(TICKS_PER_BAR / denominator), "note_off",0))

    melody_bars[-1][-1].type = tonic + 36 + 12 * octave
    return melody_bars, allowed_notes, mode, octave


def chords_grammar(melody_bars, mode, allowed_notes, octave) -> list[list[Note]]:
    """
    Formal grammar-based chord accompaniment generator.
    :param - monophonic melody represented as list of bars, i.e. lists of Notes; - mode of the melody
    :return: list of Chords
    """
    # accompaniment octave offset
    if octave <= 0:
        octave += 2
    elif octave == 1:
        octave += 1
    elif octave == 2:
        octave -= 1
    else:
        octave -= 2

    chords = []
    if mode in [0, 3, 4]:
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

        chords.append(adjust_chord(Chord(chord_name),allowed_notes,octave))
        progression_iter += 1
        chord_type_iter += 1
    return chords


melody_bars, allowed_notes, mode, octave = melody_constrained()
accomp = chords_grammar(melody_bars, mode,allowed_notes,octave)
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
        accomp_tracks[note.track].append(Message(note.state,note=note.type,velocity=note.velocity,time=note.timestamp))


out_file = MidiFile()
out_file.tracks.append(melody_track)
for track in accomp_tracks:
    out_file.tracks.append(track)
out_file.save("output.mid")
