# License Manager

A FastAPI-based license management system with admin panel and license validation.

## Features
- Create annual/lifetime licenses
- Verify license validity
- Admin dashboard
- License revocation
- Secure API endpoints

## Installation

```bash
# Clone repository
git clone  https://github.com/dypras666/license-manager 
cd license-manager

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Configuration
- Default admin credentials: 
  - Username: admin
  - Password: admin123
- API Key: masuk123
- Edit these in `main.py`

## Running
```bash
uvicorn main:app --reload
```

Access:
- Admin: http://localhost:8000/admin
- License Validator: http://localhost:8000

## API Endpoints
```
POST /api/licenses/ - Create license
GET /api/licenses/{key} - Verify license
DELETE /api/licenses/{key} - Revoke license
```

## Tech Stack
- FastAPI
- SQLite
- SQLAlchemy
- Jinja2
- TailwindCSS