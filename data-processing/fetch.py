import requests
import os
from process import COUNTIES

ENDPOINT = 'http://lehd.ces.census.gov/data/lodes/LODES7'
SEGMENTS = {
    'od': ['main', 'aux'],
    'wac': ['S000', 'SA01', 'SA02', 'SA03', 'SE01', 'SE02', 'SE03', 'SI01', 'SI02', 'SI03'],
    'rac': ['S000', 'SA01', 'SA02', 'SA03', 'SE01', 'SE02', 'SE03', 'SI01', 'SI02', 'SI03'],
}
JOB_TYPES = {
    'JT00': 'all',
    'JT01': 'primary',
    'JT02': 'private',
    'JT03': 'private primary',
    'JT04': 'federal',
    'JT05': 'federal primary',
}
AREA_SEGMENTS = {
    'S000': 'all', 
    'SA01': 'under 29',
    'SA02': '30 to 54', 
    'SA03': 'over 55',
    'SE01': '$1250/month or less',
    'SE02': '$1251-$3333/month',
    'SE03': 'more than $3333/month',
    'SI01': 'Goods Producing industry sectors',
    'SI02': 'Trade, Transportation, and Utilities industry sectors',
    'SI03': 'All Other Services industry sectors',
}

def iter_parts(year, state):
    groups = ['od', 'rac', 'wac']
    job_types = JOB_TYPES.keys()
    for group in groups:
        save_path = os.path.join(os.environ['HOME'], 'lodes-data', state, group)
        try:
            os.makedirs(save_path)
        except os.error:
            pass
        segments = SEGMENTS[group]
        for segment in segments:
            for job_type in job_types:
                state = state.lower()
                fname = '%s_%s_%s_%s_%s.csv.gz' % (state, group, segment, job_type, year)
                full_path = os.path.join(save_path, fname)
                url = '%s/%s/%s/%s' % (ENDPOINT, state, group, fname)
                yield full_path, url

def fetch(full_path, url):
    if os.path.exists(full_path):
        return 'Already fetched file: %s' % os.path.basename(full_path)
    else:
        try:
            req = requests.get(url)
        except requests.ConnectionError:
            return 'Was unable to load %s' % url
        if req.status_code != 200:
            return 'Got a %s when trying to fetch %s' % (req.status_code, url)
        f = open(full_path, 'wb')
        f.write(req.content)
        f.close()
        return 'Saved %s' % os.path.basename(full_path)

def fetch_blocks():
    pattern = 'http://www2.census.gov/geo/tiger/TIGER2010/TABBLOCK/2010/tl_2010_{0}_tabblock10.zip'
    save_dir = os.path.join(os.environ['HOME'], 'lodes-data', 'census-blocks')
    try:
        os.makedirs(save_dir)
    except os.error:
        pass
    for county in COUNTIES:
        url = pattern.format(county)
        fname = 'tl_2010_{0}_tabblock10.zip'.format(county)
        full_path = os.path.join(save_dir, fname)
        if os.path.exists(full_path):
            yield 'Already saved file: {0}'.format(full_path)
        try:
            req = requests.get(url)
        except requests.ConnectionError:
            yield 'Could not fetch census blocks for {0}'.format(county)
        if req.status_code != 200:
            yield 'Got a {0} when trying to fetch {1}'\
                .format(req.status_code, url)
        with open(full_path, 'wb') as f:
            f.write(req.content)
        yield 'Saved {0}'.format(fname)

if __name__ == "__main__":
    for f in fetch_blocks():
        print f
    states = ['il', 'wi', 'in']
    for state in states:
        for year in range(2011, 2014):
            for full_path, url in iter_parts(year, state):
                print fetch(full_path, url)
