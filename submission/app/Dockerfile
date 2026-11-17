# 1. Start from an official base image
FROM python:3.11-slim

# 2. Set the working directory inside the image
WORKDIR /app

# 3. Copy the dependency list and install it
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the application code
COPY . .

# 5. Document the port the app uses
EXPOSE 8000

# 6. The command that runs when a container starts
CMD ["python", "main.py"]

