from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import mysql.connector
from .database import create_tables, get_db_connection
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/", response_class=HTMLResponse)
def home_html() -> HTMLResponse:
    with open("app/static/homepage.html") as html:
        return HTMLResponse(content=html.read())


if __name__ == "__main__":
   uvicorn.run(app="app.main:app", host="0.0.0.0", port=6543, reload=True)