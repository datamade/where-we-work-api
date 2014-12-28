from flask import Blueprint, make_response, request, url_for, \
    session as flask_session
import json
from api.database import engine
from sqlalchemy import text
from collections import OrderedDict

geo = Blueprint('geo', __name__, url_prefix='/api/geo')

@geo.route('/')
def geo_summary():
    ''' 
    Generate a list of geography stats
    '''
    resp = {}
    return make_response(json.dumps(resp))

@geo.route('/<geo_type>/')
def geo_type(geo_type):
    ''' 
    Get stats by geo_type, either "county" or "tract"
    '''
    resp = {}
    if geo_type not in ['county', 'tract']:
        resp['status'] = 'error'
        resp['message'] = 'Geography type should be either "county" or "tract"'
    else:
        char_type = request.args.get('char_type', 'res_area')
        year = request.args.get('year', '2011')
        if char_type == 'res_area':
            table_name = 'jobs_by_{0}_{1}'.format(geo_type, year)
        else:
            table_name = 'workers_by_{0}_{1}'.format(geo_type, year)
        sel = text(''' 
          SELECT 
            g.name,
            j.*, 
            ST_AsGeoJSON(g.geom) AS geom
          FROM {0} AS j
          JOIN {1} AS g
            ON j.{1} = g.geoid
        '''.format(table_name, geo_type))
        resp = {
            'type': 'FeatureCollection',
            'features': []
        }
        with engine.begin() as conn:
            result = conn.execute(sel)
            fields = result.keys()
            for row in result:
                vals = row.values()
                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(vals[-1]),
                    'properties': OrderedDict([(k,v,) for k,v in zip(fields[:-1], vals[:-1])])
                }
                resp['features'].append(feature)
    r = make_response(json.dumps(resp, sort_keys=False))
    r.headers['Content-Type'] = 'application/json'
    return r

@geo.route('/<geo_type>/<fips>/')
def geo_type_fips(geo_type, fips):
    ''' 
    Get stats for one geography
    '''
    resp = {}
    return make_response(json.dumps(resp))
