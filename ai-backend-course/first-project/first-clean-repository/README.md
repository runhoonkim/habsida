# Environment Configuration Demo

A small Python project demonstrating how to manage application configuration with environment variables using `python-dotenv`. The project loads both normal settings and secrets from a `.env` file without hard-coding them in the source code.

## Project Structure

```text
.
├── main.py
├── requirements.txt
├── .env
├── .env.example
└── .gitignore
```

## Setup

### 1. Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd <YOUR_PROJECT_FOLDER>
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate the virtual environment

**macOS / Linux:**

```bash
source .venv/bin/activate
```

**Windows:**

```powershell
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Configuration

Create your local `.env` file from the provided example:

```bash
cp .env.example .env
```

Then open `.env` and replace the placeholder values with values for your machine.

### Environment Variables

| Variable   | Description                                                          | Example         |
| ---------- | -------------------------------------------------------------------- | --------------- |
| `APP_NAME` | The name of the application. This is a normal configuration setting. | `My Python App` |
| `API_KEY`  | A secret API key used by the application. Keep this value private.   | `your-api-key`  |

For example:

```env
APP_NAME=My Python App
API_KEY=your-real-api-key
```

**Do not commit `.env` to Git.** It contains your real configuration and secrets.

The `.env.example` file contains only placeholder values and should be committed so that other developers know which environment variables are required.

## Run the Program

Make sure your virtual environment is activated, then run:

```bash
python main.py
```

Expected output:

```text
APP_NAME: My Python App
API_KEY loaded: True
```

The program intentionally **never prints the API key itself**. It only reports whether the secret was successfully loaded.

If a required environment variable is missing, the program exits with a clear message, for example:

```text
Error: Required variable API_KEY is missing from .env
```

## Security

Never commit secrets or other sensitive configuration to the repository.

The `.gitignore` file excludes `.env`, along with the virtual environment, Python cache files, and common OS/editor files.
