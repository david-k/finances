# Local installation

Run the following in the root directory of this project (same directory as this
README) to install all dependencies:

```sh
python3 -m venv env
source env/bin/activate

python -m pip install -r requirements.txt
```

Then you can run the program as follows:
```sh
source env/bin/activate

# Run the gui
python -m my_finances.gui

# Run the command-line program
python -m my_finances.cli
```

# Running tests

```sh
python -m unittest discover
```
