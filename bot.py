from telebot import types, TeleBot
from time import time
from constants import *
from dotenv import load_dotenv
from os import getenv,remove
import utils
from mido import MidiFile
from EvolutionaryAlgorithm import EvolutionaryAlgorithm

load_dotenv()
bot = TeleBot(getenv('SECRET_TOKEN'))

# default values
common_params = {'velocity': 40, 'mode': "IONIAN"}
specific_params = dict()

# generators supported at the moment: Evolutionary Algorithm
cur_generator = ''

ea = EvolutionaryAlgorithm()
parser = utils.Parser(None,None)

@bot.message_handler(commands=['start'])
def start(msg):
    '''
    /start command
    '''
    bot.send_message(msg.chat.id,
                     "Hello! Here you can generate music with different generators and settings for them.\n" +
                     "To configure the generation, run /settings and /generators.\n" +
                     "Upload your MIDI-file (only the last submission will be considered).\n" +
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
        common_params[param] = value
    else:
        specific_params[param] = value
    bot.send_message(msg.chat.id, "Changed " + param + " to " + str(value) + ".")


@bot.message_handler(commands=['generators'])
def generators(msg):
    '''
    /generators command
    '''
    markup = types.InlineKeyboardMarkup()
    btn_ea = types.InlineKeyboardButton("Evolutionary Algorithm", callback_data='Evolutionary Algorithm')
    markup.row(btn_ea)
    bot.send_message(msg.chat.id, "Choose a generator:\n", reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: True)
def callback_message(callback):
    '''
    a function to process the generator type choice and to display settings for the chosen generator
    '''
    global cur_generator, specific_params
    cur_generator = callback.data
    settings_msg = "Chosen the " + cur_generator + " generator.\n" + \
                   "Generator-specific settings. To change, use /set <param> <value>\n"
    if cur_generator == 'Evolutionary Algorithm':
        specific_params = {
            'population': 200, 'generations': 200, 'mutation_probability': 10,
            'octave_weight': 1, 'progression_weight': 3, 'repetition_weight': 1, 'radius': 2, 'offset': -2
        }
        bot.send_message(callback.message.chat.id, settings_msg +
                         "Available param names: population, generations, mutation_probability, octave_weight," + \
                         "progression_weight, repetition_weight, radius, offset.\n" +
                         "Lowest note offset: choose even lowest note offset for modes 1,2,4,5,6, and odd for 3,7.\n" +
                         "Lowest note offset < 0: accomp will be lower than the input, otherwise higher.\n\n" +
                         "Population size: " + str(specific_params['population']) + "\n" +
                         "Number of generations: " + str(specific_params['generations']) + "\n" +
                         "Mutation probability: " + str(specific_params['mutation_probability']) + "\n" +
                         "Octave weight: " + str(specific_params['octave_weight']) + "\n" +
                         "Progression weight: " + str(specific_params['progression_weight']) + "\n" +
                         "Repetition weight: " + str(specific_params['repetition_weight']) + "\n" +
                         "Repeats search radius: " + str(specific_params['radius']) + "\n"+
                         "Lowest note offset: " + str(specific_params['offset'])
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
        bot.send_message(msg.chat.id, 'Input file accepted. Please, choose a generator by using the /generators command.')
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
            parser.generator = ea
            parser.input_file = MidiFile(INPUT_FILENAME)
            #parser.update_input()
            parser.extract_notes()
            parser.identify_key()
            ea.create_output(parser.input_file)
            info += ea.output_info
            output = ["output-combined.mid", "output-accomp.mid"]
        else:
            bot.send_message(msg.chat.id, "Error: unsupported generator chosen - " + cur_generator)
        end = time()

    if output != []:
        generation_msg = "Generated successfully in " + str((end - start) / 60) + " mins.\n"
        if info != "":
            generation_msg += "Details: " + info + "."
        bot.send_message(msg.chat.id, generation_msg)
        for file in output:
            try:
                bot.send_document(msg.chat.id, open(file, 'rb'))
            except:
                bot.send_message(msg.chat.id, "An error occurred during sending the result.")


bot.infinity_polling()