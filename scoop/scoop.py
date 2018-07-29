"""
Podcast scoop, main module.
Copyright (c) 2018 Acke, see LICENSE file for allowable usage.
"""

import collections
import datetime
import os
import sys
import urllib.request as ur

from . import playlist
from . import rssxml
from . import sql

def openurl(db, url):
    """ Return a url file pointer object. """
    agent = sql.getconfig(db, 'useragent')['value']
    req = ur.Request(url, headers={'User-Agent': agent})
    return ur.urlopen(req)

def urlfpfilename(urlfp):
    """ Return filename from url file pointer object. """
    # Some podcast will contain items whose URLs *all* have the same filename.
    # These URLs will redirect to things that look like a filename we can use.
    urlobj = ur.urlparse(urlfp.url)
    fullpath = ur.unquote(urlobj.path)
    _, filename = os.path.split(fullpath)
    return filename

def getdestdir(db, podtitle):
    return os.path.join(os.path.expanduser(sql.getconfig(db, 'downloaddir')['value']), podtitle)

def downloadrss(db, rssurl, cache=False):
    urlfp = openurl(db, rssurl)
    try:
        rssxmlbytes = urlfp.read()
    finally:
        urlfp.close()
    # Cache rssxmlbytes to file if config.saverss = True
    if cache:
        poddict = rssxml.podcastdict(rssxml.getxmltree(rssxmlbytes), rssurl)
        destdir = os.path.expanduser(sql.getconfig(db, 'downloaddir')['value'])
        os.makedirs(destdir, exist_ok=True)
        rssfile = os.path.join(destdir, '{}.rss'.format(poddict['title']))
        with open(rssfile, 'w') as f:
            f.write(str(rssxmlbytes, 'utf-8'))
    return rssxml.getxmltree(rssxmlbytes)

def addpodcasturl(db, rssurl, limit=False):
    """ Adds a new podcast from network URL to track.
    Also add all the podcast episodes, as well as download items for 'limit' number of the newest episodes. """
    root = downloadrss(db, rssurl, cache=sql.getconfig(db, 'saverss')['value'])
    podcast = sql.addpodcast(db, rssxml.podcastdict(root, rssurl))
    # Insert podcast episodes.
    episodes = sql.addepisodes(db, podcast, rssxml.episodedicts(root))
    # Create dl orders for episodes.
    downloads = sql.adddownloads(db, episodes, limit)
    # Print addition summary.
    statii = collections.Counter()
    for dl in downloads:
        statii[dl.status] += 1
    print('{}: {} new episodes ({} waiting {} skipped)'.format(podcast.title, len(episodes), statii['w'], statii['s']))

def printpodcasts(db, title=None):
    podcasts = sql.getpodcasts(db, title)
    for p in podcasts:
        print(p.title)

def editpodcast(db, podtitle, title=None, rssurl=None):
    if any([title, rssurl]):
        podcasts = sql.getpodcasts(db, podtitle)
        # Make sure that podtitle matches only one podcast before changing anything.
        np = len(podcasts)
        if np == 0:
            print('No podcasts found matching title "{}"'.format(podtitle))
        elif np == 1:
            sql.editpodcast(db, podtitle, title=title, rssurl=rssurl)
            print('{}:'.format(podtitle))
            if title:
                print('title: {} -> {}'.format(podcasts[0].title, title))
                try:
                    os.rename(getdestdir(db, podcasts[0].title), getdestdir(db, title))
                except FileNotFoundError:
                    pass
            if rssurl:
                print('rssurl: {} -> {}'.format(podcasts[0].rssurl, rssurl))
        else:
            # np > 1
            print('More than one podcast matches title "{}", please narrow your search'.format(podtitle))
    else:
        print('Nothing to do! Supply either a new title or rssurl.')

def syncpodcasts(db, title=None, limit=False):
    podcasts = sql.getpodcasts(db, title)
    for p in podcasts:
        addpodcasturl(db, p.rssurl, limit=limit)

