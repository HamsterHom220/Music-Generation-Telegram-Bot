"""
Library with generators and tools for music generation.
Limitations: only the most common time signature (4/4) is supported.
"""
from random import randint
import music21
from mido import Message, MetaMessage, MidiFile, MidiTrack, second2tick, bpm2tempo
from math import floor,ceil
from pychord import Chord
from os import remove

INPUT_FILENAME = "input.mid"

# MIDI note values: 0,1,...,127
input_file = MidiFile(INPUT_FILENAME,type=1)
try:
    TEMPO = input_file.tempo
except:
    TEMPO = bpm2tempo(120)

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


class Generator:
    '''Parent class for all generator algorithms.'''
    # lowest_note_offset: choose even lowest note offset for modes 1,2,4,5,6, and odd for 3,7
    # lowest_note_offset < 0: accomp will be lower than the input, otherwise higher
    def __init__(self, velocity=40, mode_name="IONIAN", lowest_note_offset=-2):
        self.velocity = velocity
        self.mode = MODES[mode_name]
        self.lowest_note_offset = lowest_note_offset

        self.inp_data_init()

    def inp_data_init(self):
        """
        Use before the first generation to create generator cache and for cleaning the cache after each generation.
        """
        # data to be extracted from input
        self.notes = []
        self.durations = []
        self.total_duration = 0
        #self.bars_count = 0
        #self.residue = 0  # the number of accompaniment chords (notes per track) that need to be generated for the last bar
        # if the input ends not exactly at the end of the last bar
        self.lowest_octave = 7
        self.lowest_octave_per_quarter_of_bar = []
        self.key = None  # features a tonic note and its corresponding chords
        self.tonic = None  # base note of a mode
        self.output_info = ""
        self.bar_quarters = 0

    def create_output(self):
        raise NotImplementedError("Each concrete Generator has its own create_output() implementation.")


