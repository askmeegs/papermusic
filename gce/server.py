import cv2
import socket
import pickle
import numpy as np
import os
import signal
import sys
import time
import torch
from transformers import PaliGemmaForConditionalGeneration, AutoProcessor
from PIL import Image
from transformers import BitsAndBytesConfig
from swarms import BaseMultiModalModel
import requests
import json

# verify CUDA (Nvidia GPU) is available
if not torch.cuda.is_available():
    print("🚫 No CUDA device available.")
    sys.exit()

# configure server info to listen on websocket
host = "0.0.0.0"
port = 5000
max_length = 10000


def cleanup_and_exit(signal_number, frame):
    print("👋 Quitting server...")
    for file in os.listdir("framecapture"):
        os.remove(f"framecapture/{file}")
    sys.exit()


signal.signal(signal.SIGINT, cleanup_and_exit)


# load paligemma - quantized for performance optimization
# using local Nvidia GPU
hf_token = os.getenv("HUGGINGFACE_USER_ACCESS_TOKEN")
model_id = "google/paligemma-3b-mix-224"
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,
)
model = PaliGemmaForConditionalGeneration.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map={"": 0},
    token=hf_token,
)
processor = AutoProcessor.from_pretrained(model_id, token=hf_token)


# source:
# https://medium.com/@kyeg/get-started-with-paligemma-locally-on-cloud-the-all-new-multi-modal-model-from-google-f88a97b9ead6
def inference_paligemma(prompt, img_path):
    raw_image = Image.open(img_path)
    inputs = processor(prompt, raw_image, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=50)
    return processor.decode(output[0], skip_special_tokens=True)[len(prompt) :]


# runs in the first 5 seconds of stream-receive
def identify_instrument(img_path):
    instrument = inference_paligemma(
        "Identify the musical instrument using 1-2 words", img_path
    )
    url = "http://96.224.255.115:8000/note"
    headers = {"Content-Type": "application/json"}
    data = {"name": instrument}
    print("\n⬅️ Attempting to play note: ", n)
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(response.text)


# once instrument is ID-ed, play notes based on green square surrounding note on paper instrument
def play_note(img_path):
    n = inference_paligemma(
        "Identify the musical note inside the green square, for example: C5 or B6. Return only the name of the note.",
        img_path,
    )
    url = "http://96.224.255.115:8000/note"
    headers = {"Content-Type": "application/json"}
    data = {"id": n}
    print("\n⬅️ Attempting to play note: ", n)
    response = requests.post(url, headers=headers, data=json.dumps(data))
    print(response.text)


# for the first 5 seconds, listen for the instrument webcam frames ...
def listen_for_instrument():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    frame_info = None
    buffer = None
    frame = None
    first_receipt = False
    j = 0
    print("🎹 Listening UDP for instrument on {}:{}...".format(host, port))

    start_time = time.time()

    while True:
        try:
            data, address = sock.recvfrom(max_length)
            if len(data) < 100:
                frame_info = pickle.loads(data)
                if frame_info:
                    if first_receipt == False:
                        print("✅ Received stream.")
                        first_receipt = True
                    nums_of_packs = frame_info["packs"]
                    j += 1
                    for i in range(nums_of_packs):
                        data, address = sock.recvfrom(max_length)

                        if i == 0:
                            buffer = data
                        else:
                            buffer += data

                    frame = np.frombuffer(buffer, dtype=np.uint8)
                    frame = frame.reshape(frame.shape[0], 1)

                    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                    frame = cv2.flip(frame, 1)

                    if frame is not None and type(frame) == np.ndarray:
                        if cv2.waitKey(1) == 27:
                            break
                    # if i is a multiple of 10, save frame
                    if j % 10 == 0:
                        cv2.imwrite(f"framecapture/frame_{j}.jpg", frame)
                        resp = identify_instrument(f"framecapture/frame_{j}.jpg")
                        print(resp)
                        if "success" in resp:
                            print("🎹 Identified instrument: ", resp)
                            break

            # Break the loop after 5 seconds
            if time.time() - start_time > 5:
                print("⏲️ Instrument ID TIMEOUT")
                break

# then afterwards, listen for frames of notes being played, until quit
def listen_for_notes():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))

    frame_info = None
    buffer = None
    frame = None

    print("🤔 Listening on {}:{}, waiting for connection...".format(host, port))

    first_receipt = False
    j = 0
    while True:
        try:
            data, address = sock.recvfrom(max_length)
            if len(data) < 100:
                frame_info = pickle.loads(data)
                if frame_info:
                    if first_receipt == False:
                        print("✅ Received stream.")
                        first_receipt = True
                    nums_of_packs = frame_info["packs"]
                    j += 1
                    for i in range(nums_of_packs):
                        data, address = sock.recvfrom(max_length)

                        if i == 0:
                            buffer = data
                        else:
                            buffer += data

                    frame = np.frombuffer(buffer, dtype=np.uint8)
                    frame = frame.reshape(frame.shape[0], 1)

                    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                    frame = cv2.flip(frame, 1)

                    if frame is not None and type(frame) == np.ndarray:
                        # cv2.imshow("Stream", frame)
                        if cv2.waitKey(1) == 27:
                            break
                    # if i is a multiple of 10, save frame
                    if j % 10 == 0:
                        # print("🗳️ saving frame {}".format(j))
                        cv2.imwrite(f"framecapture/frame_{j}.jpg", frame) 
                        resp = play_note(f"framecapture/frame_{j}.jpg")
                        print(resp)
        except KeyboardInterrupt:
            cleanup_and_exit(None, None)


if __name__ == "__main__":
    # listen()
    for i in range(0, 50):
        s = time.time()
        res = inference_paligemma(
            "identify the musical instrument.", "framecapture/frame_40.jpg"
        )
        f = time.time()
        print(f"🔍 Identified instrument: {res} in {f-s} seconds")
