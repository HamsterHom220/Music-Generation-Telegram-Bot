# Constraint-based monophonic generation
from mido import Message, MetaMessage, MidiFile, MidiTrack
from pychord import Chord
from random import randint,shuffle
from math import ceil

NUM_OF_BARS = 32
TICKS_PER_BAR = 1920
MODES = [
    [2, 2, 1, 2, 2, 2, 1], # IONIAN
    [2, 1, 2, 2, 2, 1, 2], # DORIAN
    [1, 2, 2, 2, 1, 2, 2], # PHRYGIAN
    [2, 2, 2, 1, 2, 2, 1], # LYDIAN
    [2, 2, 1, 2, 2, 1, 2], # MIXOLYDIAN
    [2, 1, 2, 2, 1, 2, 2], # AEOLIAN
    [1, 2, 2, 1, 2, 2, 2], # LOCRIAN
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

# args: [[1]..[1]] with len=num of bars
def subdivide(bars: list[list[int]]) -> list[list[int]]:
    if bars[0][0]==8:
        return bars
    divide = randint(0,1)
    if divide:
        bars[0][0] *= 2
        bars[0].insert(0,bars[0][0])
        shuffle(bars[0])
        shuffle(bars)
    return subdivide(bars)


melody_track = [
    MetaMessage("time_signature", numerator=4, denominator=4),
    MetaMessage("track_name", name="generated melody"),
    Message("program_change", program=0, time=0)
]
out_file = MidiFile()

key = randint(0,11)
mode = randint(0,6)
octave = randint(-1,4)
print(NUMBER_TO_NOTE[key],mode,octave)

allowed_notes = [key]
for interval in MODES[mode]:
    key += interval
    allowed_notes.append(key)

subdivision = subdivide([[1] for _ in range(NUM_OF_BARS)])
for bar in subdivision:
    for denominator in bar:
        note = allowed_notes[randint(0,6)] + 36 + 12*octave
        melody_track.append(Message("note_on", note=note, velocity=50, time=0))
        melody_track.append(Message("note_off", note=note, velocity=50, time=ceil(TICKS_PER_BAR/denominator)))

out_file.tracks.append(melody_track)
out_file.save("output.mid")