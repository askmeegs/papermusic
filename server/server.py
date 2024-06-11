from fastapi import FastAPI
from PIL import Image
from pydantic import BaseModel
from swarms import BaseMultiModalModel
from transformers import BitsAndBytesConfig
from transformers import PaliGemmaForConditionalGeneration, AutoProcessor
import asyncio
import base64
import cv2
import imutils
import numpy as np
import os
import pickle
import signal
import socket
import socket
import sys
import time
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


# continuously write frames from UDP webcam stream to disk
# source: https://pyshine.com/Send-video-over-UDP-socket-in-Python/
async def listen():
    print("attempting to listen for webcam stream...")
    try:
        j = 1
        first_receipt = False
        BUFF_SIZE = 65536
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)
        host_ip = "35.231.102.158"
        port = 5000
        message = b"Hello"
        client_socket.sendto(message, (host_ip, port))
        fps, st, frames_to_count, cnt = (0, 0, 20, 0)
        while True:
            packet, _ = client_socket.recvfrom(BUFF_SIZE)
            data = base64.b64decode(packet, " /")
            npdata = np.fromstring(data, dtype=np.uint8)
            frame = cv2.imdecode(npdata, 1)
            if j % 10 == 0:
                cv2.imwrite(f"framecapture/frame_{j}.jpg", frame)
            j += 1
            if not first_receipt:
                print("✅ RECEIVED FIRST FRAME")
                first_receipt = True
            frame = cv2.putText(
                frame,
                "FPS: " + str(fps),
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

            # cv2.imshow("RECEIVING VIDEO", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                client_socket.close()
                break
            if cnt == frames_to_count:
                try:
                    fps = round(frames_to_count / (time.time() - st))
                    st = time.time()
                    cnt = 0
                except:
                    pass
        cnt += 1
    except Exception as e:
        if e == KeyboardInterrupt:
            print("Exiting...")
            cleanup_and_exit(None, None)
        else:
            print("🚫 Error: ", e)
            return


# async def listen():
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.bind((host, port))
#     sock.listen(1)

#     print("🤔 Listening for stream {}:{}...".format(host, port))

#     conn, addr = sock.accept()
#     print("✅ Connection from: ", addr)

#     j = 0
#     while True:
#         try:
#             # receive size of the frame
#             buffer_size = pickle.loads(conn.recv(1024))

#             # receive the frame
#             buffer = b""
#             while len(buffer) < buffer_size:
#                 packet = conn.recv(buffer_size - len(buffer))
#                 if not packet:
#                     break
#                 buffer += packet

#             frame = np.frombuffer(buffer, dtype=np.uint8)
#             frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
#             frame = cv2.flip(frame, 1)

#             if frame is not None and type(frame) == np.ndarray:
#                 if cv2.waitKey(1) == 27:
#                     break
#                 # if j is a multiple of 10, save frame
#                 if j % 10 == 0:
#                     cv2.imwrite(f"framecapture/frame_{j}.jpg", frame)
#                 j += 1

#         except Exception as e:
#             if e == KeyboardInterrupt:
#                 cleanup_and_exit(None, None)
#             else:
#                 print("🚫 Error: ", e)
#                 continue


def cleanup_and_exit(signal_number, frame):
    print("👋 Quitting server...")
    # for file in os.listdir("framecapture"):
    #   os.remove(f"framecapture/{file}")
    sys.exit()


signal.signal(signal.SIGINT, cleanup_and_exit)


@app.on_event("startup")
def init():
    asyncio.create_task(listen())
