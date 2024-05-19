import json
import os
import requests
import tempfile

# from PIL import Image
# import matplotlib.pyplot as plt
import time
import subprocess
import base64
import io

MODEL_OPENAI_3='gpt-3.5-turbo'
MODEL_OPENAI_VISION="gpt-4o" # "gpt-4-turbo" # "gpt-4-1106-vision-preview"
OPENAI_API="https://api.openai.com/v1/chat/completions"
PARAMS = {
    'cache_file':'_tmp_molgpt_cache.txt'
}

def calc_downscale_size(size_orig:tuple, size_new:tuple):
    facs = [0,0]
    facs[0] = size_new[0] / size_orig[0]
    facs[1] = size_new[1] / size_orig[1]
    facs_min = min(facs)
    if facs_min > 1:
        facs[0] = 1.0
        facs[1] = 1.0
    size_new2 = [round(size_orig[0]*facs[0]),round(size_orig[1]*facs[1]) ]
    return size_new2


def encode_image(img, downscale_to=(742,960), monochrome=True, verbose=True):
    """
    Function to encode the image. Even works with PDF files, in which cases it is first converted to JPG
    """
    if isinstance(img, str):
        image_path = img
        if image_path.endswith(".pdf"):
            output_path = image_path.replace(".pdf", '')
            jpg_filenames = convert_pdf_to_jpg(image_path, output_path)
            print("Wrote to image filenames:", jpg_filenames)
            img = Image.open(jpg_filenames[0]) # first page
        else:
            img = Image.open(image_path)
    if downscale_to is not None:
        scale_to = calc_downscale_size(img.size, downscale_to)
        img = img.resize(scale_to, Image.LANCZOS)  # LANCZOS is a good choice for downsampling
    # img_path2 = img_path + "_resized.png"
    # resized_img.save(img_path2, 'PNG')
    # img_path = img_path2
    
    if monochrome:
        img = img.convert('1')  # Convert image to monochrome

    # Save the image to a bytes buffer instead of a file
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG',optimize=True, compression_level=9)  # You can change the format to PNG or other supported formats

    # Encode the bytes image as base64
    img_base64 = base64.b64encode(img_byte_arr.getvalue()).decode('utf-8') 
    if verbose:
        print("Number of characters of base64 encoded image:", len(img_base64))   

    return img_base64


def run_command(command):
    # Execute the command using an interactive shell
    command_with_env = f"bash -i -c '{command}'"
    result = subprocess.run(command_with_env, shell=True, capture_output=True, text=True)
    
    return result.stdout, result.stderr, result.returncode


def run_system_command(command):
    # Use a temporary file to capture output
    output_file = "temp_output.txt"
    
    # Command with output redirection
    full_command = f"{command} > {output_file}" # 2>&1"
    
    # Execute the command
    return_code = os.system(full_command)
    
    # Read the output from the file
    with open(output_file, 'r') as file:
        output = file.read()
    
    # Optionally, clean up the temporary file
    os.remove(output_file)
    
    return {'stdout':output, 'return_code':return_code}


def get_response_from_cache(payload, cache_file='response_cache.json'):
    if cache_file is None:
        return None
    payload_key = json.dumps(payload, sort_keys=True)
    if os.path.exists(cache_file):
        with open(cache_file, 'r') as file:
            for line in file:
                cached_payload, cached_response = json.loads(line)
                if cached_payload == payload_key:
                    return cached_response
    return None

def save_response_to_cache(payload, response, cache_file='response_cache.json'):
    payload_key = json.dumps(payload, sort_keys=True)
    with open(cache_file, 'a') as file:
        json.dump((payload_key, response), file)
        file.write('\n')
    


def get_contents(response):
    contents = []
    if 'choices' in response:
        for i in range(len(response['choices'])):
            contents.append(response['choices'][i]['message']['content'])
    return contents


