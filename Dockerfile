# Two targets:
#   test    - package with dev tools, used by CI for lint and unit tests
#   runtime - small image with only the installed package (default target)
FROM python:3.12-slim AS test
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_RETRIES=10 PIP_DEFAULT_TIMEOUT=30 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir -e ".[dev]"
COPY tests ./tests
COPY examples ./examples

FROM python:3.12-slim AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_RETRIES=10 PIP_DEFAULT_TIMEOUT=30
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/install .

FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1
COPY --from=builder /install /usr/local
RUN useradd --create-home edgeguard
USER edgeguard
WORKDIR /home/edgeguard
ENTRYPOINT ["edgeguard"]
CMD ["demo"]
