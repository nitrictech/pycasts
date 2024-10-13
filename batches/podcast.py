from common.resources import model_dir, zip_path, gen_audio_job, clips_bucket, models_bucket
from nitric.context import JobContext
from nitric.application import Nitric
from transformers import AutoProcessor, BarkModel

import scipy
import io
import torch
import numpy as np
import requests
import zipfile
import os

clips = clips_bucket.allow("write")
models = models_bucket.allow('read', 'write')

# This defines the Job Handler that will process all audio generation jobs
# using the job definition we created in the resources module
@gen_audio_job(cpus=4, memory=12000, gpus=1)
async def do_generate_audio(ctx: JobContext):
    file = ctx.req.data["file"]
    voice_preset = ctx.req.data["preset"]
    text: str = ctx.req.data["text"]
    model_id = ctx.req.data["model_id"]

    # Copy model from nitric bucket to local storage
    if not os.path.exists(model_dir):
        print("Downloading model")
        download_url = await models.file(f"{model_id}.zip").download_url()
        response = requests.get(download_url, allow_redirects=True, timeout=600)
        
        # make sure zip_path exists
        os.makedirs(os.path.dirname(zip_path), exist_ok=True)
        # save the zip file
        with open(zip_path, "wb") as f:
            f.write(response.content)
        print("Unzipping model")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(model_dir)

        # cleanup zip file
        print("Cleaning up")
        os.remove(zip_path)

    print("Loading model")
    model = BarkModel.from_pretrained(f"{model_dir}")
    processor = AutoProcessor.from_pretrained(f"{model_dir}")
    print("Model loaded")

    print(f'Using voice preset {voice_preset}')

    # Split the text by sentences and chain the audio clips together
    sentences = text.split(".")
    sentences = [sentence for sentence in sentences if sentence.strip() != ""]

    audio_arrays = []
    # for each sentence, generate the audio clip
    for index, sentence in enumerate(sentences):
        # Insert pauses between sentences to prevent clips from running together
        inputs = processor(f"{sentence}...", voice_preset=voice_preset)

        if torch.cuda.is_available():
            inputs.to("cuda")
            model.to("cuda")
        else:
            print("CUDA unavailable, defaulting to CPU. This may take a while.")

        print(f"Generating clip {index + 1}/{len(sentences)}")
        audio_array = model.generate(**inputs, pad_token_id=0)
        audio_array = audio_array.cpu().numpy().squeeze()

        audio_arrays.append(audio_array)

    final_array = np.concatenate(audio_arrays)

    buffer = io.BytesIO()
    print("Encoding clip")
    sample_rate = model.generation_config.sample_rate
    scipy.io.wavfile.write(buffer, rate=sample_rate, data=final_array)

    print("Uploading clip")
    upload_url = await clips.file(f'{file}.wav').upload_url()

    # make a put request to the upload url
    # with the buffer as the body
    # and the content type as audio/wav
    requests.put(upload_url, data=buffer.getvalue(), headers={"Content-Type": "audio/wav"}, timeout=600)

    print("Done!")

Nitric.run()