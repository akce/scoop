""" Playlist writing module. """

import os

from . import scoop
from . import sql

def playitems(dbfile, dls):
    for d in dls:
        label = '{}: {}'.format(d.podtitle, d.eptitle)
        fullpath = os.path.join(scoop.getdestdir(dbfile, d.podtitle), d.filename)
        # Only return if the file exists. Handles case where media has been deleted, moved, archived etc..
        if os.path.isfile(fullpath):
            yield label, fullpath

def writem3u(dbfile, filename, dls):
    with open(filename, 'w+') as f:
        print('#EXTM3U', file=f)
        print('', file=f)
        destdir = os.path.dirname(filename)
        for label, fullpath in playitems(dbfile, dls):
            # We don't support media length/duration yet so hardcode -1 for now.
            print('#EXTINF:-1,{}'.format(label), file=f)
            print(os.path.relpath(fullpath, destdir), file=f)
            print('', file=f)
            print(label)

def makeplaylist(dbfile, outfile, podcasttitle=None, episodetitle=None, newerthan=None):
    dls = sql.getdls(dbfile, podcasttitle=podcasttitle, episodetitle=episodetitle, statelist=['d'], newerthan=newerthan)
    if dls:
        writem3u(dbfile, outfile, dls)
