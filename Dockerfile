# Container image that runs your code
FROM alpine:3.10

RUN apk add --update nodejs npm git

RUN addgroup -S node && adduser -S node -G node

USER node

COPY entrypoint.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
