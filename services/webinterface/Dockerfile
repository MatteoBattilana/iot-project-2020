FROM python:3
COPY ./ ./
RUN pip3 install -r webinterface/requirements.txt
EXPOSE 80
WORKDIR webinterface
CMD ["python3", "-u", "./main.py"]
