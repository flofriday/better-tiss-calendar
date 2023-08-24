FROM node:latest as tailwindbuild
WORKDIR /app
COPY . .
RUN npm install
RUN npx tailwindcss -i app/templates/template.css -o app/static/style.css

FROM python:latest as pythonbuild
WORKDIR /app
COPY --from=tailwindbuild /app .
RUN pip install -r requirements.txt

ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
