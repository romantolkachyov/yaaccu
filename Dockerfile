ARG PYTHON_VERSION=3.8

FROM python:${PYTHON_VERSION} as dev

COPY requirements.txt ./requirements.txt
RUN mkdir /wheels
RUN pip wheel -w /wheels --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt --find-links /wheels

COPY requirements-dev.txt ./requirements-dev.txt
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY . /app
WORKDIR /app

EXPOSE 8000
CMD ["uvicorn", "yaaccu.app:app", "--host", "0.0.0.0", "--reload"]

FROM python:${PYTHON_VERSION} as production

COPY --from=dev /wheels /wheels
COPY requirements.txt ./requirements.txt
RUN pip install -r requirements.txt --find-links /wheels

RUN rm -Rf /wheels

COPY . /app
WORKDIR /app

EXPOSE 8000
CMD ["uvicorn", "yaaccu.app:app", "--host", "0.0.0.0", "--reload"]
