from flask import Blueprint, make_response, request, url_for, \
    session as flask_session
import json
from api.database import engine
from sqlalchemy import text
from string import lowercase

years = Blueprint('years', __name__, url_prefix='/api/years')

GEO_RANGE = {
    'county': [1,5],
    'tract': [1,11],
}

@years.route('/')
def summary_by_year():
    ''' 
    Generate a summary of statistics by year
    '''
    job_type = request.args.get('job_type', 'jt00')
    year_range = request.args.get('year_range', '2002,2011')
    segment = request.args.get('segment', 's000')
    geography = request.args.get('geography', 'county')
    char_type = request.args.get('char_type', 'res_area')
    table_names = []
    begin_year, end_year = year_range.split(',')
    year_range = range(int(begin_year), int(end_year) + 1)
    geo_range = GEO_RANGE[geography]
    selects = []
    for idx, year in enumerate(year_range):
        table_names.append('{0}_{1}_{2}'.format(char_type, year, job_type))
        selects.append('{0}.total_jobs AS "{1}"'.format(lowercase[idx], year))
    subq_fmt = '''
        (SELECT 
          SUM(total_jobs) AS total_jobs, 
          substr(geocode, {0}, {1}) as {2}
         FROM {3} 
         WHERE segment = :segment
         GROUP BY {2}) AS {4}
         '''
    fmt_args = geo_range + [geography, table_names[0], lowercase[0]]
    from_subq = subq_fmt.format(*fmt_args)
    selects = 'SELECT {0}, a.{1} FROM {2}'\
        .format(', '.join(selects), geography, from_subq)
    for idx, table_name in enumerate(table_names[1:]):
        alias = lowercase[idx + 1]
        fmt_args = geo_range + [geography, table_name, alias]
        join_subq = subq_fmt.format(*fmt_args)
        selects += ' JOIN {0} ON a.{2} = {1}.{2}'\
            .format(join_subq, alias, geography)
    sel = text(selects)
    rows = []
    fields = [y for y in year_range] + [geography]
    with engine.begin() as conn:
        rows = [dict(zip(fields, r)) for r in conn.execute(sel, segment=segment)]
    r = {
        'meta': {
            'status': 'ok',
            'query': {
                'job_type': job_type,
                'years': year_range,
                'segment': segment,
                'char_type': char_type,
            },
            'result_count': len(rows)
        },
        'objects': rows
    }
    resp = make_response(json.dumps(r))
    resp.headers['Content-Type'] = 'application/json'
    return resp

@years.route('/<int:year>/')
def origin_dest(year):
    ''' 
    Origin destination by year
    '''
    job_type = request.args.get('job_type', 'jt00')
    segment = request.args.get('segment', 's000')
    geography = request.args.get('geography', 'county')
    char_type = request.args.get('char_type', 'res_area')
    geocode = request.args.get('geocode')
    if char_type == 'res_area':
        geo = 'home'
        t = 'jobs'
    else:
        geo = 'work'
        t = 'workers'
    fmt_args = [geo, segment, t, geography, year]
    sel = '''
        SELECT {0}, connected, {1}
        FROM connected_{2}_{3}_{4} 
        '''.format(*fmt_args)
    kwargs = {}
    if geocode:
        sel = '''
        {0} WHERE {1} = :geocode 
        '''.format(sel, geo)
        kwargs = {'geocode': geocode}
    sel = text(sel)
    fields = [geo, 'connected', segment]
    results = []
    with engine.begin() as conn:
        results = [dict(zip(fields, r)) for r in conn.execute(sel, **kwargs)]
    rows = []
    for row in results:
        d = {
            'origin': row[fields[0]],
            'counts': {k:v for k,v in zip(row[fields[1]], row[fields[2]])},
            'total': sum(row[fields[2]]),
        }
        rows.append(d)
    r = {
        'meta': {
            'status': 'ok',
            'query': {
                'job_type': job_type,
                'year': year,
                'segment': segment,
                'char_type': char_type,
            },
            'result_count': len(rows)
        },
        'objects': rows
    }
    resp = make_response(json.dumps(r))
    resp.headers['Content-Type'] = 'application/json'
    return resp
    
