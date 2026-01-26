# Installation Guide

## Prerequisites

- **Python 3.8+** (or Docker)
- **FFmpeg** (for audio conversion)
  ```bash
  # Ubuntu/Debian
  sudo apt-get install ffmpeg
  
  # macOS
  brew install ffmpeg
  
  # Windows
  # Download from https://ffmpeg.org/download.html
  ```

- **API Keys** (required):
  - **Deepgram API Key**: Get from [Deepgram Console](https://console.deepgram.com/)
  - **OpenAI API Key** (optional, for AI features): Get from [OpenAI Platform](https://platform.openai.com/)

- **PostgreSQL** (optional, if not using SQLite):
  - PostgreSQL 12+ installed and running

## Installation Methods

### Option 1: Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/youtube-script.git
   cd youtube-script
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Build and run:**
   ```bash
   docker-compose up -d
   ```

4. **Access the service:**
   - Admin Dashboard: http://localhost:8001
   - API Docs: http://localhost:8001/docs
   - Health Check: http://localhost:8001/health

### Option 2: Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/youtube-script.git
   cd youtube-script
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and configure your settings
   ```

5. **Run the service:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8001
   ```

## Next Steps

After installation, proceed to:
- [Configuration Guide](configuration.md) - Set up your environment variables
- [Database Setup](database.md) - Configure your database
- [Usage Guide](usage.md) - Learn how to use the service
