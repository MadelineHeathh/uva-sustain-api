# Step-by-Step: Deploy UVA Sustainability API to Azure with Docker

This tutorial will guide you through deploying your Flask application to Azure App Service using Docker.

## Prerequisites

- Docker Desktop installed and running
- Docker Hub account (username: `madelineheathh`)
- Azure account with active subscription
- Azure CLI installed (optional, but helpful)

---

## Part 1: Prepare Docker Image

### Step 1: Verify Docker is Running

```bash
docker --version
docker ps
```

If Docker isn't running, start Docker Desktop.

### Step 2: Navigate to Project Directory

```bash
cd /Users/madiheath/fall25/Systems/uva-sustain-api
```

### Step 3: Build Docker Image

Build the Docker image with your Docker Hub username:

```bash
docker build -t madelineheathh/uva-sustain-api:latest .
```

**What this does:**
- `-t madelineheathh/uva-sustain-api:latest` - Tags the image with your Docker Hub username and "latest" tag
- `.` - Uses the current directory (where Dockerfile is located)

**Expected output:** You should see Docker downloading base images and building your app. This may take a few minutes.

### Step 4: Test Docker Image Locally (Optional but Recommended)

Test that your Docker image works before pushing:

```bash
docker run -p 8080:8080 madelineheathh/uva-sustain-api:latest
```

Then open `http://localhost:8080` in your browser. If it works, press `Ctrl+C` to stop the container.

### Step 5: Login to Docker Hub

```bash
docker login
```

Enter your Docker Hub username (`madelineheathh`) and password when prompted.

### Step 6: Push Image to Docker Hub

```bash
docker push madelineheathh/uva-sustain-api:latest
```

**What this does:** Uploads your Docker image to Docker Hub so Azure can pull it.

**Expected output:** You'll see layers being pushed. This may take a few minutes depending on your internet speed.

---

## Part 2: Deploy to Azure

### Step 7: Login to Azure Portal

