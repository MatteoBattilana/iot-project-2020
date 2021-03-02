FROM python:3
COPY ./ ./
RUN pip3 install -r webpage/requirements.txt
EXPOSE 80
WORKDIR webpage
CMD ["python3", "-u", "./main.py"]
