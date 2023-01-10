# Api

## Requirements

1. [docker](https://docs.docker.com/get-docker/)
2. [docker-compose](https://docs.docker.com/compose/install/)

## Development

### Prepare hosts

Edit `etc/hosts` and add following entries:

    127.0.0.1    api.example.com

### Copy & update env variables

    cp .env.example .env

_Notes_: API keys stored in .env are missing. Contact another developer to obtain them.

### Bootstrap the app
    
    make bootstrap

_Notes_: API keys stored in the db are missing. Contact another developer to obtain them.


### Start the app
    
    make up

## Apps

### Django app

Django app is running on port [8000](http://api.example.com:8000/admin/).

### Mailhog

MailHog is an email-testing tool with a fake SMTP server underneath that we use to catch all emails during development.
Mailhog is running on port [8025](http://localhost:8025/).

## Test users

### Admin panel

| email                   | password   | role          |
|-------------------------|------------|---------------|
| superadmin@example.com  | password   | Super Admin   |
| staffmember@example.com | password   | Staff Member  |


### Dashboard

| email                    | password   | role          |
|--------------------------|------------|---------------|
| admin@example.com        | password   | Admin         |
| assetmanager@example.com | password   | Asset Manager |
| operator@example.com     | password   | Operator      |

### Dashboard routes

We automatically convert dashboard routes from typescript to python. To update the routes run:

    make generate_dashboard_routes
