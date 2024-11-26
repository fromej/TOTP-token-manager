# TOTP Manager

A web application to manage and display TOTP (Time-Based One-Time Password) tokens with SQLite persistent storage.

## Prerequisites

- Python 3.8+
- `uv` package manager (recommended)

## Installation of UV Package Manager

### macOS/Linux
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Windows (PowerShell)
```powershell
irm https://astral.sh/uv/install.ps1 | iex
```

## Project Setup

1. Clone the repository

2. Create and activate virtual environment:
   ```bash
   uv venv  # Create virtual environment
   source .venv/bin/activate  # Activate (use .venv\Scripts\activate on Windows)
   ```

3. Install dependencies:
   ```bash
   uv pip install -r backend/requirements.in
   ```

4. Run the application:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

5. Open a web browser and navigate to `http://localhost:8000`

## Development Workflow

### Adding New Dependencies
```bash
uv pip install new-package
uv pip freeze > backend/requirements.in
```

### Updating Dependencies
```bash
uv pip install --upgrade fastapi uvicorn
uv pip freeze > backend/requirements.in
```

## Features

- Add TOTP tokens with custom names
- Persistent storage using SQLite
- Automatic token code refresh
- Delete existing tokens
- Single-page web application served directly by FastAPI

## Security Considerations

- Tokens are stored in plain text - suitable for development only
- Implement additional security measures for production use
- Consider encryption for token secrets
- Add user authentication for multi-user scenarios

## Troubleshooting

- Ensure you're using the virtual environment
- Check that all dependencies are correctly installed
- Verify Python version compatibility