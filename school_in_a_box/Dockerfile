FROM python:3.9.5-slim-buster
WORKDIR /app
COPY . /app

RUN apt update -y && apt install awscli -y

RUN pip install --default-timeout=100 -i https://pypi.python.org/simple -r requirements.txt
CMD ["python3", "app.py"]
