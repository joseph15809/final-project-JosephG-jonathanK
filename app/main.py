from fastapi import FastAPI, Request, Response, HTTPException, Query, Depends
from fastapi.responses import Response, HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import httpx
import uvicorn
import os
from dotenv import load_dotenv
import bcrypt
import uuid
import mysql.connector
from contextlib import asynccontextmanager
from pydantic import BaseModel
from datetime import datetime

from .database import (
    get_db_connection,
    setup_database,
    get_user_by_email,
    get_user_by_id,
    create_session,
    get_session,
    delete_session,
    add_user,
    get_db_connection,
    add_temperature,
    clear_database,
    add_clothes,
    remove_clothes,
    update_clothes,
    get_user_clothes,
    get_users_location,
    update_user
)

load_dotenv()
PID = os.getenv("UCSD_PID")
email = os.getenv("UCSD_EMAIL")

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


class DeviceRegistration(BaseModel):
    mac_address: str

class DeviceAssignment(BaseModel):
    user_id: int
    device_id: int   

class UpdateUserInfo(BaseModel):
    name: str
    location: str
    current_password: str = None  # Optional for password update
    new_password: str = None
    confirm_password: str = None

class Clothes(BaseModel):
    id: int    
    name: str
    clothes_type: str
    color: str


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
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=86400,  # 1 day session expiry
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
                return RedirectResponse(url="/dashboard", status_code=302)
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
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=86400,  # 1 day session expiry
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


@app.get("/wardrobe", response_class=HTMLResponse)
async def user_wardrobe(request: Request):
    """Show user profile if authenticated, error if not"""
    session_id = request.cookies.get("session_id")

    if not session_id:
        return RedirectResponse(url="/login", status_code=302)
    
    session = await get_session(session_id)
    if not session:
        return RedirectResponse(url="/login", status_code=302)
    
    user_id = session["user_id"]
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
        
    user = await get_user_by_id(user_id)
    if not user:
        return {"error": "User not found"}

    return HTMLResponse(content=read_html("app/static/wardrobe.html"))


@app.post("/wardrobe/add")
async def add_to_wardrobe(request: Request):

    # get form data
    form_data = await request.form()
    type = form_data.get("type")
    color = form_data.get("color")
    name = form_data.get("name")

    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = session["user_id"]
    if not name:
        name = color + ' ' + type

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await add_clothes(name, user_id, type, color)

    return RedirectResponse(url="/wardrobe", status_code=303)


@app.delete("/api/wardrobe/remove")
async def remove_from_wardrobe(clothes: Clothes, request: Request):
    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = session["user_id"]

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await remove_clothes(clothes.id, user_id)
    return {"success": True, "message": "Clothing item removed successfully"}



@app.post("/api/wardrobe/update")
async def update_user_clothes(clothes: Clothes, request: Request):
    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = session["user_id"]

    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    await update_clothes(clothes.id, clothes.name, clothes.clothes_type, clothes.color)
    return {"success":f"updated clothing {clothes.id}"}


async def generate_outfit_request(prompt: str):
    """Send an async request to AI API to generate outfit"""
    AI_API_URL = "https://ece140-wi25-api.frosty-sky-f43d.workers.dev/api/v1/ai/complete"
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            ai_response = await client.post(
                AI_API_URL,
                headers={
                    "email": email,
                    "pid": PID,
                    "Content-Type": "application/json"
                },
                json={"prompt": prompt}
            )
        except httpx.TimeoutException:
            return {"error": "AI API request timed out"} 
    response_data = ai_response.json()

    if ai_response.status_code != 200 or not response_data.get("success", False):
        return {"error": f"Failed to generate outfit. Status code: {ai_response.status_code}"}

    generated_outfit = response_data.get("result", {}).get("response", "No outfit recommendation found.")
    
    return {"outfit": generated_outfit}


@app.get("/api/wardrobe")
async def get_wardrobe(request: Request):
    """Get wardrobe data"""
    connection = get_db_connection()
    cursor = connection.cursor()

    session_id = request.cookies.get("session_id")

    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user_id = session["user_id"]
    
    wardrobe_data = await get_user_clothes(user_id)

    return JSONResponse(wardrobe_data, status_code=200)


