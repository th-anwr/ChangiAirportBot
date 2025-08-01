FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app ./app
COPY ./data ./data
EXPOSE 8501
CMD ["streamlit", "run", "app/chatbot.py", "--server.port=8501", "--server.address=0.0.0.0"] 