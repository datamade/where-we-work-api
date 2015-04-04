from flask import Blueprint, make_response, request, url_for, \
    session as flask_session
import json
from api.database import engine
from sqlalchemy import text
from collections import OrderedDict
from datetime import date

dthandler = lambda obj: obj.isoformat() if isinstance(obj, date) else None

geo = Blueprint('geo', __name__, url_prefix='/api/geo')

@geo.route('/')
def geo_summary():
    ''' 
    Generate a list of geography stats
    '''
    resp = {}
    return make_response(json.dumps(resp))

@geo.route('/vectors/<geoid>/')
def vectors(geoid):
    resp = {}
    char_type = request.args.get('char_type', 'res_area')
    year = request.args.get('year', '2011')
    job_type = request.args.get('job_type', 'jt00')
    char_type = request.args.get('char_type', 'res_area')
    table_name = 'origin_dest_{0}_{1}'.format(year, job_type)
    char_table_name = '{0}_{1}_{2}'.format(char_type, year, job_type)
    sel = """ 
        SELECT 
            ST_AsGeoJSON(ST_ShortestLine(b.geom, c.geom)) as line,
            ST_AsGeoJSON(c.geom) AS origin_geom,
            c.geoid10 as origin_geocode,
            ST_AsGeoJSON(b.geom) AS dest_geom
        FROM (
            SELECT 
                geom,
                geoid10
            FROM census_blocks 
            WHERE geoid10 = :geoid
        ) AS c, 
        {0} AS o 
        JOIN census_blocks AS b 
            ON o.h_geocode = b.geoid10
        WHERE h_geocode = :geoid
    """.format(table_name, char_table_name)
    resp = {
        "type": "FeatureCollection",
        "features": []
    }
    with engine.begin() as conn:
        rows = [dict(zip(r.keys(), r.values())) for r in conn.execute(text(sel), geoid=geoid)]
        for row in rows:
            feature = {
                'type': 'Feature',
                'geometry': json.loads(row['line']),
                'properties': OrderedDict([(k,v,) for k,v in zip(row.keys(), row.values())])
            }
            del feature['properties']['line']
            del feature['properties']['origin_geom']
            del feature['properties']['dest_geom']
            resp['features'].append(feature)
            feature = {
                'type': 'Feature',
                'geometry': json.loads(row['origin_geom']),
                'properties': {}
            }
            resp['features'].append(feature)
            feature = {
                'type': 'Feature',
                'geometry': json.loads(row['dest_geom']),
                'properties': {}
            }
            resp['features'].append(feature)
    r = make_response(json.dumps(resp, sort_keys=False, default=dthandler))
    r.headers['Content-Type'] = 'application/json'
    return r

@geo.route('/average-vector/')
def average_vector():
    char_type = request.args.get('char_type', 'res_area')
    year = request.args.get('year', '2011')
    job_type = request.args.get('job_type', 'jt00')
    char_type = request.args.get('char_type', 'res_area')
    table_name = 'origin_dest_{0}_{1}'.format(year, job_type)
    char_table_name = '{0}_{1}_{2}'.format(char_type, year, job_type)
    sel = '''
        select 
          st_asgeojson(
            st_shortestline(
              st_centroid(home.geom), 
              st_setsrid(
                st_point(
                  ((home.center_x - work.work_center_x) / 10 + home.center_x), 
                  ((home.center_y - work.work_center_y) / 10 + home.center_y)
                ), 4326) 
            )) as vector 
        from census_blocks as home 
        join center_of_work_2011 as work 
          on home.geoid10 = work.home_geo10
    '''
    resp = {
        "type": "FeatureCollection",
        "features": []
    }
    with engine.begin() as conn:
        rows = [dict(zip(r.keys(), r.values())) for r in conn.execute(text(sel))]
        for row in rows:
            feature = {
                'type': 'Feature',
                'geometry': json.loads(row['vector']),
                'properties': {}
            }
            resp['features'].append(feature)
    return make_response(json.dumps(resp))

@geo.route('/<geo_type>/')
def geo_type(geo_type):
    ''' 
    Get stats by geo_type, either "county" or "tract"
    '''
    resp = {}
    if geo_type not in ['county', 'tract', 'block']:
        resp['status'] = 'error'
        resp['message'] = 'Geography type should be either "county", "tract" or "block"'
    else:
        char_type = request.args.get('char_type', 'res_area')
        year = request.args.get('year', '2011')
        geoid = request.args.get('geoid')
        geo_col = geo_type
        geo_table = geo_type
        geoid_col = 'geoid'
        geoname_col = 'name'
        if char_type == 'res_area' and geo_type != 'block':
            table_name = 'jobs_by_{0}_{1}'.format(geo_type, year)
        elif char_type == 'work_area' and geo_type != 'block':
            table_name = 'workers_by_{0}_{1}'.format(geo_type, year)
        elif char_type == 'res_area' and geo_type == 'block':
            table_name = 'res_area_{0}_jt00'.format(year)
            geo_col = 'geocode'
            geo_table = 'census_blocks'
            geoid_col = 'geoid10'
            geoname_col = 'geoid10'
        elif char_type == 'work_area' and geo_type == 'block':
            table_name = 'work_area_{0}_jt00'.format(year)
            geo_col = 'geocode'
            geo_table = 'census_blocks'
            geoid_col = 'geoid10'
            geoname_col = 'geoid10'
        kwargs = {}
        sel = ''' 
          SELECT 
            g.{4},
            j.*, 
            ST_AsGeoJSON(g.geom) AS geom
          FROM {0} AS j
          JOIN {1} AS g
            ON j.{2} = g.{3}
        '''.format(table_name, geo_table, geo_col, geoid_col, geoname_col)
        if geoid:
            sel = '{0} WHERE g.{1} = :geoid'.format(sel, geoid_col)
            kwargs['geoid'] = geoid
        if geo_type == 'block':
            sel = '{0} AND j.segment = :segment'.format(sel)
            kwargs['segment'] = 's000'
        resp = {
            'type': 'FeatureCollection',
            'features': []
        }
        with engine.begin() as conn:
            result = conn.execute(text(sel), **kwargs)
            fields = result.keys()
            for row in result:
                vals = row.values()
                feature = {
                    'type': 'Feature',
                    'geometry': json.loads(vals[-1]),
                    'properties': OrderedDict([(k,v,) for k,v in zip(fields[:-1], vals[:-1])])
                }
                resp['features'].append(feature)
    r = make_response(json.dumps(resp, sort_keys=False, default=dthandler))
    r.headers['Content-Type'] = 'application/json'
    return r
