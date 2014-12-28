from flask import Blueprint, make_response, request, url_for, \
    session as flask_session, render_template
import json

views = Blueprint('views', __name__)

@views.route('/')
def index():
    return render_template('index.html')
