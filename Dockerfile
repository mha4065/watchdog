FROM python:3

WORKDIR /app

COPY . .

RUN pip install pymongo && \
pip install discord_webhook

CMD [ "python", "./watch_dog.py" ]

