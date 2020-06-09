"""
Playlist writing module.
Copyright (c) 2018-2020 Acke, see LICENSE file for allowable usage.
"""

import os

from . import sql
from . import util

def playitems(db, dls):
    # Omit podcast title if all episodes come from the same podcast.
    if len({x.podtitle for x in dls if x.podtitle is not None}) > 1:
        def makelabel(dl):
            return '{}: {}'.format(d.podtitle, d.eptitle)
    else:
        def makelabel(dl):
            return d.eptitle

    for d in dls:
        label = makelabel(d)
        fullpath = os.path.join(util.getdestdir(db, d.podtitle), d.filename)
        # Only return if the file exists. Handles case where media has been deleted, moved, archived etc..
        if os.path.isfile(fullpath):
            yield label, fullpath

def writem3u(db, filename, dls):
    with open(filename, 'w+') as f:
        print('#EXTM3U', file=f)
        print('', file=f)
        destdir = os.path.dirname(filename)
        for label, fullpath in playitems(db, dls):
            # We don't support media length/duration yet so hardcode -1 for now.
            print('#EXTINF:-1,{}'.format(label), file=f)
            print(os.path.relpath(fullpath, destdir), file=f)
            print('', file=f)

def makeplaylist(db, outfile, podcasttitle=None, episodetitle=None, newerthan=None):
    dls = sql.getdls(db, podcasttitle=podcasttitle, episodetitle=episodetitle, statelist=['d'], newerthan=newerthan)
    if dls:
        writem3u(db, outfile, dls)
        print('Wrote: {}'.format(outfile))
