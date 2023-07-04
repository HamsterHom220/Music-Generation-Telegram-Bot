# Constraint-based monophonic generation
from mido import Message, MetaMessage, MidiFile, MidiTrack
from pychord import Chord
from random import randint, shuffle
from math import ceil

NUM_OF_BARS = 32
TICKS_PER_BAR = 1920
MODES = [
    [2, 2, 1, 2, 2, 2, 1],  # IONIAN ~MAJ
    [2, 1, 2, 2, 2, 1, 2],  # DORIAN ~min
    [1, 2, 2, 2, 1, 2, 2],  # PHRYGIAN ~min
    [2, 2, 2, 1, 2, 2, 1],  # LYDIAN ~maj
    [2, 2, 1, 2, 2, 1, 2],  # MIXOLYDIAN ~maj
    [2, 1, 2, 2, 1, 2, 2],  # AEOLIAN ~MIN
    [1, 2, 2, 1, 2, 2, 2],  # LOCRIAN ~min
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


# args: [[1]..[1]] with len=num of bars
def subdivide(bars: list[list[int]]) -> list[list[int]]:
    if bars[0][0] == 8:
        return bars
    divide = randint(0, 1)
    if divide:
        bars[0][0] *= 2
        bars[0].insert(0, bars[0][0])
        shuffle(bars[0])
        shuffle(bars)
    return subdivide(bars)


class Note:
    def __init__(self, type, timestamp, state, velocity=50):
        self.type = type
        self.timestamp = timestamp
        self.velocity = velocity
        self.state = state


def melody_constrained():
    """
    rule/constraint-based generator
    :return:
    - monophonic melody represented as list of bars, i.e. lists of Notes; - list of notes in the key represented by ints; - the mode
    """
    melody_bars = []

    tonic = randint(0, 11)
    mode = randint(0, 6)
    octave = randint(-1, 4)

    allowed_notes = [tonic]
    for interval in MODES[mode]:
        tonic += interval
        allowed_notes.append(tonic)

    subdivision = subdivide([[1] for _ in range(NUM_OF_BARS)])
    for bar in subdivision:
        melody_bars.append([])
        for denominator in bar:
            note = allowed_notes[randint(0, 6)] + 36 + 12 * octave
            melody_bars[-1].append(Note(note, 0, "note_on"))
            melody_bars[-1].append(Note(note, ceil(TICKS_PER_BAR / denominator), "note_off"))
            # melody_track.append(Message("note_on", note=note, velocity=50, time=0))
            # melody_track.append(Message("note_off", note=note, velocity=50, time=ceil(TICKS_PER_BAR/denominator)))

    # melody_track.pop(-1)
    # melody_track.pop(-1)
    # melody_track.append(Message("note_on", note=allowed_notes[4]+ 36 + 12*octave, velocity=50, time=0))
    # melody_track.append(Message("note_off", note=allowed_notes[4]+ 36 + 12*octave, velocity=50, time=ceil(TICKS_PER_BAR/denominator)))
    melody_bars[-1][-1].type = tonic + 36 + 12 * octave
    return melody_bars, allowed_notes, mode, octave


def chords_grammar(melody_bars, allowed_notes, mode):
    """
    formal grammar-based generator
    :param - monophonic melody represented as list of bars, i.e. lists of Notes; - list of notes in the key represented by ints; - mode of the melody
    :return:
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
        chord = NUMBER_TO_NOTE[bar[randint(0, len(bar) - 1)].type%12]
        if progression_iter + 1 >= len(cur_progression):
            cur_progression = PROGRESSIONS[randint(0, len(PROGRESSIONS) - 1)]
            
        if chord_types[chord_type_iter % len(chord_types)] == "DIMINISHED":
            chord += "dim"
        elif chord_types[chord_type_iter % len(chord_types)] == "MINOR":
            chord += "m"
        chords.append(Chord(chord))
        progression_iter += 1
        chord_type_iter += 1
    return chords


melody_bars, allowed_notes, mode, octave = melody_constrained()
accomp = chords_grammar(melody_bars,allowed_notes,mode)

melody_track = [
    MetaMessage("time_signature", numerator=4, denominator=4),
    MetaMessage("track_name", name="generated melody"),
    Message("program_change", program=0, time=0)
]
accomp_tracks = [[
    MetaMessage("time_signature", numerator=4, denominator=4),
    MetaMessage("track_name", name="chord track "+str(i)),
    Message("program_change", program=0, time=0)
] for i in range(3)]

for bar in melody_bars:
    for note in bar:
        melody_track.append(Message(note.state,note=note.type,velocity=note.velocity,time=note.timestamp))

if octave<=1:
    octave += 2
else:
    octave -= 2
for chord in accomp:
    chord_notes = chord.components()
    for i in range(len(chord_notes)):
        note = NOTE_TO_NUMBER[chord_notes[i]] + 36 + 12*octave
        accomp_tracks[i].append(Message("note_on",note=note,velocity=30,time=0))
        accomp_tracks[i].append(Message("note_off", note=note, velocity=30, time=TICKS_PER_BAR))

out_file = MidiFile()
out_file.tracks.append(melody_track)
for track in accomp_tracks:
    out_file.tracks.append(track)
out_file.save("output.mid")
