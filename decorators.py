from flask import redirect, render_template, request, session
from functools import wraps

# decorator code source: https://stackoverflow.com/questions/5678585/django-tweaking-login-required-decorator

def login_required(f):

    @wraps(f)
    def function(*args, **kw):
        if not (session.get('user_id')):
            return redirect('/login')
        else:
            return f(*args, **kw)
    return function
