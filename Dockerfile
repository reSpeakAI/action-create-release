# Container image that runs your code
FROM python:3.10.2-alpine3.15
RUN export PYTHONPATH="${PYTHONPATH}:/src/"

COPY ./requirements.txt .
RUN apk --update add build-base libffi-dev
RUN pip install --no-cache-dir -r requirements.txt
COPY ./src /src

RUN chmod +x /src/entrypoint.py
ENTRYPOINT ["/src/entrypoint.py"]