FROM python:3.10-slim
workdir /app
copy app.py .
copy requirements.txt .
run mkdir templates
copy index.html templates
run pip install -r requirements.txt
expose 5000
entrypoint python app.py
