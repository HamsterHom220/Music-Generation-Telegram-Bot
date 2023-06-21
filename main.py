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
from random import randint
from math import ceil
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

'''Parent class for all generator algorithms.'''


class Generator:
    # data to be extracted from input
    notes = []
    durations = []
    total_duration = 0
    bars_count = 0
    residue = 0  # the number of accompaniment chords (notes per track) that need to be generated for the last bar
    # if the input ends not exactly at the end of the last bar
    lowest_octave = 7
    lowest_octave_per_quarter_of_bar = []
    key = None  # features a tonic note and its corresponding chords
    tonic = None  # base note of a mode

    # lowest_note_offset: choose even lowest note offset for modes 1,2,4,5,6, and odd for 3,7
    def __init__(self, accomp_volume=30, mode_name="IONIAN", lowest_note_offset=-4):
        self.accomp_volume = accomp_volume
        self.mode = MODES[mode_name]
        self.lowest_note_offset = lowest_note_offset

    def create_output(self, combined):
        """
        Produces: a MIDI file, such that if combined is True, then accompaniment is added to the initial file;
        otherwise it is written to a separate empty file.
        """
        raise NotImplementedError("Each concrete Generator has its own create_output() implementation.")


class Parser:
    def __init__(self, generator):
        # The recipient of processed data
        self.generator = generator

    def extract_notes(self):
        for track in INPUT_FILE.tracks:
            for token in track:
                # token.time is the time that elapsed since the previous token's time value
                # note_on with time=0 is equivalent to note_off
                if not token.is_meta:
                    if token.type == "note_off" or (token.type == "note_on" and token.time == 0):
                        self.generator.notes.append(token.note % 12)
                        self.generator.durations.append(token.time)
                        self.generator.total_duration += token.time

                        octave = (token.note // 12) - 1
                        if octave < self.generator.lowest_octave:
                            self.generator.lowest_octave = octave

                        if self.generator.total_duration >= TICKS_PER_QUARTER_OF_BAR:
                            for i in range(self.generator.total_duration // TICKS_PER_QUARTER_OF_BAR):
                                self.generator.lowest_octave_per_quarter_of_bar.append(self.generator.lowest_octave)
                            self.generator.total_duration = self.generator.total_duration % TICKS_PER_QUARTER_OF_BAR
                            self.generator.lowest_octave = 7
                    # elif token.type == "note_on":
                    #    pass
        self.generator.bars_count = self.generator.total_duration // TICKS_PER_BAR
        self.generator.residue = ceil(self.generator.total_duration % TICKS_PER_BAR / TICKS_PER_QUARTER_OF_BAR)

    def identify_key(self):
        key = music21.converter.parse(INPUT_FILENAME).analyze('key')
        self.generator.key = key.name
        self.generator.tonic = key.tonic.name


class EvolutionaryAlgorithm(Generator):
    def __init__(self, population_size=200, generations=500, mutation_probability_percent=10,
                 octave_weight=1, progression_weight=3, repetition_weight=1, repeats_search_radius=2):
        super().__init__()
        self.population_size = population_size
        self.generations = generations
        self.mutation_probability_percent = mutation_probability_percent
        self.octave_weight = octave_weight
        self.progression_weight = progression_weight
        self.repetition_weight = repetition_weight
        self.init_chord_seq = []
        self.repeats_search_radius = repeats_search_radius

    def generate_chords(self):
        """Generates and returns chord sequences in form of lists with strings based on the data collected by parser according to the music theory principles."""
        tonic_num = NOTE_TO_NUMBER[self.tonic]
        chord_types = CHORD_SEQ_MINOR
        if self.key.split(" ")[-1] == "major":
            chord_types = CHORD_SEQ_MAJOR

        i = 0
        for chord_type in chord_types:
            chord_name = NUMBER_TO_NOTE[tonic_num]
            if chord_type == "DIMINISHED":
                chord_name += "dim"
            elif chord_type == "MINOR":
                chord_name += "m"
            self.init_chord_seq.append(Chord(chord_name))

            tonic_num = (tonic_num + self.mode[i]) % 12
            i += 1

    def compute_adaptation(self, chromosome):
        """
        Measures and returns the adaptation of a given chromosome according to the following criteria:
        octaves check, progression validation, repetition check. For each of them there is a method
        that returns a certain score for each of the given chromosomes. These scores define the adaptation value.
        """
        note_ind = 0
        chord_ind = 0
        adaptation = 0
        cur_duration = 0
        while chord_ind < 4*self.bars_count + self.residue:
            # octave criterion
            cur_duration += self.durations[note_ind]
            if cur_duration>=TICKS_PER_QUARTER_OF_BAR:
                for _ in range(cur_duration//TICKS_PER_QUARTER_OF_BAR):
                    adaptation += self.check_for_octaves(chromosome,note_ind,chord_ind)
                    chord_ind += 1
                cur_duration %= TICKS_PER_QUARTER_OF_BAR
            else:
                adaptation += self.check_for_octaves(chromosome,note_ind,chord_ind)
            note_ind += 1

            # repetition criterion
            if self.residue > 0:
                if chord_ind >= 4*self.bars_count+self.residue-1:
                    adaptation += self.check_for_repetitions(chromosome)
            elif chord_ind >= 4*self.bars_count:
                adaptation += self.check_for_repetitions(chromosome)

            # progression criterion
            if note_ind % self.bars_count == 0 and note_ind <= len(chromosome):
                adaptation += self.validate_progression(chromosome)

        return adaptation

    def generate_population(self):
        """
        For each creature in the population creates a chromosome -
        random chord sequence consisting of the chords provided by generate_chords() method.
        Returns a list of tuples per each of the generated creatures. Each tuple contains
        adaptation value and the chromosome that is its owner.
        Basically, a chromosome is a chord sequence.
        """
        population = []
        for i in range(self.population_size):
            chromosome = []
            for j in range(4 * self.bars_count + self.residue):
                chromosome.append(self.init_chord_seq[randint(0, 6)])

            adaptation = self.compute_adaptation(chromosome)
            population.append((adaptation, chromosome))
        return population

    # chromosome is a list of chords represented by strings
    def check_for_octaves(self, chromosome, note_ind, chord_ind):
        '''
        This criterion is based on the fact that simultaneously played
        notes on the distance that is a multiple of octave between them
        always sound good.
        This function is a special case of mapping the interval between notes
        to some adaptation value.
        Maybe in the future this method will be generalized.
        '''
        chord_notes = Chord(chromosome[chord_ind].chord).components()
        if NUMBER_TO_NOTE[self.notes[note_ind]] in chord_notes:
            return self.octave_weight
        return 0

    def validate_progression(self, chromosome):
        '''
        Checks whether a chromosome is one of the progressions generated by applying
        any of the predefined progression patterns (stored as offset lists) to the chord list
        produced by generate_chords().
        In future this method can be improved by adding more progression presets and assigning
        different weights to them.
        '''
        for offset_list in PROGRESSIONS:
            valid = True
            for i in range(len(chromosome)):
                if self.init_chord_seq[offset_list[i%len(offset_list)] - 1].chord != chromosome[i].chord:
                    valid = False
                    break
            if valid:
                return self.progression_weight
        return 0

    def check_for_repetitions(self,chromosome):
        '''
        This criterion is based on the fact that close pattern repetitions should be avoided.
        In the future, the return formula might be adjusted.
        '''
        chromosome_parts = []
        for i in range(4):
            chromosome_parts.append(chromosome[4*i:4*i+4])
        repeats_count = 0
        for i in range(4):
            r = i+self.repeats_search_radius
            if r>4: r=4
            for j in range(i+1,r):
                if chromosome_parts[i]==chromosome_parts[j]:
                    repeats_count += 1
        return -self.repetition_weight * repeats_count / len(chromosome)

    def crossover(self, chromosome1, chromosome2):
        """
        This method will be applied to the half of the population with the highest adaptation values to
        replace the other half with a new generation of the same size as this half.

        Idea: "...by mating two individuals with different but desirable features,
        we can produce an offspring that combines both of those features."
        [Taken from Intro to Evolutionary Computing by A.E. Eiben , J.E. Smith]

        In the following implementation, each element of the child-chromosome is
        an element from the same position of one of its parents. The parent to share an element
        is chosen with 50/50 chance.
        """
        # TODO implement crossover
        pass

    def mutation(self):
        """
        This method will be applied to the whole population. As a result, in every chromosome,
        with the probability passed to the EvolutionaryAlgorithm constructor,
        two random elements (chords) will be swapped.

        Idea: "Darwin’s insight was that small, random variations – mutations – in phenotypic traits occur during reproduction
        from generation to generation. Through these variations, new combinations of
        traits occur and get evaluated. The best ones survive and reproduce, and so
        evolution progresses."
        [Taken from Intro to Evolutionary Computing by A.E. Eiben , J.E. Smith]
        """
        # TODO implement mutation
        pass

    def run(self):
        final_population = []
        # TODO implement evolutionary algorithm runner
        #  (it will incorporate population generation, adaptation measurements, crossover, and mutations)
        return final_population

    def create_output(self, combined):
        """
        Takes: final_population, self.lowest_octave_per_quarter_of_bar, args passed to constructors.
        Produces: a MIDI file, such that if combined is True, then accompaniment is added to the initial file;
        otherwise it is written to a separate empty file.
        """
        # TODO implement output file creation
        return None


g = Generator()
p = Parser(g)
p.extract_notes()
p.identify_key()
print("key:", g.key, ", tonic:", g.tonic)
