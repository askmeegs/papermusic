# while streaming webcam over UDP to GCE, receive the GCE server's response
# (note identification) so it can be played over local mac's audio.

from scamp import *
import requests
import time

# GCE server URL
SERVER_URL = "http://35.231.102.158:8000"


# configure music generation
s = Session()
# default instrument
inst = s.new_part("music box")

# s.timing_policy = 0.7

# maps note name to MIDI note number
nm = {
    "C3": 48,
    "C#3": 49,
    "D3": 50,
    "D#3": 51,
    "E3": 52,
    "F3": 53,
    "F#3": 54,
    "G3": 55,
    "G#3": 56,
    "A3": 57,
    "A#3": 58,
    "B3": 59,
    "C4": 60,
    "C#4": 61,
    "D4": 62,
    "D#4": 63,
    "E4": 64,
    "F4": 65,
    "F#4": 66,
    "G4": 67,
    "G#4": 68,
    "A4": 69,
    "A#4": 70,
    "B4": 71,
    "C5": 72,
    "C#5": 73,
    "D5": 74,
    "D#5": 75,
    "E5": 76,
    "F5": 77,
    "F#5": 78,
    "G5": 79,
    "G#5": 80,
    "A5": 81,
    "A#5": 82,
    "B5": 83,
    "C6": 84,
    "C#6": 85,
    "D6": 86,
    "D#6": 87,
    "E6": 88,
    "F6": 89,
    "F#6": 90,
    "G6": 91,
    "G#6": 92,
    "A6": 93,
    "A#6": 94,
    "B6": 95,
    "C7": 96,
}


def set_instrument():
    global inst
    # HTTP requests to GCE server
    response = requests.get(SERVER_URL + "/instrument")
    inst_name = response.json()["instrument"]
    print("🎹 PaliGemma identified the instrument as: ", inst_name)
    inst = s.new_part(inst_name)


# https://scamp.marcevanstein.com/narrative/note_properties.html
def play_note():
    global inst
    # HTTP requests to GCE server
    response = requests.get(SERVER_URL + "/note")
    note_id = response.json()["note"]
    # if PaliGemma IDed a note without an octave, add default octave
    if note_id in ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]:
        note_id += "4"
    if note_id in nm:
        print("🔈 PLAYING: ", note_id)
        midinote = nm[note_id]
        inst.play_note(midinote, 1, 1, {"articulations": ["staccato"]})
    else:
        print("🤫 Unrecognized note: {}".format(note_id))


def run_client():
    print(
        """
🎹 🎹 🎹 🎹 🎹 🎹 🎹 🎹 🎹 🎹 
┌─┐┌─┐┌─┐┌─┐┬─┐┌┬┐┌┐┌┬ ┬┌─┐┬┌─┐
├─┘├─┤├─┘├┤ ├┬┘│││││││ │└─┐││  
┴  ┴ ┴┴  └─┘┴└─┴ ┴┘└┘└─┘└─┘┴└─┘
 ✏️  ✏️  ✏️  ✏️  ✏️  ✏️  ✏️  ✏️  ✏️  ✏️
          """
    )
    # NOTE - assumes webcamclient.py is also running
    # first, poll the GCE server for the instrument
    time.sleep(3)
    set_instrument()

    # then, continously poll for the note currently being played by the webcam stream. exit on ctrl-c.
    while True:
        try:
            play_note()
        except KeyboardInterrupt:
            print("👋 Exiting...")
            break


if __name__ == "__main__":
    run_client()
