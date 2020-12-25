ARG PYTHON_VERSION=3.8
ARG ENVIRONMENT=production

FROM python:${PYTHON_VERSION}

COPY requirements.txt ./requirements.txt
COPY requirements-dev.txt ./requirements-dev.txt
RUN pip install --no-cache-dir -r requirements.txt
RUN test '$ENVIRONMENT' != 'production' && pip install --no-cache-dir -r requirements-dev.txt

COPY . /app
WORKDIR /app

EXPOSE 8000
CMD ["uvicorn", "yaaccu.asgi:app", "--host", "0.0.0.0", "--reload"]
