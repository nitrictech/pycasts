from common.resources import gen_podcast_job, gen_audio_job, scripts_bucket
from nitric.context import JobContext
from nitric.application import Nitric
from llama_cpp import Llama
import os

system_prompt = """You're a writer for the Dead Internet Podcast.
The podcast only has the host and no guests so the writing style is more like a speech than a script and should just be simple text with no queues or speaker names.
The host always starts with a brief introduction and then dives into the topic, and always finishes with a summary and a farewell.
"""

model = os.environ.get("LLAMA_MODEL", "./models/Llama-3.2-3B-Instruct-Q4_K_L.gguf")

llm = Llama(model_path=model, chat_format="llama-3", n_ctx=4096)
audio_job = gen_audio_job.allow("submit")
scripts = scripts_bucket.allow("write")

audio_model_id = "suno/bark"
default_voice_preset = "v2/en_speaker_6"

@gen_podcast_job(cpus=4, memory=12000)
async def do_gen_script(ctx: JobContext):
    prompt = ctx.req.data["prompt"]
    # TODO: Generate this from the LLM
    file = ctx.req.data["file"]

    print('generating script')

    completion = llm.create_chat_completion(
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user", 
                "content": prompt
            },
        ],
        max_tokens=-1,
        temperature=0.9,
    )

    text_response = completion["choices"][0]["message"]["content"]

    script_file = f'{file}.txt'

    await scripts.file(script_file).write(str.encode(text_response))

    print(f'script written to {script_file}')

        # send the script for generation
    await audio_job.submit({
        "text": text_response,
        "preset": default_voice_preset,
        "model_id": audio_model_id,
        "file": file,
    })

Nitric.run()