def generate_payload(prompt, model, images=[], n=1, max_tokens=4096, downscales=None, seed=8,
    encode_as_json=True, temperature=0.1):
    '''
    Generates "payload" datastructure needed for OpenAI server requestion. Typically used to prepare
    input for function `make_request_with_cache`

    Returns dictionary with needed data structure as shown in below example.
    Example:

    payload = {
    "model": MODEL_VISION,
    "n":n,
    "messages": [
        {
        "role": "user",
        "content": [
            {
            "type": "text",
            "text": """\
    This is a rasterized version of a PDF document page. \
    Previously, you were asked to generate HTML code that approximates the text content of it as close as possible. \
    {img_instructions}.

    Here is the prior HTML code:

    {{html}}

    No verbose should be present, return only the HTML code, including encapsulating <body> and <html> tags."""

            },
            { 
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
            }
        ]
        }
    ],
    "max_tokens": 4096
    }
    '''
    if encode_as_json:
        prompt = json.dumps(prompt)
    content = [
        {
        "type": "text",
        "text": prompt,
        },

    ]

    for image_counter in range(len(images)):
        image = images[image_counter]
        if isinstance(image, str):
            image = Image.open(image)
        downscale_to = None
        if downscales is not None:
            if isinstance(downscales, list):
                downscale_to = downscales[image_counter]
            elif isinstance(downscales, tuple):
                downscale_to = downscales
            base64_image = encode_image(image, downscale_to=downscale_to)
        else:
            base64_image = encode_image(image)
        content.append({ 
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
    assert isinstance(temperature, float) or isinstance(temperature, int)
    payload = {
    "model": model,
    "n":n,
    "messages": [
        {
        "role": "user",
        "content": content
        }
    ],
    "max_tokens": max_tokens,
    "seed":seed,
    "temperature":temperature
    }
    return payload

def openai_generate_headers(api_key):
    headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
    }
    return headers

def make_request_with_cache(url, payload, headers, cache_file='response_cache.json', retries=1000, server_pause_time=100,
    debug=True, default_wait=10):
    if cache_file is not None:
        cached_response = get_response_from_cache(payload, cache_file)
        if cached_response is not None and 'choices' in cached_response:
            return cached_response
    time.sleep(default_wait)
    # If no cache, make the actual request
    for retry in range(retries):
        try:
            if debug:
                print(f"Making API request to {url} with payload:")
                print(payload)
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                response_data = response.json()
                if isinstance(response_data, dict) and 'choices' in response_data:
                    # Save response to cache and return
                    if cache_file is not None:
                        save_response_to_cache(payload, response_data, cache_file)
                    return response_data
            else:
                print("Warning: server error response",response.status_code)
                print(response)
                retry_after = 100
                if 'Retry-After' in response.headers:
                    retry_after = response.headers['Retry-After']
                print(f"Waiting {retry_after} seconds before next server request")
                print('Response headers:')
                print(response.headers)
                # If response is not successful or doesn't contain 'choices', wait before retrying
                time.sleep(float(retry_after+20))
        except requests.exceptions.RequestException as e:
            print(f"Server request failed: {e}. Retry {retry} out of {retries} after pause of {server_pause_time} seconds...")
            print("The payload was:")
            print(payload)
            print(f"Again, the server request failed: {e}. Retry {retry} out of {retries} after pause of {server_pause_time} seconds...")
            time.sleep(server_pause_time)

    # If all retries are exhausted, raise an exception
    raise Exception(f"No proper server response after {retries} retries")


def response_from_prompt_openai(prompt, model, images=[], n=1, max_tokens=4096, api_key = os.getenv('OPENAI_API_KEY'),
    cache_file=PARAMS['cache_file'][0], retries=1000, server_pause_time=1000, url=OPENAI_API,
    downscales=None, temperature=0.1, verbose=True):
    """
    Convenience function for calling OpenAI
    """
    assert isinstance(model,str)
    assert isinstance(prompt, str)
    assert isinstance(temperature, float) or isinstance(temperature, int)
    payload = generate_payload(prompt, model, images=images, n=n, max_tokens=max_tokens, downscales=downscales,
        temperature=temperature)
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    if verbose:
        print("Calling OpenAI API with payload:")
        print(payload)
    result = make_request_with_cache(url, payload, headers, cache_file=cache_file, retries=retries, 
        server_pause_time=server_pause_time)
    return get_contents(result)


def generate_temporary_filename(suffix=None):
    temp_file = tempfile.NamedTemporaryFile(delete=True, suffix=suffix)
    temp_filename = temp_file.name
    temp_file.close()
    return temp_filename

def display_image(img):
    # Load the image
    if isinstance(img, str) and os.path.exists(img):
        img = Image.open(img)
    # Display the image
    img.show()


    
if __name__ == "__main__":
    pass


    