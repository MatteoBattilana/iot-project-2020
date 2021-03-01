FROM python:3
COPY ./ ./
RUN pip3 install -r thinkspeakadaptor/requirements.txt
EXPOSE 8080
WORKDIR thinkspeakadaptor
CMD ["python3", "-u",  "./main.py"]
