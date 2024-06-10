# 🎵 papermusic ✏️

draw an instrument, and play it! (fun with [PaliGemma](https://ai.google.dev/gemma/docs/paligemma) and [SCAMP](http://scamp.marcevanstein.com/))

![](images/screenshot.png)  


## v2 - Cloud Workstation (w/ Nvidia GPUs), + "local" Paligemma, + "actually local" webcam streamed via VLC 

https://docs.opencv.org/3.0-beta/doc/py_tutorials/py_gui/py_video_display/py_video_display.html

```
ffmpeg -i udp://127.0.0.1:8000 -c copy output.mp4
```

--------

**[📹 Video walkthrough]()**

### 🖥️ how to run 

*Note: this is a prototype. It has only been tested on a Debian Linux machine with Nvidia L4 GPUs (CUDA). Apple Silicon GPUs are not yet supported.*

**Prerequisites**: 
- A HuggingFace account 
- Python 3.12+ 
- A webcam

1. Clone repository: 

```
git clone https://github.com/askmeegs/papermusic 
```

2. Log into HuggingFace. 

3. [Request access to PaliGemma](https://huggingface.co/google/paligemma-3b-mix-224). Accept the terms for the model. When authorized, the HuggingFace model card will say: `You have been granted access to this model`. 

4. Getting a HuggingFace API key for your account. Go to [User Settings](https://huggingface.co/settings/profile) > Access Tokens. Create a `READ` key. Copy the value of your key. 

5. In your terminal, create an environment variable for your HuggingFace API key: 

```
export HUGGINGFACE_USER_ACCESS_TOKEN="your-key" 
```

6. Navigate to the `src/` directory. 

```
cd src/
```

7. Initialize a python virtualenv, and 

### 📚 sources

- [PaliGemma](https://huggingface.co/google/paligemma-3b-pt-224?library=transformers) (vision-language model)
- [Tutorial - Gemma on M1 Mac (Manyi, Medium)](https://medium.com/@manyi.yim/running-google-gemma-on-mac-m1-gpu-a-step-by-step-guide-and-explanation-b03dc9279a7b)
- [Tutorial - PaliGemma (Kye Gomez, Medium)](https://medium.com/@kyeg/get-started-with-paligemma-locally-on-cloud-the-all-new-multi-modal-model-from-google-f88a97b9ead6)
- [HuggingFace Transformers](https://huggingface.co/docs/transformers/index)
- [HuggingFace Inference Optimization](https://huggingface.co/docs/transformers/main/en/llm_optims)
- [SCAMP (Suite for Computer-Assisted Music in Python)](http://scamp.marcevanstein.com/)
- [ASCII Art Generator](https://patorjk.com/software/taag/#p=display&f=Graffiti&t=Type%20Something%20)
