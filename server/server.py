from fastapi import FastAPI
from PIL import Image
from pydantic import BaseModel
from swarms import BaseMultiModalModel
from transformers import BitsAndBytesConfig
from transformers import PaliGemmaForConditionalGeneration, AutoProcessor
import asyncio
import cv2
import numpy as np
import os
import signal
import socket
import struct
import sys
import torch


app = FastAPI()


# prepare to receive mac webcam stream
host = "0.0.0.0"
port = 5000
max_length = 10000

# verify CUDA (Nvidia GPU) is available
if not torch.cuda.is_available():
    print("🚫 No CUDA device available.")
    sys.exit()


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

# -------------- SERVER FUNCTIONS  ---------------------------


@app.get("/")
def index():
    return {"response": "this is the papermusic note-player server"}


@app.get("/health")
def health():
    return {"status": "ok"}


# returns cur instrument name
@app.get("/instrument")
def instrument():
    print("\nENTER /GET INSTRUMENT")

    # get the img_path of the OLDEST frame file in framecapture/
    # (this is the first frame of the stream)
    img_path = "framecapture/" + sorted(os.listdir("framecapture"))[0]

    instrument = inference_paligemma(
        "Identify the musical instrument using 1-2 words", img_path
    )
    return {"instrument": instrument}


# returns cur note name
@app.get("/note")
def note():
    print("\nENTER GET /NOTE")

    # get the img_path of the LATEST frame file in framecapture/
    # (this is the most recent frame of the stream)
    img_path = "framecapture/" + sorted(os.listdir("framecapture"))[-1]

    n = inference_paligemma(
        "Identify the musical note inside the green square, for example: C5 or B6. Return only the name of the note.",
        img_path,
    )

    return {"note": n}


# ------------- PALIGEMMA HELPER FUNCTION ---------------------------


# source:
# https://medium.com/@kyeg/get-started-with-paligemma-locally-on-cloud-the-all-new-multi-modal-model-from-google-f88a97b9ead6
def inference_paligemma(prompt, img_path):
    raw_image = Image.open(img_path)
    inputs = processor(prompt, raw_image, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=50)
    return processor.decode(output[0], skip_special_tokens=True)[len(prompt) :]


async def listen():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(1)

    print("🤔 Listening for stream {}:{}...".format(host, port))

    conn, addr = sock.accept()
    print("✅ Connection from: ", addr)

    j = 0
    while True:
        try:
            # receive size of the frame
            buffer_size = conn.recv(4)
            buffer_size = struct.unpack("!I", buffer_size)[0]

            # receive the frame
            buffer = b""
            while len(buffer) < buffer_size:
                packet = conn.recv(buffer_size - len(buffer))
                if not packet:
                    break
                buffer += packet

            frame = np.frombuffer(buffer, dtype=np.uint8)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            frame = cv2.flip(frame, 1)

            if frame is not None and type(frame) == np.ndarray:
                if cv2.waitKey(1) == 27:
                    break
                # if j is a multiple of 10, save frame
                if j % 10 == 0:
                    cv2.imwrite(f"framecapture/frame_{j}.jpg", frame)
                    print("📸 Saved frame: framecapture/frame_{}.jpg".format(j))
                j += 1

        except Exception as e:
            print(e)
            continue


loop = None  # global variable to store the event loop


@app.on_event("startup")
async def startup_event():
    global loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(listen())


@app.on_event("shutdown")
async def shutdown_event():
    global loop
    print("👋 Quitting server...")
    # for file in os.listdir("framecapture"):
    #   os.remove(f"framecapture/{file}")
    loop.stop()
