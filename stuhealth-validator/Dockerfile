FROM python:latest
LABEL maintainer="samlangten@outlook.com"
COPY . /app/stuhealth-validator
WORKDIR /app/stuhealth-validator
ENV STUHEALTH_VALIDATOR_WEBDRIVER_URL="http://127.0.0.1:4444"
ENV STUHEALTH_VALIDATOR_LISTEN_HOST="127.0.0.1"
ENV STUHEALTH_VALIDATOR_LISTEN_PORT=6666
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "main.py"]