from common.resources import main_api, model_dir, cache_dir, zip_path, gen_podcast_job, download_audio_model_topic, models_bucket
from nitric.application import Nitric
from nitric.context import HttpContext, MessageContext
from huggingface_hub import snapshot_download
import os
import zipfile
import requests

models = models_bucket.allow('write')
generate_podcast = gen_podcast_job.allow('submit')
download_audio_model = download_audio_model_topic.allow("publish")

audio_model_id = "suno/bark"
default_voice_preset = "v2/en_speaker_6"

@download_audio_model_topic.subscribe()
async def do_download_audio_model(ctx: MessageContext):
    model_id: str = ctx.req.data["model_id"]

    print(f"Downloading model to {model_dir}")
    dir = snapshot_download(model_id, local_dir=model_dir, cache_dir=cache_dir, allow_patterns=[
        "config.json",
        "generation_config.json",
        "pytorch_model.bin",
        "speaker_embeddings_path.json",
        "special_tokens_map.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.txt"
    ])

    print(f"Downloaded model to {dir}")

    # zip the model and upload it to the bucket
    print("Compressing models")

    # zip the model
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zip_file:
        for root, dirs, files in os.walk(dir):
            for file in files:
                file_path = os.path.join(root, file)
                archive_name = os.path.relpath(file_path, start=dir)
                print(f"Adding {file_path} to zip as {archive_name}")
                zip_file.write(file_path, archive_name)

    # upload the model to the bucket
    module_url = await models.file(f"{model_id}.zip").upload_url()

    with open(zip_path, "rb") as f:
        requests.put(module_url, data=f, timeout=6000)

    os.remove(zip_path)
    
    print("Successfully cached model in bucket")


@main_api.post("/download-model")
async def download_audio(ctx: HttpContext):
    model_id = ctx.req.query.get("model", audio_model_id)\
    
    if isinstance(model_id, list):
        model_id = model_id[0]
    # asynchronously download the model
    await download_audio_model.publish({ "model_id": model_id })

# Generate a text-to-speech audio clip
# Generate a sample voice line
@main_api.post("/podcast/:filename")
async def submit_auto(ctx: HttpContext):
    name = ctx.req.params["filename"]
    model_id = ctx.req.query.get("model", audio_model_id)
    preset = ctx.req.query.get("preset", default_voice_preset)

    if isinstance(model_id, list):
        model_id = model_id[0]

    if isinstance(preset, list):
        preset = preset[0]

    body = ctx.req.data
    if body is None:
        ctx.res.status = 400
        return

    print(f"using preset {preset}")

    await generate_podcast.submit({"file": name, "prompt": body.decode('utf-8')})

Nitric.run()