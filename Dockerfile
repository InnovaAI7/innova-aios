FROM python:3.12-slim

WORKDIR /app

# Install Node.js (required for Claude Code CLI)
RUN apt-get update && apt-get install -y curl && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# Ensure writable home directory for Claude CLI config/sessions
ENV HOME=/root
RUN mkdir -p /root/.claude/sessions

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run the Telegram bot
CMD ["python", "-m", "apps.command.main"]
