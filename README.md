# better-tiss-calendar

![Screenshot](screenshot.png)
TISS is the information service of TU Wien which exports a suboptimal calendar 
of events (like lectures). This project improves the calendar by rewriting the
events and enriching them with useful information.

[Live Website](https://bettercal.flofriday.dev)

## Features

- Remove lecture number from the title
- Use shorthands instead of the long name (optional)
- Correct address in the location field, not just the room
- Floor information
- Links to TISS and TUW-Maps on HTML enabled clients
- Drop in replacement
- Easy setup: no login, no account and no rage inducing captchas
- Self-hosting friendly 

## How it works

Calendar clients download subscribed calendars periodically (some even let you 
set the polling rate). Instead so when a request comes in for a calendar this 
server downloads the original calendar from tiss and formats all events and 
enriches them with more information before returning it to the client.

## Build it yourself

You first need to install python3.11 and node.

```bash
npm install
npx tailwindcss -i app/templates/template.css -o app/static/style.css
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

You can run all tests with:

```bash
python -m pytest
```

## Build with Docker

```bash
docker build -t bettercal .
docker run -it --rm -p 5000:5000 bettercal
```

The server should now start at http://localhost:5000

This approach can be used in production. However, statistics will die with the 
container, but they can be preserved by adding the 
`--mount type=bind,source="$(pwd)"/bettercal.db,target=/app/bettercal.db` argument to the 
`docker run` command.

## How we deploy 

In production we use the [gunicorn](https://gunicorn.org/) server.
The main branch is automatically deployed as a systemd user service on a linux 
box. The systemd config can be read in `bettercal.service`.

## Contributing

Contributions are quite welcome, you are awesome. 😊🎉

If you want to add a shorthand for a lecture, the file you need to edit is 
`ressources/shorthands.csv`.