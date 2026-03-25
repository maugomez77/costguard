FROM node:20-slim AS frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir -e .
COPY --from=frontend /app/frontend/dist ./frontend/dist
ENV PORT=8000
EXPOSE 8000
CMD uvicorn costguard.api:app --host 0.0.0.0 --port $PORT
