import os
import time
import sqlite3
import pyotp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from contextlib import contextmanager

app = FastAPI()

# Add CORS middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up static file serving
# Ensure the static files are in a 'static' directory within the backend folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

# Serve static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Database initialization
DB_PATH = os.path.join(BASE_DIR, 'totp_tokens.db')

@contextmanager
def get_db_connection():
    """Context manager for database connections"""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initialize the database and create table if not exists"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tokens (
                name TEXT PRIMARY KEY,
                secret TEXT NOT NULL
            )
        ''')
        conn.commit()

# Initialize DB on startup
init_db()

class TOTPToken(BaseModel):
    name: str
    secret: str

@app.get("/")
async def serve_index():
    """Serve the main index.html file"""
    return FileResponse(os.path.join(STATIC_DIR, 'index.html'))

@app.post("/add-token")
async def add_token(token: TOTPToken):
    try:
        # Validate the secret by attempting to create a TOTP object
        pyotp.TOTP(token.secret)
        
        # Store in SQLite
        with get_db_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO tokens (name, secret) VALUES (?, ?)", 
                    (token.name, token.secret)
                )
                conn.commit()
                return {"message": "Token added successfully"}
            except sqlite3.Error as e:
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid TOTP secret: {str(e)}")

@app.get("/tokens")
async def list_tokens():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name, secret FROM tokens")
        tokens = cursor.fetchall()
    
    return {
        name: generate_totp_code(secret)
        for name, secret in tokens
    }

@app.delete("/token/{name}")
async def delete_token(name: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tokens WHERE name = ?", (name,))
        conn.commit()
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Token not found")
        
        return {"message": "Token deleted successfully"}

def generate_totp_code(secret):
    totp = pyotp.TOTP(secret)
    current_code = totp.now()
    time_remaining = 30 - int(time.time() % 30)
    return {
        "code": current_code,
        "timeRemaining": time_remaining
    }

@app.get("/token/{name}")
async def get_token(name: str):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT secret FROM tokens WHERE name = ?", (name,))
        result = cursor.fetchone()
    
    if not result:
        raise HTTPException(status_code=404, detail="Token not found")
    
    secret = result[0]
    return generate_totp_code(secret)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
