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
COPY start.py ./
ENV PORT=8000
ENV DEMO_API_KEY=cg_demo_costguard_2026
EXPOSE 8000
CMD python start.py
