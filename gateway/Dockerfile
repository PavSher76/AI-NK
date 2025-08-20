FROM python:3.11-slim
WORKDIR /app
COPY gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY gateway/app.py app.py
RUN mkdir -p /app/ssl
COPY ssl/gateway.key /app/ssl/
COPY ssl/gateway.crt /app/ssl/
EXPOSE 8080 8443
CMD ["uvicorn","app:app","--host","0.0.0.0","--port","8443","--ssl-keyfile","/app/ssl/gateway.key","--ssl-certfile","/app/ssl/gateway.crt"]
