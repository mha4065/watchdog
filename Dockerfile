FROM python:3

WORKDIR /app

COPY . .

RUN apt-get update && apt-get -y install cron

COPY crontab /etc/cron.d/crontab

RUN pip install pymongo && \
    pip install discord_webhook

RUN crontab crontab

CMD ["cron", "-f"]
