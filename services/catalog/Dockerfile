FROM python:3
COPY ./ ./
RUN pip3 install -r catalog/requirements.txt
EXPOSE 8080
WORKDIR catalog
CMD ["python3", "-u", "./main.py"]
