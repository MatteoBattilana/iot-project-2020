FROM python:3
COPY ./ ./
RUN pip3 install -r simulateddevice/requirements.txt
EXPOSE 8080
WORKDIR simulateddevice
CMD ["python3", "-u",  "./main.py"]
