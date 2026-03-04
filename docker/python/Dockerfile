FROM python:3.12

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt
RUN apt update -y && apt install -y ffmpeg fluidsynth
