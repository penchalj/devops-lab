FROM python:3.12-slim
LABEL org.opencontainers.image.source="https://github.com/penchalj/devops-lab"

# Install latest Debian security updates (base image may lag behind)
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

# Run as a non-root user
RUN useradd --system --uid 10001 app
WORKDIR /app
COPY app.py .
USER app

ENV PORT=8000
EXPOSE 8000
HEALTHCHECK --interval=10s --timeout=3s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "app.py"]
