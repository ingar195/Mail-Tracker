FROM python:3.11

WORKDIR /app
RUN mkdir files

COPY alert.py .
COPY files files
COPY requirements.txt .
COPY static static
COPY templates templates
COPY tracker.py .
COPY start.py .

RUN chmod 777 -R files

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 1234
VOLUME ["/app/files"]


CMD ["python", "start.py"]