1. Go to [https://portal.azure.com](https://portal.azure.com)
2. Sign in with your Azure account

### Step 8: Create or Select Resource Group

**If you already have a resource group:**
- Click "Resource groups" in the left menu
- Select your existing resource group

**If you need to create a new one:**
1. Click "Resource groups" → "Create"
2. Name: `uva-sustainability-rg` (or your preferred name)
3. Region: Choose closest to you (e.g., `Canada Central`)
4. Click "Review + create" → "Create"

### Step 9: Create Azure Web App

1. In Azure Portal, click **"Create a resource"** (top left, green + button)
2. Search for **"Web App"**
3. Click **"Create"**

### Step 10: Configure Web App Basics

Fill in the **Basics** tab:

- **Subscription:** Select your subscription
- **Resource Group:** Select the resource group from Step 8
- **Name:** `uva-sustainability-api` (or your preferred name - must be globally unique)
- **Publish:** Select **"Container"**
- **Operating System:** Select **"Linux"**
- **Region:** Same as your resource group
- **App Service Plan:** 
  - Click "Create new" if needed
  - Name: `uva-sustainability-plan`
  - Sku and size: **Free F1** (for testing) or **Basic B1** (for production)
- Click **"Next: Deployment"**

### Step 11: Configure Container Settings

In the **Deployment** tab:

- **Container Source:** Select **"Docker Hub"**
- **Access Type:** Select **"Public"**
- **Image and Tag:** Enter `madelineheathh/uva-sustain-api:latest`
- **Startup Command:** Leave blank (or use: `python src/app.py`)

**Important:** Make sure the image name matches exactly what you pushed to Docker Hub!

Click **"Next: Networking"** (or **"Review + create"** if networking isn't needed)

### Step 12: Review and Create

1. Review all settings
2. Click **"Create"**
3. Wait for deployment to complete (this takes 2-5 minutes)
4. Click **"Go to resource"** when deployment succeeds

---

## Part 3: Configure Application Settings

### Step 13: Set Environment Variables

1. In your Web App, go to **"Configuration"** in the left menu
2. Click **"Application settings"** tab
3. Click **"+ New application setting"** and add:

   **Setting 1:**
   - Name: `PORT`
   - Value: `8080`
   - Click "OK"

   **Setting 2:**
   - Name: `HOST`
   - Value: `0.0.0.0`
   - Click "OK"

   **Setting 3:**
   - Name: `FLASK_APP`
   - Value: `src/app.py`
   - Click "OK"

4. Click **"Save"** at the top
5. Click **"Continue"** when prompted to restart

### Step 14: Verify Container Settings

1. Still in **"Configuration"**, click **"General settings"** tab
2. Scroll to **"Container settings"**
3. Verify:
   - **Image source:** Docker Hub
   - **Image and tag:** `madelineheathh/uva-sustain-api:latest`
   - **Startup command:** (can be blank or `python src/app.py`)
4. Click **"Save"** if you made any changes

---

## Part 4: Test Deployment

### Step 15: Access Your Application

1. In your Web App, click **"Overview"** in the left menu
2. Find the **"URL"** (e.g., `https://uva-sustainability-api.azurewebsites.net`)
3. Click the URL or copy and paste it into your browser

### Step 16: Test Endpoints

Try these URLs in your browser:

- **Home page:** `https://your-app-name.azurewebsites.net/`
- **Health check:** `https://your-app-name.azurewebsites.net/health`
- **Buildings list:** `https://your-app-name.azurewebsites.net/api/v1/buildings`
- **API info:** `https://your-app-name.azurewebsites.net/api`

### Step 17: Check Logs if Issues Occur

If the app doesn't work:

1. In Azure Portal, go to your Web App
2. Click **"Log stream"** in the left menu
3. Look for error messages
4. Common issues:
   - **"Application Error"** - Check environment variables are set correctly
   - **"Container failed to start"** - Check Docker image was pushed correctly
   - **"Port not found"** - Make sure PORT=8080 is set

---

## Part 5: Update Deployment (When You Make Changes)

When you update your code and want to redeploy:

### Step 18: Rebuild and Push Updated Image

```bash
cd /Users/madiheath/fall25/Systems/uva-sustain-api

# Build new image
docker build -t madelineheathh/uva-sustain-api:latest .

# Push to Docker Hub
docker push madelineheathh/uva-sustain-api:latest
```

### Step 19: Restart Azure Web App

1. Go to Azure Portal → Your Web App
2. Click **"Restart"** in the top menu
3. Wait 1-2 minutes for the app to restart with the new image

**Alternative:** Azure will automatically pull the latest image if you use a tag like `:latest`, but you may need to restart the app.

---

## Troubleshooting

### Issue: "Application Error" when accessing the site

**Solution:**
1. Check **"Log stream"** in Azure Portal for specific errors
2. Verify all environment variables are set (PORT, HOST, FLASK_APP)
3. Make sure Docker image was pushed successfully
4. Check that the image name in Azure matches Docker Hub exactly

### Issue: "Container failed to start"

**Solution:**
1. Test the Docker image locally first: `docker run -p 8080:8080 madelineheathh/uva-sustain-api:latest`
2. Check Docker Hub to verify the image exists: https://hub.docker.com/r/madelineheathh/uva-sustain-api
3. Verify the image and tag in Azure Configuration matches Docker Hub

### Issue: "404 Not Found" for API endpoints

**Solution:**
1. Make sure you're using the correct URL format
2. Check that the app is running (visit the root URL first)
3. Verify routes in `src/app.py` are correct

### Issue: Building takes too long

**Solution:**
- This is normal for the first build. Subsequent builds will be faster due to Docker layer caching.

---

## Quick Reference Commands

```bash
# Build image
docker build -t madelineheathh/uva-sustain-api:latest .

# Test locally
docker run -p 8080:8080 madelineheathh/uva-sustain-api:latest

# Login to Docker Hub
docker login

# Push to Docker Hub
docker push madelineheathh/uva-sustain-api:latest

# View running containers
docker ps

# Stop a container
docker stop <container-id>
```

---

## Next Steps

- **Custom Domain:** Add your own domain name in Azure Web App settings
- **SSL Certificate:** Azure provides free SSL for `*.azurewebsites.net` domains
- **Monitoring:** Set up Application Insights for monitoring
- **Scaling:** Adjust App Service Plan if you need more resources
- **CI/CD:** Set up GitHub Actions to automatically build and deploy on code changes

---

## Summary

You've successfully deployed your Flask application to Azure! The key steps were:

1. ✅ Built Docker image
2. ✅ Pushed to Docker Hub
3. ✅ Created Azure Web App
4. ✅ Configured container settings
5. ✅ Set environment variables
6. ✅ Tested the deployment

Your app is now live at: `https://your-app-name.azurewebsites.net`

