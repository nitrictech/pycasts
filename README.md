## Pycasts

Pycasts is a reference API for producing long form spoken audio and scripts for podcasts, powered by [Nitric](https://github.com/nitrictech/nitric), [Suno Bark](https://huggingface.co/suno/bark) and [Llama 3.2](https://www.llama.com/). 

Here's a sample of what can be produced with this project:

[power-rangers.webm](https://github.com/user-attachments/assets/bcb03055-c5d6-4883-8d0f-45fdf45191ca)

## Running locally

First off install project dependencies:

```bash
uv sync --all-extras
```

This project uses also uses smaller LLMs for producing podcast scripts, which is baked directly into the resulting container when we deploy, via the `models` directory of the project.

This can be populated by downloading an appropriately sized and quantized Llama 3.2 model. As an example:

```bash
mkdir models
curl -L https://huggingface.co/bartowski/Llama-3.2-3B-Instruct-GGUF/resolve/main/Llama-3.2-3B-Instruct-Q4_K_L.gguf -o models/Llama-3.2-3B-Instruct-Q4_K_L.gguf
```

The project can be then run locally by installing the [Nitric CLI](https://nitric.io/docs/get-started/installation). And running
```bash
nitric start
```

This will start the project on your local machine, and you will be able to use the provided local [nitric dashboard](https://localhost:49152), or your HTTP client of choice to interact with the API.

Audio models are downloaded ahead of time using the API to be stored locally in a bucket, this can be done by hitting the `/download-model` endpoint:

```bash
curl -X POST http://localhost:4001/download-model
```
> Assuming your API is hosted on 4001 (check your CLI output for `nitric start`).

## Deploying this project

Nitric provides detailed and intuitive [documentation](https://nitric.io/docs) and [guides](https://nitric.io/docs/getting-started) to help you get started quickly.

If you'd rather chat with the maintainers or community, come and join our [Discord](https://nitric.io/chat) server, [GitHub Discussions](https://github.com/nitrictech/nitric/discussions) or find us on [X](https://x.com/nitric_io).

A reference for deploying to AWS is provided along with the project under `nitric.aws.yaml`. 

## Possible project extensions

- [ ] Remove API endpoints and make podcasts on a schedule
- [ ] Use different voice models
- [ ] Add support for multiple speakers



