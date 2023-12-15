# Team Kangaroo Small Group project

## Team members
The members of the team are:
-   Simon Ha
-   Hannah Porteous
-   Xinyao (Anna) Liao
-   Amy Jassal 
-   Muhammad (Ahsan) Mahfuz

## Project structure
The project is called `task_manager`.  It currently consists of a single app `tasks`.

## Deployed version of the application
The deployed version of the application can be found at [kangarootaskaroo.pythonanywhere.com](https://kangarootaskaroo.pythonanywhere.com).

## Installation instructions
To install the software and use it in your local development environment, you must first set up and activate a local development environment.  From the root of the project:

```
$ virtualenv venv
$ source venv/bin/activate
```

Install all required packages:

```
$ pip3 install -r requirements.txt
```

Migrate the database:

```
$ python3 manage.py migrate
```

Seed the development database with:

```
$ python3 manage.py seed
```

Run all tests with:
```
$ python3 manage.py test
```
Run the javascript tests with:
```
$ firefox tasks/tests/test.html
(Or any browser instead of firefox)
```

## Sources
The packages used by this application are specified in `requirements.txt`