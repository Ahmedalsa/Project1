from flask import redirect, render_template, request, session
from functools import wraps

# code source: https://stackoverflow.com/questions/5678585/django-tweaking-login-required-decorator

def login_required(function):
    def wrapper(*args, **kw):
        if not (session.get('user_id')):
            return redirect('/login')
        else:
            return function(*args, **kw)
    return wrapper
