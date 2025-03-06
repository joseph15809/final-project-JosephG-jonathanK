from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import Response, HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
import bcrypt
import uuid
import mysql.connector
from contextlib import asynccontextmanager
from pydantic import BaseModel
from datetime import datetime

from .database import (
    setup_database,
    get_user_by_email,
    get_user_by_id,
    create_session,
    get_session,
    delete_session,
    add_user,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for managing application startup and shutdown.
    Handles database setup and cleanup in a more structured way.
    """
    # Startup: Setup resources
    try:
        await setup_database() 
        print("Database setup completed")
        yield
    finally:
        print("Shutdown completed")

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

def read_html(file_path: str) -> str:
    with open(file_path, "r") as f:
        return f.read()

@app.get("/", response_class=HTMLResponse)
def home_html():
    return HTMLResponse(content=read_html("app/static/homepage.html"))

@app.get("/signup", response_class=HTMLResponse)
def signup_html(request: Request):
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
    try:
        user_id = await add_user(name, email, hashed_password, location)

        # Generate session ID and store it
        session_id = str(uuid.uuid4())
        await create_session(user_id, session_id)

    except Exception as e:
        return {"error": f"Signup failed: {e}"}

    # Set cookie with session ID
    response = RedirectResponse(url=f"/dashboard/{user_id}", status_code=302)
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=3600,  # 1 hour session expiry
        httponly=True,  # Prevent JavaScript access
        secure=True,  # Send only over HTTPS
    )

    return response


@app.get("/login", response_class=HTMLResponse)
async def login_html(request: Request):
    """Show login if not logged in, or redirect to profile page"""
    session_id = request.cookies.get("session_id")

    if session_id:
        session = await get_session(session_id)
        if session:
            user = await get_user_by_id(session["user_id"])
            if user:
                return RedirectResponse(url=f"/dashboard/{user['user_id']}", status_code=302)
    return HTMLResponse(content=read_html("app/static/login.html"))


@app.post("/login")
async def login(request: Request):
    """Validate credentials and create a new session if valid"""
    form_data = await request.form()
    email = form_data.get("email")
    password = form_data.get("password")

    user = await get_user_by_email(email)

    if not user or not bcrypt.checkpw(password.encode(), user["password"].encode('utf-8')):
        raise HTTPException(status_code=401, detail="Invalid email or password") # checks if email and hashed password match

    # Generate session ID and store it
    session_id = str(uuid.uuid4())
    await create_session(user["user_id"], session_id)

    # Set cookie with session ID
    response = RedirectResponse(url=f"/dashboard/{user['user_id']}", status_code=302)
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=3600,  # 1 hour session expiry
        httponly=True,  # Prevent JavaScript access
        secure=True,  # Send only over HTTPS
    )

    return response


@app.post("/logout")
async def logout(request: Request):
    """Clear session and redirect to login page"""
    session_id = request.cookies.get("session_id")

    if session_id:
        await delete_session(session_id)

    # Clear cookie and redirect
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("session_id")
    return response


@app.get("/dashboard/{user_id}", response_class=HTMLResponse)
async def user_page(user_id: int, request: Request):
    """Show user profile if authenticated, error if not"""
    session_id = request.cookies.get("session_id")

    if not session_id:
        return RedirectResponse(url="/login", status_code=302)

    session = await get_session(session_id)
    if not session:
        return RedirectResponse(url="/login", status_code=302)

    user = await get_user_by_id(session["user_id"])
    if not user or user["user_id"] != user_id:
        return {"error": f"Not authenticated as {user['name']}"}

    return HTMLResponse(content=read_html("app/static/dashboard.html"))


if __name__ == "__main__":
   uvicorn.run(app="app.main:app", host="0.0.0.0", port=6543, reload=True)