### MAKE VENV

```shell
    python -m venv .venv
```

### START VENV (WINDOWS 11 PS)
```shell
    .\.venv\Scripts\activate
```

### INSTALL DEPENDENCY
```shell
    pip install -r requirements.txt
```

### START PROJECT

```shell
    uvicorn app.main:app --reload
```