FROM python:3.10-slim

RUN apt-get update && apt-get install -y ffmpeg && apt-get clean

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 10000

CMD ["gunicorn", "--bind", "0.0.0.0:10000", "app:app"]
