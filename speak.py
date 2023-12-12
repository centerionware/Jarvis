import pyttsx3
import argparse

parser = argparse.ArgumentParser("python speak.py -i \"Hello World\" -v \"Samantha\"")
parser.add_argument("-v", help="Voice to use", type=str, default="Samantha")
parser.add_argument("-i", help="Input", type=str)
args = parser.parse_args()

def SpeakText(command):
    engine = pyttsx3.init()
    engine.say(command)
    engine.runAndWait()

SpeakText(args.i)