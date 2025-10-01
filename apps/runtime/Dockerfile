# ---------- Builder ----------
FROM golang:1.23-alpine AS builder
WORKDIR /src
ENV CGO_ENABLED=0

COPY go.mod ./
RUN go mod download

COPY . .
RUN go build -o /out/runtime ./cmd/runtime

# ---------- Runtime ----------
FROM alpine:3.20
WORKDIR /app
COPY --from=builder /out/runtime /usr/local/bin/runtime

ENV RUNTIME_INBOX=/queue/inbox     RUNTIME_OUTBOX=/queue/outbox     POLL_INTERVAL_MS=500

RUN mkdir -p /queue/inbox /queue/outbox
VOLUME ["/queue"]

ENTRYPOINT ["/usr/local/bin/runtime"]
