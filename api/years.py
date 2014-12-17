from flask import Blueprint, make_response, request, url_for, \
    session as flask_session
import json
from api.database import engine

years = Blueprint('years', __name__, url_prefix='/api/years')

@years.route('/')
def summary_by_year():
    ''' 
    Generate a summary by county of statistics by year
    '''
    table_type = 'res_area'
    sel = ''' 
        SELECT 
          a.total_jobs AS "2002",
          b.total_jobs AS "2003",
          c.total_jobs AS "2004",
          d.total_jobs AS "2005",
          e.total_jobs AS "2006",
          f.total_jobs AS "2007",
          g.total_jobs AS "2008",
          h.total_jobs AS "2009",
          a.county
        FROM (
          select 
            sum(total_jobs) as total_jobs, 
            substr(geocode, 1, 5) as county 
          from res_area_2002_jt00 
          where segment = 's000' 
          group by county
        ) AS a
        JOIN (
          select 
            sum(total_jobs) as total_jobs, 
            substr(geocode, 1, 5) as county 
          from res_area_2003_jt00 
          where segment = 's000' 
          group by county
        ) AS b
          ON a.county = b.county
        JOIN (
          select 
            sum(total_jobs) as total_jobs, 
            substr(geocode, 1, 5) as county 
          from res_area_2004_jt00 
          where segment = 's000' 
          group by county
        ) AS c
          ON a.county = c.county
        JOIN (
          select 
            sum(total_jobs) as total_jobs, 
            substr(geocode, 1, 5) as county 
          from res_area_2005_jt00 
          where segment = 's000' 
          group by county
        ) AS d
          ON a.county = d.county
        JOIN (
          select 
            sum(total_jobs) as total_jobs, 
            substr(geocode, 1, 5) as county 
          from res_area_2006_jt00 
          where segment = 's000' 
          group by county
        ) AS e
          ON a.county = e.county
        JOIN (
          select 
            sum(total_jobs) as total_jobs, 
            substr(geocode, 1, 5) as county 
          from res_area_2007_jt00 
          where segment = 's000' 
          group by county
        ) AS f
          ON a.county = f.county
        JOIN (
          select 
            sum(total_jobs) as total_jobs, 
            substr(geocode, 1, 5) as county 
          from res_area_2008_jt00 
          where segment = 's000' 
          group by county
        ) AS g
          ON a.county = g.county
        JOIN (
          select 
            sum(total_jobs) as total_jobs, 
            substr(geocode, 1, 5) as county 
          from res_area_2009_jt00 
          where segment = 's000' 
          group by county
        ) AS h
          ON a.county = h.county
    '''
    rows = []
    fields = ['2002', '2003', '2004', '2005', '2006', '2007', '2008', '2009', 'county']
    with engine.begin() as conn:
        rows = [dict(zip(fields, r)) for r in conn.execute(sel)]
    resp = make_response(json.dumps(rows))
    resp.headers['Content-Type'] = 'application/json'
    return resp
