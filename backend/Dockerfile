FROM python:3.12-slim

WORKDIR /repo

COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

COPY ml/ ml/
COPY backend/ backend/
COPY data/ data/

ENV PYTHONPATH=/repo:/repo/backend
ENV APP_ENV=production
ENV DEMO_MODE=true
ENV PORT=8000

EXPOSE 8000
CMD ["python", "backend/app/main.py"]
