FROM python:3.9-slim-buster
WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .
CMD ["cat", "manage.py"]
CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]