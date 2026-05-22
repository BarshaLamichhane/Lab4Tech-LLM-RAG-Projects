import requests

# URL of the model file
url = "mistral-7b-instruct-v0.1.Q4_0.gguf"  # Replace with the actual URL of the model file


# Path where the model will be saved
save_path = f'../../models/{url.split("/")[-1]}'  # Save in the models directory with the same filename

response = requests.get(url, stream=True)

# Check if the download was successful
if response.status_code == 200:
    # Open the file in write-binary mode and save the content
    # with open(save_path, 'wb') as f:
    #     for chunk in response.iter_content(chunk_size=1024):
    #         if chunk:
    #             f.write(chunk)
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)


    print(f'Model downloaded successfully and saved to {save_path}')
else:
    print('Error downloading the model.')
