# Install Docker Desktop

Docker Desktop installation requires sudo access. Please run this manually:

## Option 1: Via Homebrew (Recommended)

Open Terminal and run:
```bash
brew install --cask docker
```

You'll be prompted for your password. Enter it to continue the installation.

## Option 2: Download from Docker Website

1. Go to: https://www.docker.com/products/docker-desktop/
2. Click "Download for Mac"
3. Open the downloaded .dmg file
4. Drag Docker.app to Applications folder
5. Open Docker.app from Applications

## After Installation

1. Open Docker Desktop:
   ```bash
   open -a Docker
   ```

2. Wait ~30 seconds for Docker to start

3. Verify Docker is running:
   ```bash
   docker info
   ```
   
   You should see Docker version info (not an error).

## Once Docker is Running

Come back and run:
```bash
cd ~/gtm-research-airflow
./deploy.sh
```

This will deploy your DAG to Astro!
