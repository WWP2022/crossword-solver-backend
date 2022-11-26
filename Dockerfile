FROM python:3.10

WORKDIR /app
COPY . .

RUN pip3 install -r requirements.txt

RUN apt-get update\
    && apt-get install tesseract-ocr-pol -y \
    && apt install libtesseract-dev -y \
    && apt-get install libgl1 -y

WORKDIR /app

CMD ["python", "-u", "main.py"]
