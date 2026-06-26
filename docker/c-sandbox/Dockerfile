FROM debian:bookworm-slim
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc g++ libc6-dev \
 && rm -rf /var/lib/apt/lists/*
WORKDIR /submission
