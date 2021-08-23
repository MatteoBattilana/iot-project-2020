FROM python:3
COPY ./ /code
WORKDIR /code/telegram-bot
RUN pip3 install -r requirements.txt
CMD ["python3", "-u", "telegram.py"]
