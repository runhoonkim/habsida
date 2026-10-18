import os
from dotenv import load_dotenv

load_dotenv()

def main():
    # loads configuration from a .env file using python-dotenv;
    # reads at least two variables — 
    # one plain setting (for example APP_NAME) and one that represents a secret (for example API_KEY);

    app_name = os.getenv("APP_NAME")
    api_key = os.getenv("API_KEY")

    # exits with a clear message if a required variable is missing, instead of crashing.
    if not app_name:
        print("Error: Required variable APP_NAME is missing from .env")

    if not api_key:
        print("Error: Required variable API_KEY is missing from .env")

    # prints the plain setting, and prints only whether the secret was found — never the secret itself (e.g. API_KEY loaded: True);
    print(f"The app name is {app_name}.")
    print("The API key is loaded.")

if __name__ == "main":
    main()