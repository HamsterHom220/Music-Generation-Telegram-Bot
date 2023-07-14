from telebot import types, TeleBot
from time import time

from Generator import Generator
from constants import *
from dotenv import load_dotenv
from os import getenv
import utils
from mido import MidiFile
from EvolutionaryAlgorithm import EvolutionaryAlgorithm
from FormalGrammar import FormalGrammar

class ConfiguredGenerator:
    def __init__(self, generator: Generator, settings: dict):
        self.generator = generator
        self.settings = settings


load_dotenv()
bot = TeleBot(getenv('SECRET_TOKEN'))

# default values
common_params = {'velocity': DEFAULT_ACCOMP_VOLUME, 'mode': DEFAULT_MODE}

# generators supported at the moment: Evolutionary Algorithm
cur_generator = ''
generator_instances = dict()
parser = utils.Parser(None,None,None)


@bot.message_handler(commands=['start'])
def start(msg):
    '''
    /start command
    '''
    bot.send_message(msg.chat.id,
                     "Hello! Here you can generate music with different generators and settings for them.\n" +
                     "To configure the generation, run /settings and /generators.\n" +
                     "As for now, the result can be generated either on top of an input, or from scratch - "+
                     "via the EvolutionaryAlgorithm and via FormalGrammar correspondingly.\n"
                     "Upload your MIDI-file if needed (only the last submission will be considered).\n" +
                     "Finally, run /generate and wait until the result is produced " +
                     "(it might take from seconds to hours, depending on the number of notes in the input, " +
                     "settings, and generator type)."
                     )


@bot.message_handler(commands=['settings'])
def settings(msg):
    '''
    /settings command
    '''
    bot.send_message(msg.chat.id,
                     "Common settings. To change, use /set <param> <value>\n" +
                     "Available param names: velocity, mode.\n" +
                     "Allowed mode values: IONIAN, DORIAN, PHRYGIAN, LYDIAN, MIXOLYDIAN, AEOLIAN, LOCRIAN.\n" +
                     "Velocity: " + str(common_params['velocity']) + "\n" +
                     "Mode: " + common_params['mode'] + "\n"
                     )


@bot.message_handler(commands=['set'])
def set_param(msg):
    '''
    /set command
    '''
    param, value = msg.text.split(' ')[1:]
    if param in common_params.keys():
        if param=='velocity':
            value = int(value)
        common_params[param] = value
    else:
        if param in {'population', 'generations', 'mutation_probability',
                     'octave_weight', 'progression_weight', 'repetition_weight', 'radius', 'offset',
                     'bars', 'tonic', 'octave'}:
            value = int(value)
        generator_instances[cur_generator].settings[param] = value
    bot.send_message(msg.chat.id, "Changed " + param + " to " + str(value) + ".")


