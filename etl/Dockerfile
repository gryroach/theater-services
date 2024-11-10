FROM python:3.11

WORKDIR /app
COPY . .

RUN pip install --upgrade pip && pip install -r requirements.txt --no-cache-dir
CMD ["python", "main.py"]