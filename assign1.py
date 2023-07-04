from mido import Message, MetaMessage, MidiFile
from pychord import Chord
from random import randint, shuffle
from math import ceil

NUM_OF_BARS = 32
TICKS_PER_BAR = 1920
MODES = [
    [2, 2, 1, 2, 2, 2, 1],  # 0 IONIAN ~MAJ
    [2, 1, 2, 2, 2, 1, 2],  # 1 DORIAN ~min
    [1, 2, 2, 2, 1, 2, 2],  # 2 PHRYGIAN ~min
    [2, 2, 2, 1, 2, 2, 1],  # 3 LYDIAN ~maj
    [2, 2, 1, 2, 2, 1, 2],  # 4 MIXOLYDIAN ~maj
    [2, 1, 2, 2, 1, 2, 2],  # 5 AEOLIAN ~MIN
    [1, 2, 2, 1, 2, 2, 2],  # 6 LOCRIAN ~min
]
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


class Note:
    """
    A class for temporary storage of MIDI message data in mutable form.
    """

    def __init__(self, type, timestamp, state, velocity=50):
        self.type = type
        self.timestamp = timestamp
        self.velocity = velocity
        self.state = state


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


def melody_constrained(mode=randint(0, 6), tonic=randint(0, 11), octave=randint(-1, 4)):
    """
    Rule/constraint-based monophonic melody generator.
    :param: 0<=mode<=6, 0<=tonic<=11, -1<=octave<=4
    :return:
    - monophonic melody represented as list of bars, i.e. lists of Notes; - list of notes in the key represented by ints; - the mode and octave
    """
    melody_bars = []

    allowed_notes = [tonic]
    for interval in MODES[mode]:
        tonic = (tonic + interval) % 12
        allowed_notes.append(tonic)

    subdivision = subdivide([[1] for _ in range(NUM_OF_BARS)])
    for bar in subdivision:
        melody_bars.append([])
        for denominator in bar:
            note = allowed_notes[randint(0, 6)] + 36 + 12 * octave
            melody_bars[-1].append(Note(note, 0, "note_on"))
            melody_bars[-1].append(Note(note, ceil(TICKS_PER_BAR / denominator), "note_off"))

    melody_bars[-1][-1].type = tonic + 36 + 12 * octave
    return melody_bars, allowed_notes, mode, octave


def chords_grammar(melody_bars, mode):
    """
    Formal grammar-based chord accompaniment generator.
    :param - monophonic melody represented as list of bars, i.e. lists of Notes; - mode of the melody
    :return: list of Chords
    """
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
        chords.append(Chord(chord_name))
        progression_iter += 1
        chord_type_iter += 1
    return chords


melody_bars, allowed_notes, mode, octave = melody_constrained()
accomp = chords_grammar(melody_bars, mode)
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

# accompaniment octave offset
if octave <= 0:
    octave += 2
elif octave == 1:
    octave += 1
elif octave == 2:
    octave -= 1
else:
    octave -= 2

for chord in accomp:
    chord_notes = chord.components()
    for i in range(len(chord_notes)):
        if NOTE_TO_NUMBER[chord_notes[i]] in allowed_notes:
            note = NOTE_TO_NUMBER[chord_notes[i]] + 36 + 12 * octave
            accomp_tracks[i].append(Message("note_on", note=note, velocity=30, time=0))
            accomp_tracks[i].append(Message("note_off", note=note, velocity=30, time=TICKS_PER_BAR))

out_file = MidiFile()
out_file.tracks.append(melody_track)
for track in accomp_tracks:
    out_file.tracks.append(track)
out_file.save("output.mid")
