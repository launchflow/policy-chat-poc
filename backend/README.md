# gcp-saas-example

Welcome to BuildFlow!

In this example we will show you how to build a simple SaaS application that uses Google Cloud Platform (GCP) services. 
We will be building a simple application that allows users to log in with their **google credentials** and create, read, update, and delete (CRUD) journal entries that are stored in a postgres database hosted on [**Google Cloud SQL**](https://cloud.google.com/sql?hl=en).

In order to run this example you will need to have a GCP project with Cloud SQL enabled.

First rename `template.env` to `.env` and update all the TODO fields.

- **GCP_PROJECT_ID** point to your GCP project
- **DATABASE_PASSWORD** once you create your DB you will need to set a password for the postgres user and put it here
- **CLIENT_ID** this should be your [OAuth client ID from Google](https://developers.google.com/identity/protocols/oauth2)
- **CLIENT_SECRET** this should be your [OAuth client secret from Google](https://developers.google.com/identity/protocols/oauth2)

## Create your resources

Once your environment is set up run:

```
buildflow apply
```

This will create all of your cloud resources.


## Run your project

Update `CREATE_MODELS` in your `.env` to `True` and run:

```
buildflow run
```

Then you can visit http://localhost:8000 to see your project running.

## Directory Structure

At the root level there are three important files:

- `buildflow.yml` - This is the main configuration file for your project. It contains all the information about your project and how it should be built.
- `main.py` - This is the entry point to your project and where your `Flow` is initialized.
- `requirements.txt` - This is where you can specify any Python dependencies your project has.

Below the root level we have:

**gcps_saas_example**

This is the directory where your project code lives. You can put any files you want in here and they will be available to your project. We create a couple directories and files for you:

- **processors**: This is where you can put any custom processors you want to use in your project. Here we have several processor.
    - *auth.py*: This is where we define our endpoints for handling user authentication
    - *journals.py*: Here we defined our CRUD API for managing journal entries
    - *service.py*: This connects all our endpoints and setups our UI
- **primitives.py**: This is where you can define any custom primitive resources that your project will need. Here we set up our Cloud SQL instance and our Cloud SQL database.
- **dependencies.py**: Here we define dependencies for connecting to our database and for authenticating users.
- **schemas.py**: This file contains our dataclass schemas for requests and responses from our endpoints.
- **settings.py**: This file loads in our environment variables and makes them available to our project.

**.buildflow**

This is a hidden directory that contains all the build artifacts for your project. You can general ignore this directory and it will be automatically generated for you. If you are using github you probably want to put this in your *.gitignore* file.
