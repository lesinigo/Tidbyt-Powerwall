FROM docker.io/alpine:3.19

RUN apk add --no-cache python3 py3-pip py3-pillow py3-requests tzdata && \
    adduser -D user

ENV PIP_BREAK_SYSTEM_PACKAGES=1
WORKDIR /app
COPY src LICENSE README.md pyproject.toml /app/
RUN pip3 install --no-cache-dir --editable .

USER user
ENTRYPOINT ["tidbyt_powerwall"]
