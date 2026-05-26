
def download_model_manually():
    import os
    import requests

    from pathlib import Path
    from dotenv import load_dotenv


    # Load .env
    load_dotenv()


    # Read variables
    parent_model_dir = Path(os.getenv("PARENT_MODEL_DIR"))
    model_name = os.getenv("MISTRAL_MODEL_NAME")


    # Create directory if not exists
    parent_model_dir.mkdir(parents=True, exist_ok=True)


    # Full model path
    model_path = parent_model_dir / model_name


    # Check if model already exists
    if model_path.exists():

        print("Model already downloaded.")
        print(f"Location: {model_path}")

    else:
        print("Starting download...")


        # Download URL
        url = (
            "https://huggingface.co/"
            "TheBloke/Mistral-7B-Instruct-v0.1-GGUF/"
            "resolve/main/"
            f"{model_name}"
        )


        response = requests.get(url, stream=True)


        if response.status_code == 200:

            total_size = int(response.headers.get("content-length", 0))
            downloaded_size = 0

            with open(model_path, "wb") as f:

                for chunk in response.iter_content(chunk_size=1024 * 1024):

                    if chunk:

                        f.write(chunk)

                        downloaded_size += len(chunk)

                        print(
                            f"Downloaded: "
                            f"{downloaded_size / (1024**3):.2f} GB / "
                            f"{total_size / (1024**3):.2f} GB",
                            end="\r"
                        )

            print("\nDownload complete!")
            print(f"Saved to: {model_path}")

        else:

            print(f"Download failed. Status code: {response.status_code}")



def download_with_ollama():
    import os
    import subprocess

    from dotenv import load_dotenv

    # Load .env file
    load_dotenv()

    # Read model path from .env
    ollama_models_path = os.getenv("PARENT_MODEL_DIR") ## Directory where the Ollama models are stored, this should be set in your .env file as OLLAMA_MODELS=/path/to/your/models

    print("Model path:", ollama_models_path) 

    # Set environment variable for current Python process
    os.environ["PARENT_MODEL_DIR"] = ollama_models_path

    # Pull model
    subprocess.run(["ollama", "pull", "mistral"]) ## This is same like running `ollama pull mistral` in terminal, it will pull the mistral model to your local machine and make it available for use in your application.

if __name__ == "__main__":
    # Uncomment the method you want to use for downloading the model

    # Method 1: Manual download using requests
    import time
    start_time = time.time()

    download_model_manually()
    end_time = time.time()
    print(f"Total download time: {end_time - start_time:.2f} seconds")
    # Method 2: Using Ollama CLI
    #download_with_ollama()