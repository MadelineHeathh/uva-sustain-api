# Running the App with Flask CLI

## Setup Complete! ✅

The app is now configured to run with `flask run` command.

## How to Run

### Option 1: Using Flask CLI (Recommended for Development)

1. **Activate virtual environment:**
   ```bash
   source venv/bin/activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run with Flask:**
   ```bash
   flask run
   ```

   Or specify host and port:
   ```bash
   flask run --host=0.0.0.0 --port=8080
   ```

### Option 2: Using Python (Still Works)

```bash
python src/app.py
```

### Option 3: Using Docker (For Deployment)

```bash
docker build -t madelineheathh/uva-sustain-api:latest .
docker run -p 8080:8080 madelineheathh/uva-sustain-api:latest
```

## Configuration

The `.flaskenv` file contains:
- `FLASK_APP=src.app` - Points Flask to your app
- `FLASK_ENV=development` - Development mode
- `FLASK_DEBUG=1` - Enable debug mode

## Environment Variables

You can still set environment variables:
```bash
export DATA_FILE=assets/sustainability_metrics.csv
export PORT=8080
export HOST=0.0.0.0
flask run
```

## Testing

After running, test the API:
```bash
curl http://localhost:5000/health
```

Or if using port 8080:
```bash
curl http://localhost:8080/health
```

## Notes

- Flask CLI uses port 5000 by default
- Data loads automatically on first request
- Both `flask run` and `python src/app.py` work
- Docker deployment still uses `python src/app.py` (as configured in Dockerfile)

