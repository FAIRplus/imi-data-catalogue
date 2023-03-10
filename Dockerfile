# Builder stage installs python requirements and builds front-end assets

# Version locked to 3.7, see https://hub.docker.com/_/python
FROM python:3.7-buster as builder

# Force standard IO streams to be unbuffered, 
#  see https://docs.python.org/2/using/cmdline.html#cmdoption-u
ENV PYTHONUNBUFFERED 1

# Set working directory to /code
WORKDIR /code

# Install the requirements (java for Flask Assets, node/npm for fetching the front-end, ldap for python-ldap)
RUN mkdir -p /code /static && \
    apt-get update && \
    apt-get install -y openjdk-11-jdk nodejs npm build-essential python3-dev python2.7-dev libldap2-dev libsasl2-dev ldap-utils && \
    npm install -g lessc less

# Add list of python requirements
COPY setup.py /code/

# Install python requirements
RUN mkdir -p /code/datacatalog/static/vendor && \
    pip install -e .  \
                --default-timeout=180 2>/dev/null || true && \
    pip install -r requirements-dev.txt \
                --default-timeout=180 2>/dev/null || true && \
    pip install gunicorn && \
    pip list -vvv

# Add the assets
COPY ./datacatalog/static /code/datacatalog/static

# Compile the assets
RUN cd /code/datacatalog/static/vendor && \
    npm ci && \
    npm run build && \
    cd /code

# Add the source code (therefore if any backend-related file changes, the build will pick up cache from previous step)
COPY . /code/

# Compile the assets with Flask-Assets
RUN python manage.py assets build

# Complete the installation of the package
RUN pip install -e . && cp -r /code/datacatalog/static/* /static/

# In case you'd like to debug stuff, then the following line would run flask's debug server
# Note, that when using docker-compose, it gets overridden (see `entrypoint` and `cmd` of docker-compose.yml)
ENTRYPOINT ["python"]
CMD ["manage.py", "runserver", "--host", "0.0.0.0"]
