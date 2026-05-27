with open("pyproject.toml", "r") as f:
    content = f.read()
content = content.replace('"Flask-Compress>=1.0",\n    "Flask-Compress>=1.0",', '"Flask-Compress>=1.0",')
with open("pyproject.toml", "w") as f:
    f.write(content)

with open("requirements-docker.txt", "r") as f:
    content = f.read()
content = content.replace("Flask-Compress>=1.0\nFlask-Compress>=1.0", "Flask-Compress>=1.0")
with open("requirements-docker.txt", "w") as f:
    f.write(content)
