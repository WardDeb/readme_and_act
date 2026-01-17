FROM python:3.14-slim

WORKDIR /
COPY . .

RUN pip install .

ENTRYPOINT ["raa"]