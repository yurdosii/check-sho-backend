FROM python:3

ENV PYTHONUNBUFFERED=1
ENV APP_WORKDIR=/code

WORKDIR $APP_WORKDIR
COPY requirements.txt $APP_WORKDIR
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev gcc musl-dev && \
    pip install -r requirements.txt && \
    apt-get install -y gcc musl-dev netbase && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
COPY . $APP_WORKDIR

COPY docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]
