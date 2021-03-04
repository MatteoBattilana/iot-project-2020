FROM python:3
COPY ./ ./
RUN pip3 install -r externalweatherapi/requirements.txt
EXPOSE 8080
WORKDIR externalweatherapi
CMD ["python3", "-u", "./main.py"]
