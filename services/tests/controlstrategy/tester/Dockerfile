FROM python:3
COPY ./ /code
WORKDIR /code/tester
RUN pip3 install -r requirements.txt
CMD ["python3", "-u", "test.py"]
