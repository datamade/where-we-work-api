from flask import Blueprint, make_response, request, url_for, \
    session as flask_session
import json

job_types = Blueprint('job_types', __name__, url_prefix='/api/job_types')

@job_types.route('/')
def summary_by_job_type():
    ''' 
    Generate a summary of statistics by job_type
    '''
    resp = {}
    return make_response(json.dumps(resp))
