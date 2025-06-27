# Falcon Usage Instructions

## Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/autosolutionsai-didac/Falcon.git
   cd Falcon
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual configuration:
   # - OPENROUTER_API_KEY: Get from https://openrouter.ai/
   # - Database credentials
   # - Google OAuth credentials
   # - Email SMTP settings
   ```

4. **Set up PostgreSQL database**
   ```bash
   # Create a PostgreSQL database named 'falcon_db'
   # Update DATABASE_URL in .env with your credentials
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the application**
   - Open http://localhost:8000 in your browser
   - Register a new account or login with Google

## Key Features

### For Lawyers
- **Case Management**: Create and manage divorce cases
- **Document Upload**: Securely upload financial documents (bank statements, tax returns, etc.)
- **AI Analysis**: Run forensic analysis to identify assets, liabilities, and potential hidden assets
- **Report Generation**: Generate comprehensive reports for court proceedings

### Security Features
- End-to-end encryption for all sensitive data
- Secure authentication with JWT tokens
- Google OAuth integration
- HTTPS enforcement in production

## API Endpoints

- `/api/auth/register` - Register new account
- `/api/auth/token` - Login
- `/api/auth/google` - Google OAuth login
- `/api/cases/` - Case management
- `/api/documents/` - Document management
- `/api/reports/` - Report generation

## Development

For development with hot reload:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Production Deployment

1. Set `ENVIRONMENT=production` in .env
2. Use a production database
3. Configure proper CORS origins
4. Use HTTPS with proper certificates
5. Set strong encryption keys