FROM python:3
COPY ./ /code
WORKDIR /code/externalweatherapi
RUN pip3 install -r requirements.txt
CMD ["python3", "-u", "main.py"]
