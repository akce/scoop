""" Playlist writing module. """

import datetime
import os
import time

from . import scoop
from . import sql

def playitems(dbfile, dls):
    for d in dls:
        label = '{}: {}'.format(d.podtitle, d.eptitle)
        fullpath = os.path.join(scoop.getdestdir(dbfile, d.podtitle), d.filename)
        yield label, fullpath

def writem3u(dbfile, filename, dls):
    with open(filename, 'w+') as f:
        print('#EXTM3U', file=f)
        print('', file=f)
        for label, fullpath in playitems(dbfile, dls):
            # We don't support media length/duration yet so hardcode -1 for now.
            print('#EXTINF:-1,{}'.format(label), file=f)
            print(fullpath, file=f)
            print('', file=f)
            print(label)

def makeplaylist(dbfile, outfile, podcasttitle=None, episodetitle=None, newerthan=None):
    if newerthan is None:
        ts = None
    else:
        # Create our newerthan timestamp.
        # Using datetime and timedelta in this way will include the whole of days-ago.
        daydiff = datetime.timedelta(days=newerthan)
        daysago = datetime.date.today() - daydiff
        ts = int(time.mktime(daysago.timetuple()))
    dls = sql.getdls(dbfile, podcasttitle=podcasttitle, episodetitle=episodetitle, statelist=['d'], newerthan=ts)
    if dls:
        writem3u(dbfile, outfile, dls)
