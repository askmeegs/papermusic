from fastapi import FastAPI
from PIL import Image
from transformers import BitsAndBytesConfig
from transformers import PaliGemmaForConditionalGeneration, AutoProcessor
import os
import glob
import sys
import time
import torch


app = FastAPI()

# verify CUDA (Nvidia GPU) is available
if not torch.cuda.is_available():
    print("🚫 No CUDA device available.")
    sys.exit()
else:
    print("✅ NVIDIA CUDA device available. Loading model...")


# load paligemma - quantized for performance optimization
hf_token = os.getenv("HUGGINGFACE_USER_ACCESS_TOKEN")
model_id = "google/paligemma-3b-mix-224"
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,  # 4 bit precision
    bnb_4bit_quant_type="nf4",
    bnb_4bit_compute_dtype=torch.bfloat16,  # computation datatype
)
model = PaliGemmaForConditionalGeneration.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map={"": 0},
    token=hf_token,
)
processor = AutoProcessor.from_pretrained(model_id, token=hf_token)
print("✅ PaliGemma model loaded.")
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
    # get the img_path of the OLDEST frame file in framecapture/
    # (this is the first frame of the stream)
    img_path = "framecapture/" + sorted(os.listdir("framecapture"))[0]

    instrument = inference_paligemma(
        "Identify the musical instrument using 1-2 words", img_path
    )

    # remove all whitespace and punctuation
    instrument = instrument.strip().replace(" ", "").replace(",", "").replace(".", "")
    print("🎹 Instrument is: {}".format(instrument))
    return {"instrument": instrument}


# returns cur note name
@app.get("/note")
def note():
    # get the most recently-streamed frame
    list_of_files = glob.glob("framecapture/*")
    img_path = max(list_of_files, key=os.path.getctime)

    print("\n PaliGemma reading frame: " + img_path)
    start_time = time.time()
    n = inference_paligemma(
        "Identify the musical note INSIDE the green rectangle, for example: C, D, E, F, G, A, or B. Return ONLY the name of the note.",
        img_path,
    )
    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Local inference in: {:.2f} seconds".format(elapsed_time))

    # remove all whitespace and punctuation
    n = n.strip().replace(" ", "").replace(",", "").replace(".", "")
    # convert to all caps
    n = n.upper()
    print("🎵 Identified: {}".format(n))
    return {"note": n}


# ------------- PALIGEMMA HELPER FUNCTION ---------------------------


# source:
# https://medium.com/@kyeg/get-started-with-paligemma-locally-on-cloud-the-all-new-multi-modal-model-from-google-f88a97b9ead6
def inference_paligemma(prompt, img_path):
    raw_image = Image.open(img_path)
    inputs = processor(prompt, raw_image, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=50)
    return processor.decode(output[0], skip_special_tokens=True)[len(prompt) :]
