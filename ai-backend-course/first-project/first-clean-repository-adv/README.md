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

## Recovering from an Accidental `.env` Commit

As part of this project, I intentionally simulated a common mistake: I committed a dummy `.env` file to Git.

The mistake was then corrected by removing `.env` from Git tracking while keeping the local file:

```bash
git rm --cached .env
```

The `.env` file was then added to `.gitignore` so that Git would ignore it in future commits:

```gitignore
.env
```

Finally, the fix was committed:

```bash
git add .gitignore
git commit -m "Stop tracking .env"
```

### What happened?

`git rm --cached .env` removed `.env` from the Git index, meaning Git stopped tracking the file. It **did not delete the local `.env` file** from my computer.

After adding `.env` to `.gitignore`, future changes to the local `.env` file are ignored by Git.

This demonstrates an important recovery workflow when a configuration file is accidentally added to a repository:

1. Remove the file from Git tracking with `git rm --cached .env`.
2. Add `.env` to `.gitignore`.
3. Commit the fix.
4. Keep using the local `.env` file for application configuration.

> **Important:** This exercise used a dummy `.env` file. If a real secret such as an API key has already been committed and pushed to a remote repository, simply removing the file from tracking is not enough. The exposed secret should be revoked or rotated, and the secret should be removed from the repository history if necessary.

## Run the Program

Make sure your virtual environment is activated, then run:

```bash
python main.py
```

Expected output:

```text
APP_NAME: My Python App
API_KEY loaded: True
APP_DEBUG: False
PORT: 3000
```

The program intentionally **never prints the API key itself**. It only reports whether the secret was successfully loaded.

Optional configuration variables have sensible defaults. For example:

* `APP_DEBUG` defaults to `false`.
* `PORT` defaults to `3000`.

If a required environment variable is missing, the program exits with a clear message instead of crashing. For example:

```text
Error: Missing required environment variable(s): API_KEY
Please check your .env file.
```

## Security

Never commit secrets or other sensitive configuration to the repository.

The `.gitignore` file excludes `.env`, along with the virtual environment, Python cache files, and common OS/editor files.

The `.env.example` file should contain only placeholder values and can safely be committed to the repository.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
