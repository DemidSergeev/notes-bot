FROM python:3.13

COPY ./requirements.txt /app/
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENTRYPOINT ["python", "-m", "src.main"]