# RecallGuard

A comprehensive product recall monitoring system that helps users stay informed about safety recalls for their registered products.

## Overview

RecallGuard automatically monitors FDA and CPSC recall databases and uses AI to match recalls with user-registered products, sending immediate notifications when potential matches are found.

## Features

- **Product Registration**: Easy registration of household products
- **AI-Powered Matching**: Intelligent matching of recalls to your products
- **Real-time Notifications**: Immediate alerts for potential recall matches
- **Multiple Data Sources**: Monitors FDA and CPSC recall databases
- **Dashboard Interface**: User-friendly web interface for managing products and viewing alerts

## Project Structure

```
RecallGuard/
├── frontend/               # Next.js frontend application
│   ├── app/               # App router pages and layouts
│   │   ├── auth/          # Authentication pages
│   │   ├── dashboard/     # Dashboard and product management
│   │   └── recalls/       # Recall browsing
│   ├── components/        # React components
│   │   ├── features/      # Feature-specific components
│   │   └── ui/           # UI components
│   ├── services/          # API service layer
│   └── types/            # TypeScript type definitions
│
├── backend/               # FastAPI backend application
│   ├── app/              # Main application code
│   │   ├── core/         # Core functionality (models, database, schemas)
│   │   ├── services/     # Business logic services
│   │   ├── api/          # API endpoints
│   │   └── main.py       # FastAPI application entry point
│   ├── scripts/          # Utility and migration scripts
│   ├── tests/            # Test files
│   └── docs/             # Backend documentation
│
└── docs/                 # Project documentation

```

## Tech Stack

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **React Hot Toast** - Toast notifications

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL/SQLite** - Database
- **OpenAI API** - AI-powered recall matching
- **APScheduler** - Background job scheduling

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- PostgreSQL (optional, SQLite for development)

### Installation

#### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Initialize database
python -m scripts.create_tables

# Run the backend
python -m uvicorn app.main:app --reload
```

#### Frontend Setup
```bash
cd frontend
npm install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your configuration

# Run the frontend
npm run dev
```

### Environment Variables

#### Backend (.env)
```
DATABASE_URL=sqlite:///./recallguard.db
OPENAI_API_KEY=your_api_key_here
EMAIL_SERVICE_API_KEY=your_email_api_key
PORT=8000
```

#### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Usage

1. **Register**: Create an account with your email
2. **Add Products**: Register your household products in the dashboard
3. **Monitor**: The system automatically checks for recalls
4. **Get Notified**: Receive immediate alerts for matching recalls

## API Documentation

When the backend is running, visit:
- API Documentation: `http://localhost:8000/docs`
- Alternative docs: `http://localhost:8000/redoc`

## Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Quality
```bash
# Backend
cd backend
black .
flake8 .
mypy .

# Frontend
cd frontend
npm run lint
npm run type-check
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- FDA API for recall data
- CPSC for product safety information
- OpenAI for AI-powered matching capabilities