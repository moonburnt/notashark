# Set image to latest available alpine, as for the moment of writing this
FROM alpine:3.17

# We won't want to run our program as superuser, right?
RUN adduser --uid 10000 --system --ingroup users --home /home/user user

# Install system dependencies
RUN apk add python3 py3-setuptools py3-pip --no-cache

# From there forward, switch to non-root
USER user

# Copy our bot's files into container
RUN mkdir /home/user/notashark

# Ensure pip install won't complain
ENV PATH="/home/user/.local/bin:$PATH"

WORKDIR /home/user/notashark
COPY ./setup.py setup.py
COPY ./notashark/* notashark/
COPY ./README.md README.md

# Build bot
RUN pip install .

# Configure the entrypoint
ENTRYPOINT ["python3", "notashark"]

# CMD ["--show-logs"]
