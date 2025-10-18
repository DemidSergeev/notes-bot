FROM python:3.13

COPY . /app
WORKDIR /app

RUN pip install --no-cache-dir -r requirements.txt
ENTRYPOINT ["python", "-m", "src.main"]