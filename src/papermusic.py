import cv2
from scamp import *
import os
import google.generativeai as genai
import time

# gemini config
genai.configure(api_key=os.environ["GEMINI_API_KEY"])

# Scamp (music generation) config
s = Session()

s.timing_policy = 0.7

# note to midi mapping. the following basic notes are supported:
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


# helper function: uploads an image to Gemini
def upload_to_gemini(path, mime_type=None):
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file


# the initial call to Gemini is:
# given a drawing of a musical instrument, ask Gemini to identify it
def identify_instrument():
    # wait 2 seconds, then capture a single webcam frame.
    time.sleep(2)
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    fp = "framecapture/webcam_instrument.jpg"
    cv2.imwrite(fp, frame)
    cap.release()
    cv2.destroyAllWindows()

    # ask Gemini what it sees
    image = upload_to_gemini(fp, mime_type="image/png")
    generation_config = {
        "temperature": 0.5,
        "top_p": 0.95,
        "max_output_tokens": 100,
        "response_mime_type": "text/plain",
    }
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
    chat_session = model.start_chat()

    response = chat_session.send_message(
        {
            "role": "user",
            "parts": [
                image,
                "Here is a picture of a musical instrument. in one or two words, without punctuation, identify what musical instrument this might be. If you aren't sure, return the name of a random, fun instrument.",
            ],
        }
    )
    return response.text.strip()


# init a synthesizer based on the identified instrument
def create_instrument(name: str):
    try:
        inst = s.new_part(name)
        print("found matching preset instrument")
        return inst
    except:
        print("unrecognized instrument, returning music box!")
        inst = s.new_part("music box")
        return inst


# ask gemini to identify the number of playable notes in the drawing of the instrument
def create_instrument_range():
    fp = "framecapture/webcam_instrument.jpg"
    image = upload_to_gemini(fp, mime_type="image/png")

    generation_config = {
        "temperature": 0.5,
        "top_p": 0.95,
        "max_output_tokens": 100,
        "response_mime_type": "text/plain",
    }
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
    chat_session = model.start_chat()

    response = chat_session.send_message(
        {
            "role": "user",
            "parts": [
                image,
                "Identify the range of playable notes for this instrument. Even if the drawing doesn't look like an instrument, treat it like it is, in fact, an instrument. The range of POSSIBLE notes can be from C4 to C7, C4 being the lowest, C7 the highest- but you don't have to include every note in the range- start at C4 and see how far you get. Every part of the instrument - like one key, one fret, one shape - should represent exactly one note. Don't create more than 10 notes. Always include sharps: for instance, F# should always follow F. Don't include flats- for instance, return F# but don't return Gb. Examples: if you see a piano, return the notes for both the black and white keys. If you see the strings of an instrument, return not just the list of open strings, but the notes that can be played on each string. If you see something that doesn't look like an instrument, return a list of notes anyway, that could map to the parts of the image. Output: Return the notes as a list of comma separated notes. Return nothing else except that list of notes.",
            ],
        }
    )
    # post process, convert to list of strings
    output = response.text.split(", ")
    output = [x.strip() for x in output]
    print("🎼 gemini identified the range: {}".format(output))
    return output


def test_range(inst, inst_range):
    for r in inst_range:
        if r in nm:
            # play_note(note, volume, duration_beats)
            inst.play_note(nm[r], 1, 0.4)
        else:
            print("⚠️ unrecognized note {}, skipping".format(r))


# given a frame where the user is pointing at a note on the instrument,
# ask Gemini to identifty what note they're playing, then have the synth play it.
def identify_and_play_note(inst, inst_id, inst_range, filepath):
    print("Identifying: {}".format(filepath))
    image = upload_to_gemini(filepath, mime_type="image/png")
    generation_config = {
        "temperature": 0.7,
        "top_p": 0.95,
        "max_output_tokens": 20,
        "response_mime_type": "text/plain",
    }
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        generation_config=generation_config,
    )
    chat_session = model.start_chat()

    prompt = "I am playing this instrument: {}. I am playing one note on this instrument by placing a green square around the note. Play the note representing the spot I'm pointing at. The range of possible notes are (from lowest, to highest): {}. Given that specific range, return the value of note I am pointing to. Return a single note in a format like this: C4. If you aren't sure, or if there's no hand in the picture pointing at something, say Not Sure.".format(
        inst_id, inst_range
    )

    response = chat_session.send_message(
        {
            "role": "user",
            "parts": [
                image,
                prompt,
            ],
        }
    )
    note_id = response.text
    # strip all whitespace and punctuation from string
    note_id = note_id.strip().replace(" ", "").replace(",", "").replace(".", "")
    print("Gemini sees: {}".format(note_id))
    if note_id in ["C", "D", "E", "F", "G", "A", "B"]:
        note_id += "4"
    if note_id in nm:
        inst.play_note(nm[note_id], 1, 2)
    else:
        print("🤔 unrecognized note {}, playing silence".format(response.text))


def papermusic():
    print(
        """
🎹 🎹 🎹 🎹 🎹 🎹 🎹 🎹 🎹 🎹 
┌─┐┌─┐┌─┐┌─┐┬─┐┌┬┐┌┐┌┬ ┬┌─┐┬┌─┐
├─┘├─┤├─┘├┤ ├┬┘│││││││ │└─┐││  
┴  ┴ ┴┴  └─┘┴└─┴ ┴┘└┘└─┘└─┘┴└─┘
 ✏️  ✏️  ✏️  ✏️  ✏️  ✏️  ✏️  ✏️  ✏️  ✏️
          """
    )

    print("👀 Identifying the instrument...")
    inst_id = identify_instrument()

    print("🔮 Gemini sees: {}. Initializing synthesizer...".format(inst_id))
    inst = create_instrument(inst_id)
    inst_range = create_instrument_range()

    # print("🔊 Your instrument can play these notes...")
    # test_range(inst, inst_range)

    print("🎵 Now play!")
    try:
        while True:
            cap = cv2.VideoCapture(0)
            count = 0
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            while cap.isOpened():
                ret, frame = cap.read()
                if ret:
                    # capture 1 frame every 500 ms
                    if count % (fps // 2) == 0:
                        fp = "framecapture/{}.jpg".format(time.time())
                        cv2.imwrite(fp, frame)
                        identify_and_play_note(inst, inst_id, inst_range, fp)
                    count += 1
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
                else:
                    break
    except KeyboardInterrupt:
        print("👋 Quitting...")
        cap.release()
        cv2.destroyAllWindows()
        # clean up webcam image files
        files = os.listdir("framecapture")
        for f in files:
            if f != "README.md":
                os.remove("framecapture/" + f)


if __name__ == "__main__":
    papermusic()
