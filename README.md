# Stepwise

## Development

[API](./api/README.md)

[Dashboard](./api/README.md)


## Git hooks

To start using git hooks you need to install `pre-commit` package:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip3 install pre-commit
```

and then install the hooks in your git repo:

```bash
pre-commit install
```

From now on, before each commit your code will be formatted and quality-checked.
