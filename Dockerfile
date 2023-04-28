FROM python:3

WORKDIR /app

COPY . .

RUN pip install croniter

RUN pip install pymongo && \
pip install discord_webhook

CMD cron && echo "*/5 * * * * * root python /app/watch_dog.py" | crontab - \
    && tail -f /var/log/cron.log
