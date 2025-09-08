# RecallGuard Backend

FastAPI-based backend for RecallGuard - Product recall alert system.

## Setup

### Windows Installation

If you encounter compilation errors on Windows, try one of these approaches:

#### Option 1: Use Windows-specific requirements
```bash
pip install -r requirements-windows.txt
```

#### Option 2: Install problematic packages separately
```bash
pip install --only-binary=all psycopg2-binary
pip install --only-binary=all pydantic
pip install -r requirements.txt
```

#### Option 3: Use conda (recommended for Windows)
```bash
conda install psycopg2 pydantic fastapi uvicorn sqlalchemy python-dotenv alembic
pip install email-validator
```

### Standard Installation
```bash
pip install -r requirements.txt
```

## Environment Setup

Set up environment variables in `.env`:
```
DATABASE_URL=postgresql://username:password@localhost:5432/recallguard
PORT=8000
```

## Database Initialization

Create database tables:
```bash
python create_tables.py
```

## Running the Application

```bash
python main.py
```

## Troubleshooting

### Windows Compilation Issues

1. **Install Visual Studio Build Tools**: Download and install Microsoft C++ Build Tools
2. **Use pre-compiled wheels**: `pip install --only-binary=all package_name`
3. **Try older versions**: Some packages have better Windows compatibility in older versions
4. **Use conda**: `conda install package_name` often provides pre-compiled packages

### PostgreSQL Connection Issues

1. Make sure PostgreSQL is running
2. Check your DATABASE_URL format: `postgresql://user:password@host:port/database`
3. Ensure the database exists before running the application

## API Endpoints

### Create User
```bash
curl -X POST "http://localhost:8000/users" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "user@example.com",
       "phone": "+1234567890",
       "products": [
         {
           "product_name": "iPhone 15",
           "brand": "Apple",
           "model": "A2846"
         }
       ]
     }'
```

### Get User
```bash
curl -X GET "http://localhost:8000/users/1"
```

### Get User Products
```bash
curl -X GET "http://localhost:8000/users/1/products"
```

### Health Check
```bash
curl -X GET "http://localhost:8000/health"
```

## Deployment

This application is ready for Railway deployment. The `PORT` environment variable is automatically detected and used.