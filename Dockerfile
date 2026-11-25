FROM python:3.11-slim
WORKDIR /app
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/base.txt -r requirements/m1.txt -r requirements/m3.txt
COPY src/ src/
COPY api/ api/
COPY models/ models/
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
