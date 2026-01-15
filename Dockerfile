FROM python:3.14-slim

WORKDIR /
COPY . .

RUN pip install .

ENTRYPOINT [
    "raa",
    '--username', '${GH_USERNAME}',
    '--filename', '${FILE_NAME}',
    '--max_lines', '${MAX_LINES}',
    '--repo', '${REPO_NAME}',
]