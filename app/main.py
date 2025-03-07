from fastapi import FastAPI, Request, Response, HTTPException, Query
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
    get_db_connection,
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

class SensorData(BaseModel):
    mac_address: str
    value: float
    unit: str
    timestamp: str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

valid_sensor = {"temperature"}

class DeviceRegistration(BaseModel):
    mac_address: str

class DeviceAssignment(BaseModel):
    device_id: int   

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
    
@app.post("/api/register_device/")
def register_device(device: DeviceRegistration):
    """Registers an ESP32 device using its MAC address."""
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Check if the device is already registered
        cursor.execute("SELECT * FROM devices WHERE mac_address = %s", (device.mac_address,))
        existing_device = cursor.fetchone()

        if existing_device:
            return {"message": "Device already registered", "device_id": existing_device["device_id"]}

        # Register new device
        cursor.execute("INSERT INTO devices (mac_address) VALUES (%s)", (device.mac_address,))
        connection.commit()

        device_id = cursor.lastrowid  # Get the new device's ID
        return {"message": "Device registered successfully", "device_id": device_id}

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        cursor.close()
        connection.close()


@app.get("/api/devices/{user_id}")
def get_user_devices(user_id: int):
    """Retrieve all devices registered to a specific user."""
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch all devices linked to the user
        cursor.execute("""
            SELECT device_id, mac_address, name, timestamp
            FROM devices
            WHERE user_id = %s
        """, (user_id,))
        
        devices = cursor.fetchall()

        if not devices:
            raise HTTPException(status_code=404, detail="No devices found for this user.")

        return {"devices": devices}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        cursor.close()
        connection.close()



@app.get("/api/{uesr_id}/{mac_address}/{sensor_type}")
def get_all_sensor_data(user_id: int,
                        mac_address: str,
                        sensor_type: str,
                        order_by: str = Query(None, alias="order-by"),
                        start_date: str = Query(None, alias="start-date"),
                        end_date: str = Query(None, alias="end-date")):

    if sensor_type not in valid_sensor:
        raise HTTPException(status_code=404, detail="invalid sensor type")

    query = f"SELECT * FROM {sensor_type}"
    condition = ["user_id = %s", "mac_address = %s"]
    params = [user_id, mac_address]

    if start_date:
        condition.append("timestamp >= %s")
        params.append(start_date)
    if end_date:
        condition.append("timestamp <= %s")
        params.append(end_date)
    if condition:
        query += " WHERE " + " AND ".join(condition)
    if order_by in {"value", "timestamp"}:
        query += f" ORDER BY {order_by}"

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, params)
    results = cursor.fetchall()
    cursor.close()
    connection.close()

    for row in results:
        if isinstance(row["timestamp"], datetime):  # Check if it's a datetime object
            row["timestamp"] = row["timestamp"].strftime("%Y-%m-%d %H:%M:%S")

    return results


@app.post("/api/temperature")
def insert_sensor_data(data: SensorData):

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(f"INSERT INTO temperature (mac_address, value, unit, timestamp) VALUES (%s, %s, %s, %s)", 
                                            (data.mac_address, data.value, data.unit, data.timestamp))
    connection.commit()
    new_id = cursor.lastrowid
    cursor.close()
    connection.close()

    return {"id": new_id}


@app.get("/api/user/{user_id}/devices")
def get_user_devices(user_id: int):
    """Retrieve all ESP32 devices registered to a specific user."""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT device_id, mac_address, name FROM devices WHERE user_id = %s", (user_id))
        devices = cursor.fetchall()

        return {"user_id": user_id, "devices": devices}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        cursor.close()
        connection.close()


@app.get("api/devices")
def get_devices():
    """Get avialable an ESP32 device to a user."""
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        cursor.execute("SELECT device_id FROM devices WHERE user_id = %s", ('NULL'))
        devices = cursor.fetchone()

        return devices

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        cursor.close()
        connection.close()    


@app.post("/api/user/{user_id}/add_device")
def add_device_to_user(user_id: int, assignment: DeviceAssignment):
    """Assign an ESP32 device to a user."""
    connection = get_db_connection()
    cursor = connection.cursor()

    try:
        # Check if the device is already assigned
        cursor.execute("SELECT user_id FROM devices WHERE device_id = %s", (assignment.device_id,))
        device = cursor.fetchone()

        if device and device[0] is not None:
            raise HTTPException(status_code=400, detail="Device is already assigned to another user.")

        # Assign device to the user
        cursor.execute("UPDATE devices SET user_id = %s WHERE device_id = %s", (user_id, assignment.device_id))
        connection.commit()

        return {"message": "Device successfully added to your profile"}

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        cursor.close()
        connection.close()


@app.get("/profile", response_class=HTMLResponse)
def signup_html(request: Request):
    return HTMLResponse(content=read_html("app/static/profile.html"))


if __name__ == "__main__":
   uvicorn.run(app="app.main:app", host="0.0.0.0", port=8000, reload=True)