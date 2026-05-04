# Multi-stage build for aw-server-rust (central server)
FROM rust:1.82-bookworm AS builder

# Install Node.js for aw-webui build
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY aw-server-rust/ .

# Build aw-server in release mode (skip webui for faster builds; webui can be served separately)
RUN make build SKIP_WEBUI=true RELEASE=true

# Runtime stage
FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /build/target/release/aw-server /usr/local/bin/aw-server

# Data directory for ActivityWatch database
VOLUME ["/root/.local/share/activitywatch"]

EXPOSE 5600

ENTRYPOINT ["aw-server", "--host", "0.0.0.0", "--port", "5600"]
