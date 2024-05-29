import py3Dmol
import json
import servertools
import time
import os
from dotenv import load_dotenv

load_dotenv()

if not os.getenv("OPENAI_API"):
    os.environ["OPENAI_API"] = input("Enter your OpenAI API key:")


MODEL='gpt-4o'

PROMPT_TEMPLATE = """
You are py3dmolGPT. For a given user input, you are supposed to generate the style information commands
to be used by py3Dmol as 2 dictionaries for the selection and the style content, to be enclosded in tags
<selection>...</selection> and <molstyle>...</molstyle>.

Example:

User input:
'''
Show me the protein in green form. 
'''

The response should be:
'''
<selection>
{{}}
</selection>
<molstyle>
"stick": {{"colorscheme": "yellowCarbon"}}
</molstyle>
'''

The user input was:

'''
{user_input}
'''

"""

def save_html(view, html_file='molecule_visualization.html'):
    """Saves the current state of the viewer to an HTML file."""

    html_content = view._make_html()
    complete_html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Molecular Visualization</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <!-- Include additional styles or scripts here if necessary -->
</head>
<body>
    {html_content}
</body>
</html>"""
    refresh_head = '<meta http-equiv="refresh" content="5" />'  # Refresh every 5 seconds
    complete_html = complete_html.replace('<head>', '<head>' + refresh_head)
    print(f"Saving HTML file {html_file} to be viewed in browser")
    with open(html_file, "w") as file:
        file.write(complete_html)

    print("Visualization saved to molecule_visualization.html. Please open this file in a web browser.")


def create_viewer(pdb_code:str):
    """
    Creates and returns a py3Dmol view for a given PDB ID
    
    Args:

        pdb_code(str): 4-character PDB accession code according to <https://rcsb.org>
    """
    view = py3Dmol.view(query=f'pdb:{pdb_code}')
    view.setStyle({'cartoon': {'color': 'spectrum'}})
    view.zoomTo()
    return view


def parse_user_json(text, default = {}):
    text = text.strip()
    if not (text.startswith("{") and text.endswith("}") ):
        text = '{ ' + text + ' }'
    try:
        result = json.loads(text)
        return result
    except Exception as e:
        print(f"Could not parse JSON string: {e}")
    return default


def apply_user_commands(view, selection, style):
    """Applies user input commands to modify the molecular visualization."""
    print("Applying selection:")
    print(selection)
    print("Applying style:")
    print(style)
    try:
        # Parse JSON input into Python dictionaries
        if isinstance(selection, str):
            selection = parse_user_json(selection)
            # selection = json.loads(selection)
        if isinstance(style, str):
            style = parse_user_json(style) # json.loads(style)
        # Execute the command in the context of the 'view' object
        print("Parsed selection:", selection)
        print("Parsed style:", style)
        view.setStyle(selection, style)
        save_html(view)
    except Exception as e:
        print(f"Error parsing text: {e}")


def strip_from(text, prefix=None, postfix=None, require=False):
    print("Processing text:")
    print(text)
    if prefix:
        pos = text.find(prefix)
        if pos >= 0:
            text = text[pos+len(prefix):]
        else:
            if require:
                return None
    if postfix:
        pos = text.rfind(postfix)
        if pos >= 0:
            text = text[:pos]
        else:
            if require:
                return None
    return text

import sys

if __name__ == "__main__":
    selection = '{}' # "chain": "A", "resi": [50, 55]}'
    style = '{"cartoon": {"colorscheme": "yellowCarbon"} }'
    pdb_code = "1mbn" 
    if len(sys.argv) > 1:
        pdb_code = sys.argv[1]
    if len(pdb_code) != 4:
        print("Warning: the first parameter should be a PDB code consisting of 4 characters (for example '1mbn'")
    print("Visualizing molecular structure corresponding to PDB accession code", pdb_code)
    print(f"For information from the PDB database seet: https://www.rcsb.org/structure/{pdb_code}")
    viewer = create_viewer(pdb_code)
    save_html(viewer)
    # viewer.show()
    while True:
        apply_user_commands(viewer, selection, style)

        user_input = input("Plain text command:")
        prompt = PROMPT_TEMPLATE.format(user_input=user_input)
        response = servertools.response_from_prompt_openai(prompt, model=MODEL)
        if not response:
            print("Strange, no command from user obtained")
            time.sleep(10)
            continue
        response = response[0]
        selection_input =  strip_from(response, '<selection>', '</selection>')
        if selection_input:
            # if not selection_input.startswith("{"):
            #     selection_input = '{' + selection_input + '}'
            selection = selection_input
        style_input =  strip_from(response, '<molstyle>', '</molstyle>')
        if style_input:
            # if not style_input.startswith("{"):
            #     style_input = '{' + style_input + '}'
            style = style_input

    