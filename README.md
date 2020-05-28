# FAIRplus imi-data-catalogue

**Name:** FAIRplus catalogue for IMI projects and associated Datasets

**Goal:** Create a database of IMI funded **projects** and their associated **datasets**

Local installation of development environment and procedure for docker version are described below. 

## Table of content

  * [Local installation](#local-installation)
  	* [Requirements](#requirements)
	* [Procedure](#procedure)
	* [Testing](#testing)
  * [Docker-compose build](#docker-compose-build)
  	* [Requirements](#requirements-for-docker-compose-build)
	* [Building](#building)
	* [Maintenance](#maintenance-of-docker-compose)
	* [Modifying the datasets](#modifying-the-datasets)
  * [Single Docker deployment](#single-docker-deployment)
  
## Local installation

### Requirements

Python ≥ 3.7
Solr ≥ 8.2

### Procedure

1. Install python requirements with:

    ```
    python setup.py install
    ```

1. The less compiler needs to be installed to generate the css files.

    ```
    sudo npm install less -g
    ```

1. Create the setting.py file by copying the template:
    ```
    cp datacatalog/settings.py.template datacatalog/settings.py
    ```
1. Modify the setting file according to your local environment.
   The SECRET_KEY parameter needs to be filled with a random string.
   For maximum security, generate it using python:
   ```python
   import os
   os.urandom(24)
    ```
1. Install the npm dependencies with:

    ```bash
    cd datacatalog/static/vendor
    npm install
    ```
1. Create a solr core
    ```bash
    $SOLR_INSTALLATION_FOLDER/bin/solr create_core -c datacatalog
    ```

1. Back to the application folder, build the assets:

    ```
    ./manage.py assets build
    ```

1. Initialize the solr schema:

    ```
    ./manage.py init_index
    ```
1. Index the provided datasets:

     ```
     ./manage.py import_entities Json dataset
     ```

1. Run the development server:

    ```
    ./manage.py runserver
    ```
The application should now be available under http://localhost:5000

### Testing
To run the unit tests:

```
python setup.py test
```

Note that a different core is used for tests and will have to be created.
By default, it should be called datacatalog_test.
## Docker-compose build
Thanks to docker-compose, it is possible to easily manage all the components (solr and web server) required to run the application.

### Requirements for docker-compose build

Docker and git must be installed.

### Building

`(local)` and `(web container)` indicate context of execution.

1. First, generate the certificates that will be used to enable HTTPS in reverse proxy. To do so, execute `deploy/nginx/generate_keys.sh` (relies on OpenSSL).
If you don't plan to use HTTPS or just want to see demo running, you can skip this (warning - it would cause the HTTPS connection to be unsafe!).

1. Then, copy `settings.py.template` to `settings.py`. Edit the `settings.py` file to add a random string of characters in `SECRET_KEY` and then run:

	```
	(local) $ docker-compose up --build
	```
	
	That will create a container with datacatalog web application, and a container for solr (the data will be persisted between runs).

1. Then, to create solr cores, execute in another console:

	```
	(local) $ docker-compose exec solr solr create_core -c datacatalog
	(local) $ docker-compose exec solr solr create_core -c datacatalog_test
	
	```

1. Then, to fill solr data:  

	```
	(local) $ docker-compose exec web /bin/bash
	(web container) $ python manage.py init_index 
	(web container) $ python manage.py import_entities Json dataset 
	
	(PRESS CTRL+D or type: "exit" to exit)
	```
1. The web application should now be available with loaded data via https://localhost  

### Maintenance of docker-compose
Docker container keeps the application in the state that it has been when it was built. 
Therefore, if you change any files in the project, in order to see changes in application the container has to be rebuilt:

```
docker-compose up --build
```

If you wanted to delete solr data, you need to run (that will remove any persisted data - you must redo `solr create_core`):

```
docker-compose down --volumes
```

### Modifying the datasets

The datasets are all defined in the file `tests/data/records.json`.
This file can me modified to add, delete and modify datasets.
After saving the file, rebuild and restart docker-compose with:

```
CTLR+D
```
to stop all the containers

```
docker-compose up --build
```
to rebuild and restart the containers

```
(local) $ docker-compose exec web /bin/bash
(web container) $ python manage.py import_entities Json dataset 

(PRESS CTRL+D or type: "exit" to exit)
```
To reindex the datasets

## Single Docker deployment
In some cases, you might not want Solr and Nginx to run (for example if there are multiple instances of Data Catalog runnning).
Then, simply use:

```
(local) $ docker build . -t "data-catalog"
(local) $ docker run --name data-catalog --entrypoint "gunicorn" -p 5000:5000 -t data-catalog -t 600 -w 2 datacatalog:app --bind 0.0.0.0:5000
```
