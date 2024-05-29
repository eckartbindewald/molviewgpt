## How to run

### Setup of needed libraries:

```
cd molviewgpt
pip install pipenv
pipenv install
```

### Setup of OpenAI API Key:

Create or edit vile `.env` in the project home directory. Easiest is to edit file `_env_sample.txt`, replace `YOUR_API_KEY` with your OpenAI API Key and save the file under the name `.env`

In other words, in file `_env_sample.txt` change the line

```
OPENAI_API=YOUR_API_KEY
```

according to whatever your API key is.

Alternatively you specify the environment variable OPENAI_API with the usual ways depending on your operating system.


### Running the program:

```
pipenv run python molviewgpt/py3dmolgpt.py
```

This will start a dialog using the plain command line interface.
To view the output, open with your web browser the generated file: `molecule_visualization.html`
Updates to the web-site can take about 30 seconds

