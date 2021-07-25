# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

# Install pip requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt \
    && rm -rf requirements.txt

WORKDIR /app
COPY . /app

RUN mkdir -p /app/.streamlit

RUN bash -c 'echo -e "\
[general]\n\
email = \"\"\n\
" > /app/.streamlit/credentials.toml'

RUN bash -c 'echo -e "\
[server]\n\
enableCORS = false\n\
" > /app/.streamlit/config.toml'

EXPOSE 8501

# Creates a non-root user with an explicit UID and adds permission to access the /app folder
# For more info, please refer to https://aka.ms/vscode-docker-python-configure-containers
RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app
USER appuser

# During debugging, this entry point will be overridden. For more information, please refer to https://aka.ms/vscode-docker-python-debug
ENTRYPOINT ["streamlit", "run"]
CMD ["emmaus_walking/app.py"]
