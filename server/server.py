import cv2
import socket
import pickle
import numpy as np
import os
import signal
import sys

import torch
from transformers import PaliGemmaForConditionalGeneration, AutoProcessor
from PIL import Image
from transformers import BitsAndBytesConfig
from swarms import BaseMultiModalModel


# configure server info to listen on websocket
host = "0.0.0.0"
port = 5000
max_length = 10000


def cleanup_and_exit(signal_number, frame):
    print("👋 Quitting server...")
    # for file in os.listdir("framecapture"):
    #     os.remove(f"framecapture/{file}")
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
)
processor = AutoProcessor.from_pretrained(model_id)


# source:
# https://medium.com/@kyeg/get-started-with-paligemma-locally-on-cloud-the-all-new-multi-modal-model-from-google-f88a97b9ead6
def inference_paligemma(prompt, img_path):
    raw_image = Image.open(img_path)
    inputs = processor(prompt, raw_image, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=50)
    return processor.decode(output[0], skip_special_tokens=True)[len(prompt) :]


def listen():
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
        except KeyboardInterrupt:
            cleanup_and_exit(None, None)


if __name__ == "__main__":
    # listen()
    inference_paligemma("identify the musical instrument.", "framecapture/frame_40.jpg")
