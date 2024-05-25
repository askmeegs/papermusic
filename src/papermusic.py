import cv2
from scamp import *
import os
import google.generativeai as genai

genai.configure(api_key=os.environ["GEMINI_API_KEY"])


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


def upload_to_gemini(path, mime_type=None):
    file = genai.upload_file(path, mime_type=mime_type)
    print(f"Uploaded file '{file.display_name}' as: {file.uri}")
    return file


# given a drawing of a musical instrument, ask Gemini to identify it
def identify_instrument():
    image = upload_to_gemini("instruments/test1.png", mime_type="image/png")
    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
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
                'here is a picture of a musical instrument. in one word, without punctuation, identify what musical instrument this might be. if you aren\'t sure, say "music box." ',
            ],
        }
    )
    print("🔮 gemini flash thinks the drawing is: " + response.text)
    return response.text, image


# ask gemini to identify the number of playable notes in the drawing of the instrument
def id_instrument_range(image):
    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
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
                "identify the playable notes for this instrument. The range of notes can be from C4 to C7, C4 being the lowest, C7 the highest. Include sharps, for instance, F# should always follow F. Return the notes as a list of comma separated notes. Return nothing else except that list. This is an example, but don't return this exact list: C4, D4, E4. Return the list of notes based on the image of the instrument.",
            ],
        }
    )
    # post process, convert to list of strings
    output = response.text.split(", ")
    print("🎼 gemini identified the range: {}".format(output))
    return output


def test_range(inst, inst_range):
    print("TESTING THE RANGE....")
    for r in inst_range:
        if r in nm:
            inst.play_note(nm[r], 0.8, 0.5)
        else:
            print("⚠️ unrecognized note {}, skipping".format(r))


def play_instrument(inst, inst_id, inst_range, filepath):
    image = upload_to_gemini(filepath, mime_type="image/png")
    generation_config = {
        "temperature": 0.3,
        "top_p": 0.95,
        "top_k": 64,
        "max_output_tokens": 8192,
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
                "the user is playing the instrument: {}. they are playing one note on this instrument. the range of possible notes are: {}. return the note they are most likely playing. return a single note in a format like this: C4".format(
                    inst_id, inst_range
                ),
            ],
        }
    )
    if response.text in nm:
        inst.play_note(nm[response.text], 0.8, 1)
    else:
        print("🎻 unrecognized note {}, skipping".format(response.text))


# init a synthesizer based on the identified instrument
def create_instrument(name: str):
    s = Session()
    try:
        inst = s.new_part(name)
        print("found matching preset instrument")
        return inst
    except:
        print("unrecognized instrument, returning music box!")
        inst = s.new_part("music box")
        return inst


def play(inst, notename):
    try:
        print("playing note: {}".format(notename))
        inst.play_note(nm[notename], 0.8, 0.5)
    except:
        print("⚠️ unrecognized note {}, skipping".format(notename))


def papermusic():
    # print multiline str
    print(
        """
        🎹  🎹      🎹    🎹  🎹  🎹  🎹      🎹    🎹  🎹
┌─┐┌─┐┌─┐┌─┐┬─┐┌┬┐┌┐┌┬ ┬┌─┐┬┌─┐
├─┘├─┤├─┘├┤ ├┬┘│││││││ │└─┐││  
┴  ┴ ┴┴  └─┘┴└─┴ ┴┘└┘└─┘└─┘┴└─┘
        ✏️  ✏️  ✏️   ✏️  ✏️  ✏️   ✏️  ✏️  ✏️
          """
    )
    inst_id, image = identify_instrument()
    inst = create_instrument(inst_id)
    inst_range = id_instrument_range(image)
    # test_range(inst, inst_range)

    play_instrument(inst, inst_id, inst_range, "notes/piano_note1.png")
    play_instrument(inst, inst_id, inst_range, "notes/piano_note2.png")
    play_instrument(inst, inst_id, inst_range, "notes/piano_note3.png")

    # inst.play_note(60, 0.8, 0.5)
    # inst.play_note(67, 0.8, 0.5)
    # inst.play_note(64, 0.8, 0.5)
    # cap = cv2.VideoCapture(0)  # 0 is the default webcam
    # count = 0
    # fps = int(cap.get(cv2.CAP_PROP_FPS))  # Get frames per second

    # while cap.isOpened():
    #     ret, frame = cap.read()
    #     if ret:
    #         if count % fps == 0:  # Capture frame every second
    #             cv2.imwrite("framecapture/{:d}.jpg".format(count // fps), frame)
    #  play_instrument
    #         count += 1
    #         if cv2.waitKey(1) & 0xFF == ord("q"):  # Press 'q' to quit
    #             break
    #     else:
    #         break

    # cap.release()
    # cv2.destroyAllWindows()


if __name__ == "__main__":
    papermusic()
