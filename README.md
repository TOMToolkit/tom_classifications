# tom_classifications

Classifications!

This is an app designed to support different ways a broker can classify a target using the TOM

The documentation and a more detailed readme will come later.


## Installation Procedure

1. Install the package into your TOM environment:

"pip install tom_classifications"

2. In your project's "settings.py", add "tom_classifications" to your "INSTALLED_APPS" setting:
"INSTALLED_APPS = [
    ...
    'tom_classifications',
]"

3. Migrate your TOM's database to install the new database tables:
`./manage.py migrate`
