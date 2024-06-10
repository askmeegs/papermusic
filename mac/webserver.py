# while streaming webcam over UDP to GCE, receive the GCE server's response
# (note identification) so it can be played over local mac's audio.
import os
from fastapi import FastAPI
from pydantic import BaseModel
import requests

app = FastAPI()


class Note(BaseModel):
    id: str


# ------------- HEALTH --------------------------
@app.get("/")
def index():
    return {"response": "🗺️ hello, this is the whereami backend!"}


@app.get("/health")
def health():
    return {"status": "ok"}


# ------------- HANDLE PLAYED NOTES --------------------------
@app.post("/note")
def playnote(n: Note):
    