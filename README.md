# better-tiss-calendar

![Screenshot](screenshot.png)
A better tiss calendar

[Live Website](https://bettercal.flofriday.dev)

## Features

- Remove lecture number from the title
- Use shorthands instead of the long name
- Correct address in the location field, not just the room
- Floor information
- Links to TISS and TUW-Maps on HTML enabled clients

## How it works

Calendar clients download subscribed calendars periodically (some even let you 
set the polling rate). Instead so when a request comes in for a calendar this 
server downloads the original calendar from tiss and formats all events and 
enriches them with more information before returning it to the client.

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
The main branch is automatically deployed as a systemd user service on a linux 
box. The systemd config can be read in `bettercal.service`.

## Contributing

Contributions are quite welcome, you are awesome. 😊🎉

If you want to add a shorthand for a lecture, the file you need to edit is 
`ressources/shorthands.csv`.