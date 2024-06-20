from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware
from dash_app import create_dash_app
import transform

# run this in terminal: uvicorn main:app --reload
# paste this into the browser: http://127.0.0.1:8000/dash/

app = FastAPI()

# Create Dash app
dash_app = create_dash_app()

app.mount("/dash", WSGIMiddleware(dash_app.server))

@app.get("/")
def read_root():
    return {"message": "Hello World"}

if __name__ == '__main__':
     import uvicorn
     uvicorn.run(app, host="0.0.0.0", port=8000)

