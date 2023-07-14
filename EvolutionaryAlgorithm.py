"""
Library with generators and tools for music generation.
Limitations: only the most common time signature (4/4) is supported.
"""
from mido import MetaMessage
from Generator import Generator
from utils import *


class PopulationItem:
    def __init__(self, adaptation_value, chromosome: list[str]):
        self.adaptation = adaptation_value
        self.chromosome = chromosome


class EvolutionaryAlgorithm(Generator):
    # lowest_note_offset: choose even lowest note offset for modes 1,2,4,5,6, and odd for 3,7
    # lowest_note_offset < 0: accomp will be lower than the input, otherwise higher
    def __init__(self, population_size=DEFAULT_POPULATION, generations=DEFAULT_GENERATIONS, mutation_probability_percent=DEFAULT_MUTATION_PROBABILITY,
                 octave_weight=DEFAULT_OCTAVE_W, progression_weight=DEFAULT_PROGRESSION_W, repetition_weight=DEFAULT_REPETITION_W, repeats_search_radius=DEFAULT_RADIUS,lowest_note_offset=DEFAULT_OFFSET):
        self.ticks_per_bar = 1536
        super().__init__()
        self.population_size = population_size
        self.generations = generations
        self.mutation_probability_percent = mutation_probability_percent
        self.octave_weight = octave_weight
        self.progression_weight = progression_weight
        self.repetition_weight = repetition_weight
        self.init_chord_seq = []
        self.repeats_search_radius = repeats_search_radius
        self.lowest_note_offset = lowest_note_offset
        self.input_file = None
        self.inp_data_init()

    def inp_data_init(self):
        # data to be extracted from input
        self.notes = []
        self.durations = []
        self.total_duration = 0
        self.lowest_octave = 7
        self.lowest_octave_per_quarter_of_bar = []
        self.key = None  # features a tonic note and its corresponding chords
        self.tonic = None  # base note of a mode
        self.output_info = ""
        self.bar_quarters = 0

    def build_init_chords(self):
        """Generates and returns chord sequences in form of lists with strings based on the data collected by parser according to the music theory principles."""
        tonic_num = NOTE_TO_NUMBER[self.tonic]
        # chord_types = CHORD_SEQ_MINOR
        # if self.key.split(" ")[-1] == "major":
        #     chord_types = CHORD_SEQ_MAJOR
        if self.mode in [0, 3, 4]:
            chord_types = CHORD_SEQ_MAJOR
        else:
            chord_types = CHORD_SEQ_MINOR

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
        while note_ind < len(self.durations) and chord_ind<self.bar_quarters:
            # octave criterion
            cur_duration += self.durations[note_ind]
            if cur_duration >= self.ticks_per_bar//4:
                for _ in range(cur_duration // self.ticks_per_bar // 4):
                    adaptation += self.check_for_octaves(chromosome, note_ind, chord_ind)
                    chord_ind += 1
                cur_duration %= self.ticks_per_bar//4
            else:
                adaptation += self.check_for_octaves(chromosome, note_ind, chord_ind)
            note_ind += 1

            # repetition criterion
            adaptation += self.check_for_repetitions(chromosome)

            # progression criterion
            adaptation += self.validate_progression(chromosome)
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
        population = []
        for i in range(self.population_size):
            chromosome = []
            for j in range(self.bar_quarters):
                chromosome.append(self.init_chord_seq[randint(0, 6)])

            adaptation = self.compute_adaptation(chromosome)
            population.append(PopulationItem(adaptation, chromosome))
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
        chord_notes = Chord(chromosome[chord_ind].chord).components()
        if NUMBER_TO_NOTE[self.notes[note_ind]] in chord_notes:
            return self.octave_weight
        return 0

    def validate_progression(self, chromosome: list[str]):
        '''
        Checks whether a chromosome is one of the progressions generated by applying
        any of the predefined progression patterns (stored as offset lists) to the chord list
        produced by build_init_chords().
        In future this method can be improved by adding more progression presets and assigning
        different weights to them.
        '''
        for offset_list in PROGRESSIONS:
            valid = True
            for i in range(len(chromosome)):
                if self.init_chord_seq[offset_list[i % len(offset_list)] - 1].chord != chromosome[i].chord:
                    valid = False
                    break
            if valid:
                return self.progression_weight
        return 0

    def check_for_repetitions(self, chromosome: list[str]):
        '''
        This criterion is based on the fact that close pattern repetitions should be avoided.
        In the future, the return formula might be adjusted.
        '''
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
            inp_metadata = self.input_file.tracks[1][0]
        except IndexError:
            inp_metadata = MetaMessage("instrument_name",name="default")
        for i in range(3):
            track = MidiTrack()
            track.append(inp_metadata)
            track.append(MetaMessage("time_signature", numerator=4, denominator=4))
            track.append(MetaMessage("track_name", name="generated track " + str(i)))
            track.append(Message("program_change", program=0, time=0))
            accomp_tracks.append(track)

        self.input_file.type=1
        final_population = self.generate_accomp()

        # choosing the last chromosome as the result
        output_chord_seq = final_population[-1].chromosome
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
                accomp_tracks[j].append(Message("note_off", note=note, velocity=self.velocity, time=self.ticks_per_bar//4))

        for i in range(3):
            accomp_tracks[i].append(self.input_file.tracks[0][-1])
            self.input_file.tracks.append(accomp_tracks[i])
            accomp_file.tracks.append(accomp_tracks[i])

        self.output_info += self.tonic
        if "minor" in self.key:
            self.output_info += "m"

        self.input_file.save("output-combined.mid")
        accomp_file.save("output-accomp.mid")
        self.inp_data_init()


# g = EvolutionaryAlgorithm()
# p = Parser(g)
# p.extract_notes()
# p.identify_key()
# g.create_output()

