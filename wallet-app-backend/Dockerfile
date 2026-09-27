# ---------- stage 1: build the frontend ----------
FROM node:20-alpine AS frontend
WORKDIR /frontend
COPY wallet-app-frontend/package.json wallet-app-frontend/package-lock.json ./
RUN npm ci
COPY wallet-app-frontend/ ./
RUN npm run build

# ---------- stage 2: python runtime serving API + built SPA ----------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY wallet-app-backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY wallet-app-backend/ ./
COPY --from=frontend /frontend/dist ./static_frontend

EXPOSE 8000

# Apply migrations, make sure demo data exists, then serve the API and the SPA.
CMD ["sh", "-c", "flask db upgrade && flask seed-demo && gunicorn app:app --bind 0.0.0.0:${PORT:-8000} --workers 2 --timeout 60"]