@app.get("/api/generate-outfit/{temperature}/{condition}")
async def generate_user_outfit(temperature: int, condition: str, request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        session = await get_session(session_id)
        if session:
            user_id = session["user_id"]
            user = await get_user_by_id(user_id)
            if user:
                clothes = await get_user_clothes(user_id)
                weather_text = f"{temperature}°F, {condition}"
                prompt = f"From these pieces of clothing: {clothes} and based on the weather ({weather_text}), generate an outfit me to wear."
                outfit_result = await generate_outfit_request(prompt)
                return JSONResponse(outfit_result, status_code=200)
    return JSONResponse({"error": "Failed to authenticate user"}, status_code=401) 


@app.get("/dashboard", response_class=HTMLResponse)
async def user_page(request: Request):
    """Show user dashboard if authenticated, error if not"""
    session_id = request.cookies.get("session_id")

    if not session_id:
        return RedirectResponse(url="/login", status_code=302)

    session = await get_session(session_id)
    if not session:
        return RedirectResponse(url="/login", status_code=302)

    user_id = session["user_id"]
    if not user_id:
        return RedirectResponse(url="/login", status_code=302)
    
    user = await get_user_by_id(user_id)
    if not user:
        return {"error": "User not found"}

    return HTMLResponse(content=read_html("app/static/dashboard.html"))
    

@app.get("/api/userInfo")
async def get_user_info(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        session = await get_session(session_id)
        if session:
            user = await get_user_by_id(session["user_id"])
            if user:
                return {"name": user["name"],
                        "email": user["email"],
                        "location": user["location"]}
    return {"error": "could not get user info"}


@app.put("/api/updateUser")
async def update_user_info(request: Request, user_data: UpdateUserInfo):
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session = await get_session(session_id)
    if not session:
        raise HTTPException(status_code=401, detail="Session expired")

    user_id = session["user_id"]
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="user not found")

    # Check if password update is requested
    if user_data.current_password and user_data.new_password and user_data.confirm_password:
        # Validate current password
        if not bcrypt.checkpw(user_data.current_password.encode(), user["password"].encode()):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Check if new passwords match and update
        if user_data.new_password != user_data.confirm_password:
            raise HTTPException(status_code=400, detail="New passwords do not match")
        hashed_new_password = bcrypt.hashpw(user_data.new_password.encode(), bcrypt.gensalt()).decode()
        await update_user(user_id, user_data.name, user_data.location, hashed_new_password)
    
    else:
        await update_user(user_id, user_data.name, user_data.location)

    return {"success": "User info updated successfully"}


@app.get("/api/location/{user_id}")
async def get_user_location(user_id: int, request: Request):
    try:
        location = await get_users_location(user_id)
    except Exception as e:
        return {"error": f"getting loction failed {e}"}
    return {"location": location}


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


@app.get("/api/temperature/{mac_address}")
def get_all_sensor_data(mac_address: str,
                        order_by: str = Query(None, alias="order-by"),
                        start_date: str = Query(None, alias="start-date"),
                        end_date: str = Query(None, alias="end-date")):

    query = f"SELECT * FROM temperature"
    condition = ["mac_address = %s"]
    params = [mac_address]

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
async def insert_sensor_data(data: SensorData):
    try:
        new_id = await add_temperature(data.mac_address, data.value, data.unit, data.timestamp)

    except Exception as e:
        return {"error": f"adding data failed: {e}"}

    return {"id": new_id}


@app.get("/api/devices/{user_id}")
def get_user_devices(user_id: int):
    """Retrieve all devices registered to a specific user."""
    
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        # Fetch all devices linked to the user
        cursor.execute("""
            SELECT device_id, mac_address, name
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


@app.get("/api/devices")
def get_devices():
    """Get avialable an ESP32 device to a user."""
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute("SELECT * FROM devices WHERE user_id IS NULL")
        devices = cursor.fetchall()

        return {"devices": devices}

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        cursor.close()
        connection.close()    


@app.post("/api/add_device")
def add_device_to_user(assignment: DeviceAssignment):
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
        cursor.execute("UPDATE devices SET user_id = %s WHERE device_id = %s", (assignment.user_id, assignment.device_id))
        connection.commit()

        return {"message": "Device successfully added to your profile"}

    except Exception as e:
        connection.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

    finally:
        cursor.close()
        connection.close()


@app.get("/api/getId")
async def get_user_id(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        session = await get_session(session_id)
        if session:
            user_id = session["user_id"]
            user = await get_user_by_id(user_id)
            if not user or user["user_id"] != user_id:
                return {"error": f"Not authenticated as {user['name']}"}
            return {"user_id":user_id}    
    return{"error":"Could not get user id"}


@app.get("/profile", response_class=HTMLResponse)
async def signup_html(request: Request):
    session_id = request.cookies.get("session_id")
    if session_id:
        session = await get_session(session_id)
        if session:
            user_id = session["user_id"]
            user = await get_user_by_id(user_id)
            if not user or user["user_id"] != user_id:
                return {"error": f"Not authenticated as {user['name']}"}
            return HTMLResponse(content=read_html("app/static/profile.html"))
    return RedirectResponse(url="/login", status_code=302)


if __name__ == "__main__":
    uvicorn.run(app="app.main:app", host="0.0.0.0", port=8000, reload=True)
