from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import APIKeyHeader, HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel
from typing import Optional
import uuid
import secrets
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from fastapi import Security
from starlette.middleware.sessions import SessionMiddleware

# App setup
app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="your-secret-key")
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Security setup
security = HTTPBasic()
API_KEY_HEADER = APIKeyHeader(name="X-API-Key")
API_KEY = "masuk123"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"

# Database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./licenses.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class License(Base):
    __tablename__ = "licenses"
    id = Column(String, primary_key=True, index=True)
    key = Column(String, unique=True, index=True)
    is_lifetime = Column(Boolean, default=False)
    expiry_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

Base.metadata.create_all(bind=engine)

class LicenseCreate(BaseModel):
    is_lifetime: bool = False
    duration_days: Optional[int] = None

class LicenseInfo(BaseModel):
    key: str
    is_lifetime: bool
    expiry_date: Optional[datetime]
    is_active: bool

def verify_api_key(api_key: str = Security(API_KEY_HEADER)):
    if api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(401, detail="Invalid credentials")
    return credentials.username

# Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
        request.session["authenticated"] = True
        return RedirectResponse("/admin", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

@app.get("/admin")
async def admin_page(request: Request, db: Session = Depends(get_db)):
    if not request.session.get("authenticated"):
        return RedirectResponse("/login")
    licenses = db.query(License).all()
    return templates.TemplateResponse("admin.html", {"request": request, "licenses": licenses})

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login")

@app.post("/api/licenses/", response_model=LicenseInfo)
def create_license(
    license_data: LicenseCreate,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    license_key = str(uuid.uuid4())
    new_license = License(
        id=str(uuid.uuid4()),
        key=license_key,
        is_lifetime=license_data.is_lifetime,
        expiry_date=None if license_data.is_lifetime else 
                   datetime.utcnow() + timedelta(days=license_data.duration_days or 365)
    )
    db.add(new_license)
    db.commit()
    db.refresh(new_license)
    return new_license

@app.get("/api/licenses/{license_key}", response_model=LicenseInfo)
def verify_license(
    license_key: str,
    db: Session = Depends(get_db)
):
    license = db.query(License).filter(License.key == license_key).first()
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    if not license.is_lifetime and license.expiry_date < datetime.utcnow():
        license.is_active = False
        db.commit()
    return license

@app.delete("/api/licenses/{license_key}")
def revoke_license(
    license_key: str,
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    license = db.query(License).filter(License.key == license_key).first()
    if not license:
        raise HTTPException(status_code=404, detail="License not found")
    license.is_active = False
    db.commit()
    return {"message": "License revoked successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)