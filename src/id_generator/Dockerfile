### First stage
FROM alpine:3.23.3 AS base_build

ENV HOME="/root"

### Bash
RUN apk add bash

### Generic dependencies

RUN apk add --no-cache git bash build-base libffi-dev openssl-dev bzip2-dev zlib-dev readline-dev sqlite-dev
RUN apk add gcc make g++ zlib-dev
RUN apk add python3 py3-pip
RUN apk update

### Second stage
FROM alpine:3.23.3

### Set the data from base image to final image
COPY --from=base_build / /

### Set envs and workdirs
ENV HOME="/root"

WORKDIR $HOME

### Install
RUN python -m venv .venv_pipx
RUN .venv_pipx/bin/pip install --no-cache-dir pipx

RUN .venv_pipx/bin/pipx install poetry
RUN .venv_pipx/bin/pipx ensurepath

ENV PATH="/root/.local/bin:$PATH"

### Copy lock with exact python versions
COPY pyproject.toml .
COPY poetry.lock .
COPY id_generator.py .
COPY .env .
COPY dist/ dist/
COPY routes/ routes/

RUN python -m venv .venv

RUN poetry install

CMD [".venv/bin/start_id_generator", "postgres"]
