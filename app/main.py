from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import Response, HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import bcrypt
import mysql.connector
from .database import create_tables, get_db_connection
from pydantic import BaseModel
from datetime import datetime


app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")

def read_html(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()

@app.get("/", response_class=HTMLResponse)
def home_html():
    return HTMLResponse(content=read_html("app/static/homepage.html"))

@app.get("/login", response_class=HTMLResponse)
def home_html():
    return HTMLResponse(content=read_html("app/static/login.html"))

@app.get("/signup", response_class=HTMLResponse)
def home_html(request: Request):
    return HTMLResponse(content=read_html("app/static/signup.html"))

@app.post("/signup") 
async def signup(request: Request):
    
    # get form data
    form_data = await request.form()
    name = form_data.get("name")
    email = form_data.get("email")
    password = form_data.get("password")
    location = form_data.get("location")

    # makes sure all fields are filled
    if not (name and email and password and location):
        return {"error": "All fields are required"}

    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode() # hash password before storing

    connection = get_db_connection()
    if not connection:
        return {"error": "Database connection failed"}

    cursor = connection.cursor()

    try:
        cursor.execute(
            "INSERT INTO user (name, email, password, location) VALUES (%s, %s, %s, %s)",
            (name, email, hashed_password, location)
        )
        connection.commit()

        # Get the user_id of the newly created user
        cursor.execute("SELECT LAST_INSERT_ID()")
        user_id = cursor.fetchone()[0]

    except Exception as e:
        connection.rollback()
        return {"error": f"Failed to insert user: {e}"}

    finally:
        cursor.close()
        connection.close()

    # Redirect to the user's account page
    return RedirectResponse(url=f"/dashboard/{user_id}", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, user_id: int):
    connection = get_db_connection()
    if not connection:
        return {"error": "Database connection failed"}

    cursor = connection.cursor(dictionary=True)
    
    cursor.execute("SELECT name, email, location FROM user WHERE user_id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    connection.close()

    if not user:
        return{"error":"User not found"}

    return HTMLResponse(content=read_html("app/static/dashboard.html"))



if __name__ == "__main__":
   uvicorn.run(app="app.main:app", host="0.0.0.0", port=6543, reload=True)