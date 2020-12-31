ARG BUILD_PREFIX=
FROM ${BUILD_PREFIX}python:3.7-alpine
LABEL maintainer="Jens Frost <post@j-frost.dk>"

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY requirements.txt ./
RUN apk add --no-cache tini && \
    pip install --no-cache-dir -r requirements.txt

COPY user.toml.example ./user.toml
COPY default.toml ./
COPY nextcloudinflux.py ./

ENTRYPOINT [ "tini", "--" ]
CMD [ "python", "./nextcloudinflux.py" ]
