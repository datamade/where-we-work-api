from subprocess import Popen, PIPE
from table_defs import WORK_AREA_CREATE, RES_AREA_CREATE, OD_CREATE
import psycopg2
import os
from cStringIO import StringIO
import csv
import gzip

COUNTIES = [
    '17031', 
    '17111', 
    '17037',
    '17063',
    '17093',
    '17197',
    '18127',
    '17097', 
    '17043', 
    '18111', 
    '17089', 
    '18073', 
    '18089', 
    '55059'
]

DB_USER = 'postgres'
DB_HOST = 'localhost'
DB_NAME = 'lodes'
DB_PORT = '5433'
DB_CONN_STR = 'host={0} dbname={1} user={2} port={3}'\
    .format(DB_HOST, DB_NAME, DB_USER, DB_PORT)

SEGMENTS = [
    's000',
    'sa01',
    'sa02',
    'sa03',
    'se01',
    'se02',
    'se03',
    'si01',
    'si02',
    'si03',
]

def create_tables():
    counter = 0
    with psycopg2.connect(DB_CONN_STR) as conn:
        with conn.cursor() as curs:
            for year in range(2002,2012):
                for jt in range(6):
                    job_type = 'jt{0}'.format(str(jt).zfill(2))
                    curs.execute(OD_CREATE.format(year, job_type))
                    curs.execute(WORK_AREA_CREATE.format(year, job_type))
                    curs.execute(RES_AREA_CREATE.format(year, job_type))
                    counter += 1
    print 'Created or found all {0} tables'.format(counter)

TABLE_LOOKUP = {
    'od': 'origin_dest',
    'rac': 'res_area',
    'wac': 'work_area',
}

def iterfiles(params, dirname, names):
    for name in names:
        fpath = os.path.join(dirname, name)
        if os.path.isfile(fpath) and fpath.endswith('.gz'):
            load_area(fpath)

def load_area(fpath):
    fname = os.path.basename(fpath)
    parts = fname.split('_')
    table_type = parts[1]
    data_year = parts[-1].split('.')[0]
    if table_type == 'od':
        job_type = parts[3].lower()
    else:
        segment, job_type = parts[2].lower(), parts[3].lower()
    main_table = TABLE_LOOKUP[fname.split('_')[1]]
    out = StringIO()
    writer = csv.writer(out)
    with gzip.GzipFile(fpath) as f:
        reader = csv.reader(f)
        headers = reader.next()
        for row in reader:
            work, home = unicode(row[0][:5]), unicode(row[1][:5])
            if work in COUNTIES or home in COUNTIES:
                if table_type == 'od':
                    writer.writerow([row[0], row[1]])
                else:
                    row.append(segment)
                    writer.writerow(row)
    out.seek(0)
    copy_st = ''' 
        COPY {0}_{1}_{2} FROM STDIN CSV
    '''.format(main_table, data_year, job_type)
    with psycopg2.connect(DB_CONN_STR) as conn:
        with conn.cursor() as curs:
            try:
                curs.copy_expert(copy_st, out)
            except psycopg2.IntegrityError:
                conn.rollback()
    print 'Loaded {0}'.format(fname)
    return None

if __name__ == "__main__":
    import sys
    basedir = sys.argv[1]
    create_tables()
    os.path.walk(basedir, iterfiles, None)
   #with psycopg2.connect(DB_CONN_STR) as conn:
   #    with conn.cursor() as curs:
   #        for year in range(2002,2012):
   #            for jt in range(6):
   #                job_type = 'jt{0}'.format(str(jt).zfill(2))
   #                curs.execute('CREATE INDEX ON origin_dest_{0}_{1}(h_geocode)'.format(year, job_type))
   #                curs.execute('CREATE INDEX ON origin_dest_{0}_{1}(w_geocode)'.format(year, job_type))