@bot.message_handler(commands=['generators'])
def generators(msg):
    '''
    /generators command
    '''
    markup = types.InlineKeyboardMarkup()
    btn_ea = types.InlineKeyboardButton("Evolutionary Algorithm", callback_data='Evolutionary Algorithm')
    btn_fg = types.InlineKeyboardButton("Formal Grammar", callback_data='Formal Grammar')
    markup.row(btn_ea)
    markup.row(btn_fg)
    bot.send_message(msg.chat.id, "Choose a generator:\n", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    '''
    a function to process the generator type choice and to display settings for the chosen generator
    '''
    global cur_generator
    cur_generator = callback.data
    settings_msg = "Chosen the " + cur_generator + " generator.\n" + \
                   "Generator-specific settings. To change, use /set <param> <value>\n"
    if cur_generator == 'Evolutionary Algorithm':
        if 'Evolutionary Algorithm' not in generator_instances.keys():
            specific_params = {
                'population': DEFAULT_POPULATION, 'generations': DEFAULT_GENERATIONS, 'mutation_probability': DEFAULT_MUTATION_PROBABILITY,
                'octave_weight': DEFAULT_OCTAVE_W, 'progression_weight': DEFAULT_PROGRESSION_W, 'repetition_weight': DEFAULT_REPETITION_W, 'radius': DEFAULT_RADIUS, 'offset': DEFAULT_OFFSET
            }
            generator_instances['Evolutionary Algorithm'] = ConfiguredGenerator(EvolutionaryAlgorithm(),specific_params)

        bot.send_message(callback.message.chat.id, settings_msg +
                         "Available param names: population, generations, mutation_probability, octave_weight," + \
                         "progression_weight, repetition_weight, radius, offset.\n" +
                         "Lowest note offset: choose even lowest note offset for modes 1,2,4,5,6, and odd for 3,7.\n" +
                         "Lowest note offset < 0: accomp will be lower than the input, otherwise higher.\n\n" +
                         "Population size: " + str(generator_instances[cur_generator].settings['population']) + "\n" +
                         "Number of generations: " + str(generator_instances[cur_generator].settings['generations']) + "\n" +
                         "Mutation probability: " + str(generator_instances[cur_generator].settings['mutation_probability']) + "\n" +
                         "Octave weight: " + str(generator_instances[cur_generator].settings['octave_weight']) + "\n" +
                         "Progression weight: " + str(generator_instances[cur_generator].settings['progression_weight']) + "\n" +
                         "Repetition weight: " + str(generator_instances[cur_generator].settings['repetition_weight']) + "\n" +
                         "Repeats search radius: " + str(generator_instances[cur_generator].settings['radius']) + "\n"+
                         "Lowest note offset: " + str(generator_instances[cur_generator].settings['offset'])
                         )
    elif cur_generator == 'Formal Grammar':
        if 'Formal Grammar' not in generator_instances.keys():
            specific_params = {'bars': DEFAULT_NUM_OF_BARS, 'tonic': DEFAULT_TONIC, 'octave': DEFAULT_OCTAVE}
            generator_instances['Formal Grammar'] = ConfiguredGenerator(FormalGrammar(),specific_params)

        bot.send_message(callback.message.chat.id, settings_msg +
                         "Available param names: bars, tonic, octave.\n" +
                         "Number of bars (defines the output length): "+ str(generator_instances[cur_generator].settings['bars']) +".\n" +
                         "Tonic (is in [0;11]): "+ str(generator_instances[cur_generator].settings['tonic'])+" - "+ NUMBER_TO_NOTE[generator_instances[cur_generator].settings['tonic']] +".\n"+
                         "Octave (is in [-1;4]): "+ str(generator_instances[cur_generator].settings['octave']) +"."
                         )
    else:
        bot.send_message(callback.message.chat.id, "Error: unsupported generator chosen - " + cur_generator)


@bot.message_handler(content_types=['document'])
def handle_input_file(msg):
    '''
    a function to retrieve an input file
    '''
    if msg.document.mime_type == 'audio/midi':
        file_info = bot.get_file(msg.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        with open(INPUT_FILENAME, 'wb') as new_file:
            new_file.write(downloaded_file)
        bot.send_message(msg.chat.id, 'Input file accepted. To generate accompaniment, use /generators command.')
    else:
        bot.send_message(msg.chat.id, 'Wrong input format.')


@bot.message_handler(commands=['generate'])
def generate(msg):
    '''
    /generate command
    '''
    info = ""
    output = []
    start = end = 0

    if cur_generator == '':
        bot.send_message(msg.chat.id, "Error: no generator is chosen. Please, choose one via /generators command.")
    else:
        bot.send_message(msg.chat.id, "Generating via " + cur_generator + "...")
        start = time()
        if cur_generator == 'Evolutionary Algorithm':
            parser.generator = generator_instances['Evolutionary Algorithm'].generator
            parser.ticks_per_bar = parser.generator.ticks_per_bar
            parser.input_file = MidiFile(INPUT_FILENAME)
            parser.extract_notes()
            parser.identify_key()
            parser.generator.input_file = parser.input_file
            parser.generator.create_output()
            info += parser.generator.output_info
            output = ["output-combined.mid", "output-accomp.mid"]
        elif cur_generator == 'Formal Grammar':
            generator_instances['Formal Grammar'].generator.create_output()
            output = ["output.mid"]
        else:
            bot.send_message(msg.chat.id, "Error: unsupported generator chosen - " + cur_generator)
        end = time()

    if output != []:
        if cur_generator=='Evolutionary Algorithm':
            generation_msg = "Generated successfully in " + str((end - start) / 60) + " mins.\n"
        elif cur_generator=='Formal Grammar':
            generation_msg = "Generated successfully in " + str(end - start) + " secs.\n"
        if info != "":
            generation_msg += "Details: " + info + "."
        bot.send_message(msg.chat.id, generation_msg)
        for file in output:
            try:
                bot.send_document(msg.chat.id, open(file, 'rb'))
            except:
                bot.send_message(msg.chat.id, "An error occurred during sending the result.")


bot.infinity_polling()