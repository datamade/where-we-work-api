from flask import Blueprint, make_response, request, url_for, \
    session as flask_session
import json

segments = Blueprint('segments', __name__, url_prefix='/api/segments')

@segments.route('/')
def summary_by_segment():
    ''' 
    Generate a summary of statistics by segment
    '''
    resp = {}
    return make_response(json.dumps(resp))
