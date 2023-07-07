FROM ubuntu:latest
FROM python:3.9-slim-buster

COPY . /bot
WORKDIR /bot

RUN pip install music21
RUN pip install mido
RUN pip install pychord
RUN pip install pyTelegramBotAPI
RUN pip install python-dotenv

CMD ["python3","bot.py"]