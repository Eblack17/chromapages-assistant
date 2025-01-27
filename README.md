# Chromapages AI Assistant

A containerized AI chatbot built with LangChain and Google's Gemini AI model, designed to provide information about Chromapages' web design and development services.

## Features

- RAG (Retrieval Augmented Generation) implementation
- Real-time chat interface
- Knowledge base integration
- Containerized deployment
- GitHub Actions automation

## Tech Stack

- Python 3.12
- Flask
- LangChain
- Google Gemini AI
- Docker
- GitHub Actions

## Container Usage

You can pull and run the container directly from GitHub Container Registry:

```bash
docker pull ghcr.io/[your-username]/chromapages-assistant:latest
docker run -p 8080:8080 -e GOOGLE_API_KEY=your_api_key ghcr.io/[your-username]/chromapages-assistant:latest
```

Or build it locally:

```bash
docker build -t chromapages-assistant .
docker run -p 8080:8080 -e GOOGLE_API_KEY=your_api_key chromapages-assistant
```

## Environment Variables

- `GOOGLE_API_KEY`: Your Google AI API key
- `PORT`: Port to run the server on (default: 8080)

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/[your-username]/chromapages-assistant.git
cd chromapages-assistant
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API key
```

5. Run the application:
```bash
python app.py
```

## Deployment

The application is automatically built and deployed to GitHub Container Registry on push to the main branch. You can find the latest container image at:

```
ghcr.io/[your-username]/chromapages-assistant:latest
```

## License

MIT License 