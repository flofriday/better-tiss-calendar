# better-tiss-calendar

![Screenshot](screenshot.png)
A better tiss calendar

[Live Website](https://bettercal.flofriday.dev/)

## Build it yourself

You first need to install python3.11 and node.

```bash
npm install
npx tailwindcss -i templates/template.css -o static/style.css
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --debug
```

The server should now start at http://localhost:5000

**Note:** While working on the frontend, it is quite handy to add the `--watch` 
flag to the tailwind command.

**Warning:** The flask server here cannot be used in production and is optimized
for development comfort.

## How we deploy 

In production we use the [gunicorn](https://gunicorn.org/) server.
The service is deployed as a systemd user service on a linux box, which is 
described in `bettercal.service`.