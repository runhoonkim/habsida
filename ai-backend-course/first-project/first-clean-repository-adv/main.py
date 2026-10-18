import os
import sys
from dotenv import load_dotenv

load_dotenv()

def main():
    # get required variables
    app_name = os.getenv("APP_NAME")
    api_key = os.getenv("API_KEY")

    # get optional variables
    is_debug = os.getenv("APP_DEBUG", "false").lower() == "true"
    port = os.getenv("PORT", "3000")
    host = os.getenv("HOST", "localhost")

    # if required varaibles are miissing, fail loudly
    missing_variables = []
    
    if not app_name:
        missing_variables.append("APP_NAME")

    if not api_key:
        missing_variables.append("API_KEY")

    if missing_variables:
        print(
            f"Error: Missing required environment variable(s): "
            f"{', '.join(missing_variables)}"
         )
        print("Please check your .env file.")
        sys.exit(1)

    # Print configuration safely
    print(f"APP_NAME: {app_name}")
    print(f"API_KEY loaded: {bool(api_key)}")
    print(f"APP_DEBUG: {is_debug}")
    print(f"PORT: {port}")
    print(f"HOST: {host}")

    if is_debug:
        print("Debug mode is enabled.")


if __name__ == "__main__":
    main()