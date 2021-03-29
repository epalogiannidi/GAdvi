FROM python:3.7 as base

RUN pip install virtualenv
ENV VIRTUAL_ENV=/venv
RUN virtualenv venv -p python3
ENV PATH="VIRTUAL_ENV/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    unixodbc-dev \
    unixodbc \
    libpq-dev

WORKDIR /app
ADD . /app

# Install dependencies
RUN pip install -r requirements.txt

# Expose port
EXPOSE 5000

# Run the application:
CMD ["python", "server.py"]
