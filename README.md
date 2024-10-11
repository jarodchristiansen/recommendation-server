# Deploy FastAPI on Render

Use this repo as a template to deploy a Python [FastAPI](https://fastapi.tiangolo.com) service on Render.

See https://render.com/docs/deploy-fastapi or follow the steps below:

## Recommendation Engine Exploration using Spotif Tracks

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/render-examples/fastapi)

to run the app locally, setup a virtual env and activate it. From there you can pip install from the requirements.txt file, and run `uvicorn main:app --host 0.0.0.0 --port $PORT` to start the app

### Running Unit Tests:

note `conftest.py` in `tests` directory to manage the directory structure of main.py being outside of app directory

after activating venv go to root directory and run:

`pytest` to run all available tests in `tests` directory

`pytest --cov=app` to run coverage report of the app structure
