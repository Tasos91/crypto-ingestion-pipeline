FROM python:3.9-slim

WORKDIR /app

# Εγκατάσταση όλων των βιβλιοθηκών και για τα δύο scripts
RUN pip install flask minio urllib3 websocket-client requests pika

# Αντιγραφή όλων των αρχείων στο container
COPY . /app