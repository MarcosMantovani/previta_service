FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy everything
COPY . /app/

# Install dependencies
RUN pip install -r requirements.txt

# Debug: list files
RUN echo "=== FILES COPIED ===" && ls -la /app/ && echo "=== SH FILES ===" && find /app -name "*.sh" -type f

# Make scripts executable
RUN chmod +x /app/start-*.sh /app/wait-for-it.sh

# Run the app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8882"]
