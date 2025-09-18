FROM python:3.10-slim

WORKDIR /app
COPY . /app   
# copies everything inside Frontend/ into /app

RUN pip install --no-cache-dir streamlit requests

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]

