# while streaming webcam over UDP to GCE, receive the GCE server's response
# (note identification) so it can be played over local mac's audio.

from scamp import *
from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI()

# configure music generation
s = Session()
s.timing_policy = 0.7
nm = {
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
# default instrument (if one can't be identified)
inst_name = "music box"


class Note(BaseModel):
    id: str


class Instrument(BaseModel):
    name: str


# ------------- HEALTH --------------------------
@app.get("/")
def index():
    return {"response": "this is the papermusic note-player server"}


@app.get("/health")
def health():
    return {"status": "ok"}


# -------------- HANDLE INSTRUMENT ID (init synth) ----------------
@app.post("/instrument")
def instrument(i: Instrument):
    global inst_name
    try:
        i = s.new_part(i.name)
        inst_name = i.name
        print("⭐ found matching preset instrument: {}".format(i.name))
        return {"response": "success - instrument {} initialized.".format(i.name)}
    except:
        print("🤔 unrecognized instrument {}, using default.".format(i.name))
        return {
            "response": "success - unrecognized instrument {}, using default.".format(
                i.name
            )
        }


# ------------- HANDLE PLAYED NOTES --------------------------
@app.post("/note")
def playnote(n: Note):
    note_id = n.id
    note_id = note_id.strip().replace(" ", "").replace(",", "").replace(".", "")
    print("🤖 PaliGemma saw: {}".format(note_id))
    # replace a generic note with a specific octave
    if note_id in ["C", "D", "E", "F", "G", "A", "B"]:
        note_id += "4"
    # play the note
    if note_id in nm:
        inst = s.new_part(inst_name)
        midinote = nm[note_id]
        # https://scamp.marcevanstein.com/narrative/note_properties.html
        inst.play_note(midinote, 1, 1, {"articulations": ["staccato"]})
        return {"response": "success - note {} played.".format(note_id)}
    else:
        print("🤔 unrecognized note {}, playing silence".format(note_id))
        return {
            "response": "success - unrecognized note {}, playing silence".format(
                note_id
            )
        }


def init():
    print(
        """
🎹 🎹 🎹 🎹 🎹 🎹 🎹 🎹 🎹 🎹 
┌─┐┌─┐┌─┐┌─┐┬─┐┌┬┐┌┐┌┬ ┬┌─┐┬┌─┐
├─┘├─┤├─┘├┤ ├┬┘│││││││ │└─┐││  
┴  ┴ ┴┴  └─┘┴└─┴ ┴┘└┘└─┘└─┘┴└─┘
 ✏️  ✏️  ✏️  ✏️  ✏️  ✏️  ✏️  ✏️  ✏️  ✏️
          """
    )
