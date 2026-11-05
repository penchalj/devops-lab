FROM python:3.12-slim

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
