from flask import Blueprint, make_response, request, url_for, \
    session as flask_session
import json

views = Blueprint('views', __name__)

@views.route('/')
def index():
    return ''' 
      <html>
        <head></head>
        <body>
          <div><h1>This is a placeholder</h1></div>
        </body>
      </html>
    '''
