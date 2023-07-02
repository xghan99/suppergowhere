FROM python:3.9-slim-buster

ENV APP_HOME /app
ENV PYTHONBUFFERED True
WORKDIR $APP_HOME 
ADD requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip install --no-cache-dir gunicorn
RUN groupadd -r app && useradd -r -g app app
COPY ./data ./data
COPY --chown=app:app ./frontend ./
USER app
CMD exec gunicorn --bind :$PORT --log-level info --workers 1 --threads 8 --timeout 0 app:server