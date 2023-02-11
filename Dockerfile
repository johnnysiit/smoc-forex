FROM python:3


RUN pip3 install requests matplotlib pandas yfinance
RUN mkdir app
ADD main.py /app/
#ADD diff_direction.config /app
#ADD both_direction.config /app
COPY forex.cronjob /etc/cron.d/forex.cronjob
ENV PATH "$PATH:/path/to/chromedriver"
RUN apt-get update 
RUN apt-get install -y cron 
RUN chmod 0644 /etc/cron.d/forex.cronjob 
RUN crontab /etc/cron.d/forex.cronjob
RUN touch /var/log/cron.log
CMD cron && tail -f /var/log/cron.log