FROM node:24-trixie-slim AS tailwindbuild
WORKDIR /app
COPY . .
RUN npm install
RUN npx @tailwindcss/cli -i app/templates/template.css -o app/static/style.css

FROM python:3.13-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY --from=tailwindbuild /app .
RUN uv sync

ENTRYPOINT ["uv", "run", "--", "gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
