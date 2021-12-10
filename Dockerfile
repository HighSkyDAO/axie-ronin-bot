# Builder
FROM python:3.7.12-alpine3.15 as builder

# Set up workdir and env variables
WORKDIR /usr/src/app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Build dependencies
COPY ./requirements.txt .
RUN apk update \
    && apk add build-base \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /usr/src/app/wheels -r requirements.txt

# Final stage
FROM python:3.7.12-alpine3.15

# Set up workdir and env variables
WORKDIR /usr/src/app
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Copy application code
COPY . /usr/src/app/

# Copy build dependencies from the build stage
COPY --from=builder /usr/src/app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Run the app
CMD [ "python", "./bot2.py" ]