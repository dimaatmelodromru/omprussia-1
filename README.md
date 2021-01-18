# Simple image preview generator

## Requirements

```python3 -m pip install -r requirements.txt```

or

```python3 -m pip install jinja2```

## Usage

```
$./icon-preview.py --help
usage: icon-preview.py [-h] [--small] [--medium] [--large] [--cover]
                       icons template result

Icon preview generator CLI tool

positional arguments:
  icons       Icons path
  template    Template path (otherwise default.html is used)
  result      Result HTML file path (with filename)

optional arguments:
  -h, --help  show this help message and exit
  --small     Small icons
  --medium    Medium icons
  --large     Large icons
  --cover     Cover icons
```

