from flask import Blueprint, make_response, request, url_for, \
    session as flask_session
import json
from api.database import engine

years = Blueprint('years', __name__, url_prefix='/api/years')

@years.route('/')
def summary_by_year():
    ''' 
    Generate a summary of statistics by year
    '''
    resp = {}
    return make_response(json.dumps(resp))
