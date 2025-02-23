import base64
import os
import time
from typing import Optional, Dict, List
import pyotp
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlmodel import Field, Session, SQLModel, create_engine, select

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up static file serving
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
DB_PATH = os.path.join(BASE_DIR, 'totp_tokens.db')

# Serve static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Database configuration
DATABASE_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DATABASE_URL)


# Models
class Token(SQLModel, table=True):
    name: str = Field(primary_key=True)
    secret: str


class TOTPToken(SQLModel):
    name: str
    secret: str


class TOTPResponse(SQLModel):
    code: str
    timeRemaining: int


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# Initialize DB on startup
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


def get_session():
    with Session(engine) as session:
        yield session


@app.get("/")
async def serve_index():
    """Serve the main index.html file"""
    return FileResponse(os.path.join(STATIC_DIR, 'index.html'))


def normalize_secret(secret: str) -> str:
    """Normalize the secret to ensure it's properly base32 encoded"""
    try:
        # Try to decode and re-encode to validate base32
        decoded = base64.b32decode(secret.upper().replace(" ", ""))
        return base64.b32encode(decoded).decode('utf-8')
    except Exception:
        # If not valid base32, assume it's raw data and encode it
        return base64.b32encode(secret.encode('utf-8')).decode('utf-8')


@app.post("/add-token")
async def add_token(token: TOTPToken):
    try:
        # Normalize and validate the secret
        normalized_secret = normalize_secret(token.secret)
        # Validate by attempting to create a TOTP object
        pyotp.TOTP(normalized_secret)

        with Session(engine) as session:
            db_token = Token(name=token.name, secret=normalized_secret)
            session.merge(db_token)  # merge will insert or update
            session.commit()
            return {"message": "Token added successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid TOTP secret: {str(e)}")


@app.get("/tokens")
async def list_tokens() -> Dict[str, TOTPResponse]:
    with Session(engine) as session:
        tokens = session.exec(select(Token)).all()
        return {
            token.name: generate_totp_code(token.secret)
            for token in tokens
        }


@app.delete("/token/{name}")
async def delete_token(name: str):
    with Session(engine) as session:
        token = session.exec(select(Token).where(Token.name == name)).first()
        if not token:
            raise HTTPException(status_code=404, detail="Token not found")

        session.delete(token)
        session.commit()
        return {"message": "Token deleted successfully"}


def generate_totp_code(secret: str) -> TOTPResponse:
    """Generate TOTP code from a base32 encoded secret"""
    totp = pyotp.TOTP(secret)
    current_code = totp.now()
    time_remaining = 30 - int(time.time() % 30)
    return TOTPResponse(
        code=current_code,
        timeRemaining=time_remaining
    )


@app.get("/token/{name}")
async def get_token(name: str) -> TOTPResponse:
    with Session(engine) as session:
        token = session.exec(select(Token).where(Token.name == name)).first()
        if not token:
            raise HTTPException(status_code=404, detail="Token not found")

        return generate_totp_code(token.secret)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)