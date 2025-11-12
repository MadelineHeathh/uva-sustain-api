# Virtual Environment (venv) Guide

## How to Activate Virtual Environment

### If venv already exists:

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

### If venv doesn't exist, create it first:

1. **Create virtual environment:**
   ```bash
   python3 -m venv venv
   ```

2. **Activate it:**
   ```bash
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Quick Commands

### Activate venv:
```bash
cd /Users/madiheath/fall25/Systems/uva-sustain-api
source venv/bin/activate
```

### Deactivate venv:
```bash
deactivate
```

### Check if venv is active:
When active, you'll see `(venv)` at the start of your terminal prompt:
```
(venv) madiheath@MacBook-Pro uva-sustain-api %
```

## For This Project

Since you're using Docker, you don't strictly need a venv for deployment, but it's useful for local development:

```bash
# Create venv (if needed)
python3 -m venv venv

# Activate
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run app locally (for testing)
python src/app.py
```

## Note

For Docker deployment, you don't need to activate venv - Docker handles the environment automatically.

