FROM python:3
COPY ./ ./
RUN pip3 install -r raspberry/requirements.txt
EXPOSE 8080
WORKDIR raspberry
CMD ["python3", "-u",  "./main.py"]
