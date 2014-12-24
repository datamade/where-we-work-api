from subprocess import Popen, PIPE
from table_defs import WORK_AREA_CREATE, RES_AREA_CREATE, OD_CREATE
import psycopg2
import os
from cStringIO import StringIO
import csv
import gzip
from sqlalchemy import create_engine, Table, MetaData, Column, String, Float
from sqlalchemy.dialects.postgresql import TIMESTAMP
from geoalchemy2 import Geometry
from shapely.geometry import MultiPolygon, asShape
import zipfile
import shapefile

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
DB_HOST = '127.0.0.1'
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
        elif os.path.isfile(fpath) and fpath.endswith('.zip'):
            load_shapes(fpath)
        else:
            print "I don't know what to do with {0}".format(fpath)

GEO_TYPE_MAP = {
    'C': String,
    'N': Float,
    'L': Float,
    'D': TIMESTAMP,
}

def load_shapes(fpath):
    content = StringIO()
    file_contents = open(fpath, 'r')
    content.write(file_contents.read())
    content.seek(0)
    shp = StringIO()
    dbf = StringIO()
    shx = StringIO()
    with zipfile.ZipFile(content, 'r') as f:
        for name in f.namelist():
            if name.endswith('.shp'):
                shp.write(f.read(name))
            if name.endswith('.shx'):
                shx.write(f.read(name))
            if name.endswith('.dbf'):
                dbf.write(f.read(name))
    shp.seek(0)
    shx.seek(0)
    dbf.seek(0)
    shape_reader = shapefile.Reader(shp=shp, dbf=dbf, shx=shx)
    fields = shape_reader.fields[1:]
    records = shape_reader.shapeRecords()
    columns = []
    for field in fields:
        fname, d_type, f_len, d_len = field
        col_type = GEO_TYPE_MAP[d_type]
        kwargs = {}
        if d_type == 'C':
            col_type = col_type(f_len)
        elif d_type == 'N':
            col_type = col_type(d_len)
        if fname.lower() == 'geoid10':
            kwargs['primary_key'] = True
        columns.append(Column(fname.lower(), col_type, **kwargs))
    for record in records:
        geo_type = record.shape.__geo_interface__['type']
    geo_type = 'MULTIPOLYGON'
    columns.append(Column('geom', Geometry(geo_type)))
    conn_str='postgresql+psycopg2://{user}:@{host}:{port}/{name}'\
        .format(user=DB_USER, host=DB_HOST, port=DB_PORT, name=DB_NAME)
    metadata = MetaData()
    engine = create_engine(conn_str, 
                           convert_unicode=True, 
                           server_side_cursors=True)
    table = Table('census_blocks', metadata, *columns)
    table.create(engine, checkfirst=True)

    ins = table.insert()
    shp_count = 0
    values = []
    for record in records:
        d = {}
        for k,v in zip(table.columns.keys(), record.record):
            d[k] = v
        geom = asShape(record.shape.__geo_interface__)
        geom = MultiPolygon([geom])
        d['geom'] = 'SRID=4326;%s' % geom.wkt
        values.append(d)
        shp_count += 1
        if shp_count % 1000 == 0:
            # dump 100 shapefile records at a time
            conn = engine.connect()
            trans = conn.begin()
            try:
                conn.execute(ins, values)
                trans.commit()
                print 'Loaded {0} shapes'.format(shp_count)
            except Exception, e:
                print e.message
                trans.rollback()
            conn.close()
            values = []
    # out of the loop -- add the remaining records
    if (len(values) != 0):
        conn = engine.connect()
        trans = conn.begin()
        try:
            conn.execute(ins, values)
            trans.commit()
            print 'Loaded {0} shapes'.format(shp_count + len(values))
        except Exception, e:
            print e.message
            trans.rollback()
        conn.close()

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
                    writer.writerow(row)
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
            except psycopg2.IntegrityError, e:
                print e
                conn.rollback()
    print 'Loaded {0}'.format(fname)
    return None

def indexes(create=True):
    for year in range(2002,2012):
        for jt in range(6):
            with psycopg2.connect(DB_CONN_STR) as conn:
                with conn.cursor() as curs:
                    job_type = 'jt{0}'.format(str(jt).zfill(2))
                    for tname in ['origin_dest', 'res_area', 'work_area']:
                        if tname == 'origin_dest':
                            fields = ['h_geocode', 'w_geocode']
                        else:
                            fields = ['geocode', 'segment']
                        for field in fields:
                            table = '{tname}_{year}_{job_type}'\
                                .format(tname=tname, year=year, job_type=job_type)
                            if create:
                                c = ''' 
                                  CREATE INDEX {table}_{field}_idx ON {table} ({field})
                                '''.format(table=table, field=field)
                            else:
                                c = '''
                                  DROP INDEX {table}_{field}_idx
                                '''.format(table=table, field=field)
                            try:
                                curs.execute(c)
                                conn.commit()
                                print 'created index {table}_{field}_idx'\
                                    .format(table=table, field=field)
                            except Exception, e:
                                print e
                                conn.rollback()
    

if __name__ == "__main__":
    import sys
    arg = sys.argv[1]
    if os.path.exists(arg):
        create_tables()
        os.path.walk(arg, iterfiles, None)
    else:
        indexes()
