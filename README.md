# YouTube Audio Transcription & AI Content Generation Service

A comprehensive FastAPI service for downloading YouTube videos, transcribing audio, managing AI prompts, and generating content using OpenAI GPT models. Features a full admin dashboard, bulk operations, and robust database storage.

## 🚀 Features

### Core Functionality
- **Video Transcription**: Download audio from YouTube videos and transcribe using Deepgram API
- **Channel Processing**: Extract all videos from YouTube channels with automatic pagination
- **Metadata Extraction**: Capture complete video metadata (title, channel, duration, views, upload date, etc.)
- **Smart Caching**: Avoids re-processing already transcribed videos
- **Rate Limiting Protection**: Handles YouTube bot detection and rate limits gracefully

### AI Integration
- **OpenAI GPT Integration**: Generate content using GPT-3.5, GPT-4, and other models
- **Prompt Management**: Store and reuse AI prompts with variable templates
- **Bulk Content Generation**: Generate AI content for multiple videos simultaneously
- **Content Storage**: Store multiple AI-generated content items per video (1 → many relationship)

### Admin Dashboard
- **Web-based UI**: Complete admin dashboard for all operations
- **Video Management**: View, search, and filter all videos
- **Transcript Viewing**: Browse and view transcripts with full-text search
- **Bulk Operations**: Select multiple videos and perform batch operations
- **Prompt Management**: Create, edit, and manage AI prompts
- **User Management**: Create and manage admin users
- **Settings Configuration**: Configure cookies, webhooks, and more

### Database & Storage
- **Dual Database Support**: SQLite (default) or PostgreSQL
- **Unlimited Text Storage**: All large fields (transcripts, prompts, content) use TEXT type
- **Metadata Storage**: Complete video metadata stored in structured and JSON format
- **Content Relationships**: One video can have many generated content items

### API Features
- **RESTful API**: Complete REST API with automatic Swagger documentation
- **Authentication**: Basic Auth and Bearer token support
- **Advanced Filtering**: Filter videos by status, channel, date range, search terms
- **Pagination**: Support for large datasets
- **Bulk Endpoints**: Process multiple videos in single requests

## 📋 Quick Start

### Prerequisites
- Python 3.8+ or Docker
- FFmpeg installed
- Deepgram API key ([Get one here](https://console.deepgram.com/))
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys)) - Optional for AI features

### Installation

**Option 1: Docker (Recommended)**
```bash
git clone https://github.com/yourusername/youtube-script.git
cd youtube-script
cp .env.example .env
# Edit .env and add your API keys
docker-compose up -d
```

**Option 2: Local Installation**
```bash
git clone https://github.com/yourusername/youtube-script.git
cd youtube-script
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your API keys
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

### Access the Service

- **Admin Dashboard**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **Health Check**: http://localhost:8001/health

## 📚 Documentation

Comprehensive documentation is available in the [`docs/`](docs/) directory:

- **[Installation Guide](docs/installation.md)** - Detailed installation instructions for Docker and local setup
- **[Configuration Guide](docs/configuration.md)** - Environment variables, API keys, and YouTube cookies setup
- **[Database Setup](docs/database.md)** - SQLite and PostgreSQL configuration, schema details
- **[Usage Guide](docs/usage.md)** - Admin dashboard usage, API examples, feature guides
- **[API Documentation](docs/api.md)** - Complete API reference with all endpoints
- **[Troubleshooting](docs/troubleshooting.md)** - Common issues and solutions

## 🎯 Basic Usage

### Admin Dashboard

1. Navigate to http://localhost:8001
2. Login with admin credentials (create first user via API)
3. Use the dashboard to:
   - Process YouTube channels
   - Transcribe videos
   - Generate AI content
   - Manage prompts and users

### API Example

```python
import requests
from requests.auth import HTTPBasicAuth

# Transcribe a video
response = requests.post(
    "http://localhost:8001/transcribe",
    json={"videos": ["abc123xyz45"]},
    auth=HTTPBasicAuth("admin", "admin")
)
result = response.json()
print(result['success'][0]['transcript'])
```

See [Usage Guide](docs/usage.md) for more examples.

## 🔐 Authentication

All API endpoints require authentication:

- **Basic Auth** (recommended for API): `username:password`
- **Bearer Token** (for dashboard): Get token from `/api/login` endpoint

See [Usage Guide - Authentication](docs/usage.md#authentication) for details.

## 🗄️ Database

The service supports two database backends:

- **SQLite** (default) - Perfect for development, no setup required
- **PostgreSQL** - Recommended for production

See [Database Setup Guide](docs/database.md) for configuration details.

## ⚙️ Configuration

Key environment variables:

```bash
DEEPGRAM_API_KEY=your-key          # Required
OPENAI_API_KEY=your-key            # Required for AI features
DB_TYPE=sqlite                      # or postgres
YOUTUBE_COOKIES=...                # Highly recommended
YOUTUBE_SLEEP_INTERVAL=2.0         # Rate limiting delay
```

See [Configuration Guide](docs/configuration.md) for complete setup.

## 🐛 Troubleshooting

Common issues and solutions:

- **Bot Detection**: Configure YouTube cookies (see [Configuration Guide](docs/configuration.md))
- **Rate Limiting**: Increase `YOUTUBE_SLEEP_INTERVAL` or wait before retrying
- **Database Errors**: Check connection settings and permissions
- **FFmpeg Not Found**: Install FFmpeg (see [Installation Guide](docs/installation.md))

See [Troubleshooting Guide](docs/troubleshooting.md) for detailed solutions.

## 📊 Project Status

- ✅ Video transcription
- ✅ Channel processing
- ✅ AI content generation
- ✅ Prompt management
- ✅ Bulk operations
- ✅ Admin dashboard
- ✅ Database storage
- ✅ API documentation

## 🤝 Contributing

Contributions are welcome! Please see the [Contributing Guidelines](CONTRIBUTING.md) (if available) or open an issue to discuss your changes.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source. Please check the LICENSE file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube video downloader
- [Deepgram](https://www.deepgram.com/) - Speech-to-text API
- [OpenAI](https://openai.com/) - GPT models for content generation

## 📞 Support

- **Documentation**: Check the [`docs/`](docs/) directory
- **API Docs**: http://localhost:8001/docs (when running)
- **Issues**: Report bugs or request features on GitHub Issues

---

**Made with ❤️ for the open source community**
