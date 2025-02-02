from invoke import task

@task
def runserver(c):
    c.run("python manage.py runserver")

@task
def migrate(c):
    c.run("python manage.py migrate")

@task
def makemigrations(c):
    c.run("python manage.py makemigrations")

@task
def createsuperuser(c):
    c.run("python manage.py createsuperuser")

@task
def test(c):
    c.run("python manage.py test")

@task
def shell(c):
    c.run("python manage.py shell")