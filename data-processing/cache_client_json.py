import requests
from boto.s3.connection import S3Connection
from boto.s3.key import Key
from config import AWS_ACCESS_KEY, AWS_SECRET_KEY
from process import COUNTIES
import json
from operator import itemgetter
from collections import OrderedDict

ENDPOINT = 'http://127.0.0.1:5000/api/years'

if __name__ == "__main__":
    s3_conn = S3Connection(AWS_ACCESS_KEY, AWS_SECRET_KEY)
    bucket = s3_conn.get_bucket('census-lodes')
    for year in range(2002, 2012):
        all_tracts = {}
        params = {
            'geography': 'tract',
            'char_type': 'res_area',
        }
        res_area = requests.get('{0}/{1}/'.format(ENDPOINT, year), params=params)
        home_tracts = set()
        work_tracts = set()
        for tract in res_area.json()['objects']:
            county = tract['origin'][:5]
            if county in COUNTIES:
                all_tracts[tract['origin']] = {'traveling-from': tract['counts']}
                home_tracts.add(tract['origin'])

        params['char_type'] = 'work_area'
        work_area = requests.get('{0}/{1}/'.format(ENDPOINT, year), params=params)
        for tract in work_area.json()['objects']:
            county = tract['origin'][:5]
            if county in COUNTIES:
                try:
                    all_tracts[tract['origin']]['traveling-to'] = tract['counts']
                except KeyError:
                    all_tracts[tract['origin']] = {
                        'traveling-from': {}, 
                        'traveling-to': tract['counts']
                    }
                work_tracts.add(tract['origin'])
        for tract in (home_tracts - work_tracts):
            all_tracts[tract]['traveling-to'] = {}
        for tract, val in all_tracts.items():
            tt = sorted(val['traveling-to'].items(), 
                        key=itemgetter(1), reverse=True)
            tf = sorted(val['traveling-from'].items(), 
                        key=itemgetter(1), reverse=True)
            outp = OrderedDict([('traveling-to', OrderedDict(tt)), 
                                ('traveling-from', OrderedDict(tf))])
            key = Key(bucket)
            key.key = '{0}/{1}.json'.format(year, tract)
            key.set_contents_from_string(json.dumps(outp, sort_keys=False))
            key.make_public()
            key.copy(key.bucket, key.name, preserve_acl=True, metadata={'Content-Type': 'application/json'})
            print 'saved {0}'.format(key.name)
