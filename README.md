# Beer Benches Seating

A small web app for generating pretix-compatible seating plans for Oktoberfest-style beer benches. It keeps pairs on opposite benches, provides a live SVG preview and exports the JSON accepted by the [pretix seating-plan editor](https://seats.pretix.eu).

## Run locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Open `http://localhost:8000`, adjust the layout and click **Download pretix JSON**.

The original command-line generator remains available:

```bash
python seating.py
```

It writes `seating.json` using the default configuration.

## Test

```bash
pytest -q
```

## Container

```bash
docker build -t beer-benches-seating .
docker run --rm -p 8000:8000 beer-benches-seating
```

## CI/CD and production deployment

GitLab CI tests the app and publishes an immutable container image for every commit. On `main`, the tagged `appvm` shell runner on `ml-apps` deploys the image automatically with Docker Compose and Traefik to `https://beer-benches-seating.ml-events.eu`.

The deployment follows the established `ml-site-astro` pattern: the runner already has Docker access, logs into the GitLab registry using the standard CI credentials and runs the Compose file from the checked-out repository. No SSH keys, server addresses or project-specific CI variables are required. The Docker host must provide the external `traefik` network.
