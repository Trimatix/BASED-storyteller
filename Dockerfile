FROM python:3

# Copy reqs in first to use docker build caching
COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && \
    rm -rf /tmp/requirements.txt

COPY . /app
WORKDIR /app
ENTRYPOINT ["python", "./main.py"]
