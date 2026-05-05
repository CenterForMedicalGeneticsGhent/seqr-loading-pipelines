FROM docker:dind as BUILD
FROM ghcr.io/astral-sh/uv:python3.11-alpine AS UV_BUILD
FROM ghcr.io/astral-sh/uv:python3.11-bookworm AS BUILDER
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*
WORKDIR /
COPY pyproject.toml uv.lock .
RUN uv sync --group prod --no-group dev --locked

FROM hailgenetics/hail:0.2.138-py3.11
COPY --from=BUILD /usr/local/bin/docker /usr/local/bin/docker
COPY --from=UV_BUILD /usr/local/bin/uv /usr/local/bin/uv
COPY --from=BUILDER /.venv /.venv
ENV PATH="/.venv/bin:$PATH"
LABEL maintainer="Broad TGG"

ARG PIPELINE_RUNNER_APP_VERSION
ENV PIPELINE_RUNNER_APP_VERSION=${PIPELINE_RUNNER_APP_VERSION}

RUN curl -sSL https://sdk.cloud.google.com | bash
ENV PATH $PATH:/root/google-cloud-sdk/bin

COPY pyproject.toml uv.lock .

# Application Code
WORKDIR /loading_pipeline
COPY loading_pipeline/api api
COPY loading_pipeline/bin bin
COPY loading_pipeline/lib lib
COPY loading_pipeline/ops ops
COPY loading_pipeline/var/liftover var/liftover

# Special paths
COPY loading_pipeline/var/spark_config/spark-defaults.conf /usr/local/lib/python3.10/dist-packages/pyspark/conf/spark-defaults.conf
COPY loading_pipeline/bin/vep /vep


WORKDIR /
EXPOSE 6000 8082
CMD ["uv", "run", "python3", "-m", "loading_pipeline.api"]
