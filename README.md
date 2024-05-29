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

Visualize a structure with a specific Protein Data Bank (PDB, see <https://rcsb.org>) accession code:

```
pipenv run python molviewgpt/py3dmolgpt.py [<PDB_CODE>]
```

For example, PDB code `1mbn` (hemoglobin, <https://www.rcsb.org/structure/1mbn>) is the default:

```
pipenv run python molviewgpt/py3dmolgpt.py 1mbn
```

Once the program is running, point your browser to open the generated local HTML file with name `molecule_visualization.html`

Example input in the dialog (not all examples yet functional):

* `show the protein in backbone representation` or `show as backbone`
* `show in green`
* `show non-protein parts as solid in red` or try `show ligands in red and as spheres` . Note: DOES NOT SEEM TO WORK AT THE MOMENT
* `highlight the active site` NOTE: Does not work yet - needs information obtained from UniProt to augment prompt with external inforaation
* `show in a way that explains the mechanism` : NOTE: Does not work yet - needs information obtained from UniProt to augment prompt with external inforaation
* `space-filling` or `show as spacefill`


For inspiration regarding protein structures see for example the Molecule of the Month series: <https://pdb101.rcsb.org/motm/142>


This will start a dialog using the plain command line interface.
To view the output, open with your web browser the generated file: `molecule_visualization.html`
Updates to the web-site can take about 30 seconds