def downloadepisode(db, dl):
    # Download episode from dl.mediaurl > config:downloaddir/dl.podtitle/dl.mediaurl:filename
    # Ensure destdir exists.
    destdir = getdestdir(db, dl.podtitle)
    os.makedirs(destdir, exist_ok=True)
    urlfp = openurl(db, dl.mediaurl)
    filename = urlfpfilename(urlfp)
    fullpath = os.path.join(destdir, filename)
    try:
        with open(fullpath, 'wb') as f:
            for chunkbytes in iter(lambda: urlfp.read(0x4000), b''):
                f.write(chunkbytes)
    finally:
        urlfp.close()
    return filename

def syncdls(db, updateindex=False):
    dls = sql.getdls(db, statelist=['w'])
    for d in dls:
        try:
            filename = downloadepisode(db, d)
        except Exception as e:
            # Mark download failed.
            state = 'e'
            print(str(e), file=sys.stderr)
            filename = None
        else:
            # Download success.
            state = 'd'
        sql.markdl(db, d, state, filename)
        print('{} {:32} {}'.format(state, d.podtitle, d.eptitle))
    if updateindex and dls:
        # Update the index playlist for each podcast that had new episodes downloaded.
        indexfile = sql.getconfig(db, 'indexfile')['value']
        for podtitle in sorted({p.podtitle for p in dls}):
            outfile = os.path.join(getdestdir(db, podtitle), indexfile)
            playlist.makeplaylist(db, outfile, podcasttitle=podtitle)

def getmaxpodtitlelen(lst):
    return len(max(lst, key=lambda x: len(x.podtitle)).podtitle)

def printepisodes(db, podcasttitle=None, episodetitle=None):
    episodes = sql.getepisodes(db, podcasttitle=podcasttitle, episodetitle=episodetitle)
    maxtitle = getmaxpodtitlelen(episodes)
    fmt = '{:<5} {:' + str(maxtitle) + '} {} {}'
    for e in episodes:
        print(fmt.format(e.episodeid, e.podtitle, datetime.date.fromtimestamp(e.pubdate), e.title))

def makedlsprintlines(dls):
    maxtitle = getmaxpodtitlelen(dls)
    fmt = '{} {:' + str(maxtitle) + '} {}'
    return (fmt.format(d.status, d.podtitle, d.eptitle) for d in dls)

def insertdls(db, episodes):
    """ Insert new dl orders for each episode in episodes. """
    if episodes:
        dlorders = sql.adddownloads(db, episodes, limit=False)
        print('\n'.join(makedlsprintlines(dlorders)))

def dlnewepisodes(db):
    """ Adds download orders for new episodes. """
    insertdls(db, sql.getnewepisodes(db))

def dloldepisodes(db, idlist=None, podcasttitle=None, episodetitle=None):
    """ Create dl orders for old/existing episodes. """
    episodes = sql.getepisodes(db, idlist=idlist, podcasttitle=podcasttitle, episodetitle=episodetitle)
    # Remove episodes that already have outstanding 'w' dl orders.
    eids = [e.episodeid for e in episodes]
    waitingdlids = frozenset(d.episodeid for d in sql.getdls(db, episodeids=eids, statelist=['w']))
    insertdls(db, [e for e in episodes if e.episodeid not in waitingdlids])

def printdls(db, podcasttitle=None, episodetitle=None, statelist=None, newerthan=None):
    dls = sql.getdls(db, podcasttitle=podcasttitle, episodetitle=episodetitle, statelist=statelist, newerthan=newerthan)
    print('\n'.join(makedlsprintlines(dls)))

def printallconfig(db):
    for row in sql.getallconfig(db):
        print('{:16} {:16} {}'.format(row['key'], row['value'], row['description']))

def printconfig(db, key):
    row = sql.getconfig(db, key)
    print('{:16} {}'.format(key, row['value']))

def setconfig(db, key, value):
    sql.setconfig(db, key, value)
