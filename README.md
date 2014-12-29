## Setup notes

On OS X, you need to build Mapnik from source to get it to work with a
virtualenv + homebrew python. Steps:

1. Install Mapnik Dependencies without virtualenv activated (which will ensure
boost-python bindings will be linked correctly to homebrew python)

2. ``configure``, ``make``, and ``sudo make install`` Mapnik with virtualenv
activated.

## Running TileStache

The configs that TileStache needs are in the ``tilestache`` directory. After
``pip install``-ing TileStache, [these
scripts](https://github.com/TileStache/TileStache#installation) should be in
the ``bin`` directory of your virtualenv so you should be able to run them like
so with your virtualenv activated:

```bash
$ tilestache-server.py -c tilestache/tilestache.cfg
```

Or with gunicorn:

```bash 
gunicorn -w 3 -b 127.0.0.1:8080 "TileStache:WSGITileServer('tilestache/tilestache.cfg')"
```