class Parser:
    def __init__(self, generator):
        # The recipient of processed data
        self.generator = generator

    def extract_notes(self):
        cur_duration = 0
        for track in input_file.tracks:
            prev_time = -1
            for token in track:
                #print(token,type(token))
                # token.time is the time that elapsed since the previous token's time value
                # note_on with time=0 is equivalent to note_off
                if not token.is_meta:
                    # if at some moment there are multiple notes played simultaneously,
                    # consider only such one of them that appears the most early in the input file
                    if (token.time!=prev_time) and (token.type == "note_off" or (token.type == "note_on" and token.time != 0)):
                        self.generator.notes.append(token.note % 12)
                        self.generator.durations.append(token.time)
                        #self.generator.total_duration += token.time
                        cur_duration += token.time

                        octave = (token.note // 12) - 1
                        if octave < self.generator.lowest_octave:
                            self.generator.lowest_octave = octave

                        if cur_duration >= TICKS_PER_QUARTER_OF_BAR:
                            for i in range(cur_duration // TICKS_PER_QUARTER_OF_BAR):
                                self.generator.lowest_octave_per_quarter_of_bar.append(self.generator.lowest_octave)
                            cur_duration %= TICKS_PER_QUARTER_OF_BAR
                            self.generator.lowest_octave = 7

                        prev_time = token.time
                    # elif token.type == "note_on":
                    #    pass
        self.generator.total_duration = ceil(second2tick(input_file.length,tempo=TEMPO,ticks_per_beat=TICKS_PER_BAR))
        #self.generator.bars_count = self.generator.total_duration // TICKS_PER_BAR // 4
        #print("Bars:",self.generator.bars_count)
        #self.generator.residue = ceil(self.generator.total_duration % TICKS_PER_BAR/ TICKS_PER_QUARTER_OF_BAR) # number of residual bar quarters
        #print("Residue:",self.generator.residue)
        self.generator.bar_quarters = floor(self.generator.total_duration / TICKS_PER_QUARTER_OF_BAR / 4)
        #print(self.generator.bar_quarters)
        #exit()

    def identify_key(self):
        key = music21.converter.parse(INPUT_FILENAME).analyze('key')
        self.generator.key = key.name
        self.generator.tonic = key.tonic.name


class PopulationItem:
    def __init__(self, adaptation_value, chromosome: list[str]):
        self.adaptation = adaptation_value
        self.chromosome = chromosome


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

    def build_init_chords(self):
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

        #print("Initial chords built.")

    def compute_adaptation(self, chromosome: list[str]):
        """
        Measures and returns the adaptation of a given chromosome according to the following criteria:
        octaves check, progression validation, repetition check. For each of them there is a method
        that returns a certain score for each of the given chromosomes. These scores define the adaptation value.
        """
        if len(chromosome)==0:
            raise RuntimeError
        note_ind = 0
        chord_ind = 0
        adaptation = 0
        cur_duration = 0
        #print("Computing adaptation for",chromosome,end="...")
        while note_ind < len(self.durations) and chord_ind<self.bar_quarters:#4 * self.bars_count - 1*(self.residue!=0) + self.residue:
            # octave criterion
            cur_duration += self.durations[note_ind]
            if cur_duration >= TICKS_PER_QUARTER_OF_BAR:
                for _ in range(cur_duration // TICKS_PER_QUARTER_OF_BAR):
                    adaptation += self.check_for_octaves(chromosome, note_ind, chord_ind)
                    chord_ind += 1
                cur_duration %= TICKS_PER_QUARTER_OF_BAR
            else:
                adaptation += self.check_for_octaves(chromosome, note_ind, chord_ind)
            note_ind += 1

            # repetition criterion
            # if self.residue > 0:
            #     if chord_ind >= 4 * self.bars_count - 1*(self.residue!=0) + self.residue:
            #         adaptation += self.check_for_repetitions(chromosome)
            #         return adaptation
            #if chord_ind >= self.bar_quarters:
            adaptation += self.check_for_repetitions(chromosome)
                #return adaptation

            # progression criterion
            #if note_ind % self.bars_count == 0 and note_ind <= len(chromosome):
            adaptation += self.validate_progression(chromosome)
        #print(" Result:",adaptation)
        return adaptation

    def generate_population(self):
        """
        For each creature in the population creates a chromosome -
        random chord sequence consisting of the chords provided by build_init_chords() method.
        Returns a list of tuples per each of the generated creatures. Each tuple contains
        adaptation value and the chromosome that is its owner.
        Basically, a chromosome is a chord sequence.
        """
        if self.population_size==0:
            raise RuntimeError
        self.build_init_chords()
        #print("Generating population...")
        population = []
        for i in range(self.population_size):
            chromosome = []
            #print(self.bar_quarters)
            for j in range(self.bar_quarters):#4 * self.bars_count - 1*(self.residue!=0) + self.residue):
                chromosome.append(self.init_chord_seq[randint(0, 6)])

            adaptation = self.compute_adaptation(chromosome)
            population.append(PopulationItem(adaptation, chromosome))
        #print("Population generated.")
        return population

    # chromosome is a list of chords represented by strings
    def check_for_octaves(self, chromosome: list[str], note_ind, chord_ind):
        '''
        This criterion is based on the fact that simultaneously played
        notes on the distance that is a multiple of octave between them
        always sound good.
        This function is a special case of mapping the interval between notes
        to some adaptation value.
        Maybe in the future this method will be generalized.
        '''
        #print("Checking",chromosome,"for octaves at note:",note_ind,", chord:",chord_ind,end="... ")
        chord_notes = Chord(chromosome[chord_ind].chord).components()
        if NUMBER_TO_NOTE[self.notes[note_ind]] in chord_notes:
            #print("Result: found.")
            return self.octave_weight
        #print("Result: not found.")
        return 0

    def validate_progression(self, chromosome: list[str]):
        '''
        Checks whether a chromosome is one of the progressions generated by applying
        any of the predefined progression patterns (stored as offset lists) to the chord list
        produced by build_init_chords().
        In future this method can be improved by adding more progression presets and assigning
        different weights to them.
        '''
        #print("Validating progression for",chromosome,end="... ")
        for offset_list in PROGRESSIONS:
            valid = True
            for i in range(len(chromosome)):
                if self.init_chord_seq[offset_list[i % len(offset_list)] - 1].chord != chromosome[i].chord:
                    valid = False
                    break
            if valid:
                #print("Result: valid.")
                return self.progression_weight
        #print("Result: invalid.")
        return 0

    def check_for_repetitions(self, chromosome: list[str]):
        '''
        This criterion is based on the fact that close pattern repetitions should be avoided.
        In the future, the return formula might be adjusted.
        '''
        #print("Checking",chromosome,"for repetitions... ",end="")
        chromosome_parts = []
        for i in range(4):
            chromosome_parts.append(chromosome[4 * i:4 * i + 4])
        repeats_count = 0
        for i in range(4):
            r = i + self.repeats_search_radius
            if r > 4: r = 4
            for j in range(i + 1, r):
                if chromosome_parts[i] == chromosome_parts[j]:
                    repeats_count += 1
        #("Result:",repeats_count)
        return -self.repetition_weight * repeats_count / len(chromosome)

    def crossover(self, sorted_population: list[PopulationItem]):
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
        #print("Performing crossover...")
        for j in range(self.population_size // 2):
            parent1 = sorted_population[randint(self.population_size // 2, self.population_size - 1)].chromosome
            parent2 = sorted_population[randint(self.population_size // 2, self.population_size - 1)].chromosome

            if parent2 == parent1:
                parent2 = sorted_population[randint(self.population_size // 2, self.population_size - 1)].chromosome

            child = []
            for i in range(len(parent1)):
                if randint(0, 1) > 0:
                    child.append(parent1[i])
                else:
                    child.append(parent2[i])
            sorted_population[j].chromosome = child
        #print("Crossover completed.")
        return sorted_population  # not guaranteed to be sorted anymore

    def mutation(self, population: list[PopulationItem]):
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
        #print("Performing mutation...")
        for i in range(self.population_size):
            if randint(1, 100) < self.mutation_probability_percent:
                chromosome_len = len(population[i].chromosome)
                if chromosome_len<=1:
                    continue
                i1 = randint(0, chromosome_len - 1)
                i2 = randint(0, chromosome_len - 1)
                while i2 == i1:
                    i2 = randint(0, chromosome_len - 1)
                population[i].chromosome[i1], population[i].chromosome[i2] = population[i].chromosome[i2], population[i].chromosome[i1]
        #print("Mutation completed.")
        return population

    def generate_accomp(self):
        '''
        The evolutionary algorithm runner
        (incorporates population generation, adaptation measurements, crossover, and mutations)
        '''
        final_population = sorted(self.generate_population(), key=lambda x: x.adaptation)
        for _ in range(self.generations):
            final_population = self.mutation(self.crossover(final_population))
            for item in final_population:
                item.adaptation = self.compute_adaptation(item.chromosome)
            final_population = sorted(final_population, key=lambda x: x.adaptation)
        return final_population

    def create_output(self):
        """
        Takes: final_population, self.lowest_octave_per_quarter_of_bar, args passed to constructors.
        Produces: 2 MIDI files, such that "output-combined.mid" is the initial file + accompaniment;
                and "output-accomp.mid" is just the accompaniment written to an empty file.
        """
        accomp_tracks = []
        accomp_file = MidiFile(type=1)
        try:
            inp_metadata = input_file.tracks[1][0]
        except IndexError:
            inp_metadata = MetaMessage("instrument_name",name="default")
        for i in range(3):
            track = MidiTrack()
            track.append(inp_metadata)
            track.append(MetaMessage("time_signature", numerator=4, denominator=4))
            track.append(MetaMessage("track_name", name="generated track " + str(i)))
            track.append(Message("program_change", program=0, time=0))
            accomp_tracks.append(track)

        input_file.type=1
        final_population = self.generate_accomp()

        # choosing the last chromosome as the result
        output_chord_seq = final_population[-1].chromosome
        #print("seq:",output_chord_seq)
        for i in range(len(output_chord_seq)):
            chord_notes = output_chord_seq[i].components()
            for j in range(len(chord_notes)):
                if len(self.lowest_octave_per_quarter_of_bar)<len(chord_notes):
                    self.lowest_octave_per_quarter_of_bar.append(self.lowest_octave)
                note = \
                    36 + 12 * \
                    (self.lowest_octave_per_quarter_of_bar[j]+self.lowest_note_offset) + \
                    NOTE_TO_NUMBER[chord_notes[j]]
                accomp_tracks[j].append(Message("note_on", note=note, velocity=self.velocity, time=0))
                accomp_tracks[j].append(Message("note_off", note=note, velocity=self.velocity, time=TICKS_PER_QUARTER_OF_BAR))

        for i in range(3):
            #print(input_file.tracks)
            accomp_tracks[i].append(input_file.tracks[0][-1])
            input_file.tracks.append(accomp_tracks[i])
            accomp_file.tracks.append(accomp_tracks[i])


        self.output_info += self.tonic
        if "minor" in self.key:
            self.output_info += "m"

        try:
            remove("output-combined.mid")
            remove("output-accomp.mid")
        except OSError:
            pass

        #print(input_file.tracks)
        #print(len(input_file.tracks))
        #print(input_file.type)
        input_file.save("output-combined.mid")
        accomp_file.save("output-accomp.mid")
        self.inp_data_init()


#TEST_____________________________
# g = EvolutionaryAlgorithm()
# p = Parser(g)
# p.extract_notes()
# p.identify_key()
# g.create_output()

# input_file = MidiFile("E melody.mid",type=1)
# g = EvolutionaryAlgorithm()
# p = Parser(g)
# p.extract_notes()
# p.identify_key()
# g.create_output()
