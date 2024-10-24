from nitric.resources import api, bucket, job, topic
import os
import tempfile
# Our main API for submitting audio generation jobs
main_api = api("main")
# A job for generating our audio content
gen_audio_job = job("audio")
# A job for generating our audio script
gen_podcast_job = job("podcast")

# A bucket for storing output audio clips
clips_bucket = bucket("clips")
scripts_bucket = bucket("scripts")
# And another bucket for storing our models
models_bucket = bucket("models")

# Many cloud API Gateways impose hard response time limits on synchronous requests.
# To avoid these limits, we can use a Pub/Sub topic to trigger asynchronous processing.
download_audio_model_topic = topic("download-audio-model")

model_dir = os.path.join(tempfile.gettempdir(), "ai-podcast", ".model")
cache_dir = os.path.join(tempfile.gettempdir(), "ai-podcast", ".cache")
zip_path = os.path.join(tempfile.gettempdir(), "ai-podcast", "model.zip")