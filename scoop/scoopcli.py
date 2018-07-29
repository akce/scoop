"""
Scoop command line processing module.
Copyright (c) 2018 Acke, see LICENSE file for allowable usage.
"""
import argparse
import datetime
import os
import time

from . import nestedarg
from . import playlist
from . import scoop

def numberrangestolist(numberranges):
    numlist = []
    for x in numberranges.split(','):
        try:
            a, b = x.split('-')
        except ValueError:
            numlist.append(int(x))
        else:
            numlist.extend(list(range(int(a), int(b) + 1)))
    return list(sorted(numlist))

def daystotimestamp(days):
    if days is None:
        ts = None
    else:
        # Create our newerthan timestamp.
        # Using datetime and timedelta in this way will include the whole of days-ago.
        daydiff = datetime.timedelta(days=days)
        daysago = datetime.date.today() - daydiff
        ts = int(time.mktime(daysago.timetuple()))
    return ts

def init(args):
    scoop.init(dbfile=args.dbfile)

def addpodcast(args):
    scoop.addpodcasturl(rssurl=args.rssurl, dbfile=args.dbfile, limit=args.limit)

def lspodcasts(args):
    scoop.printpodcasts(dbfile=args.dbfile, title=args.title)

def editpodcast(args):
    scoop.editpodcast(dbfile=args.dbfile, podtitle=args.podtitle, title=args.title, rssurl=args.rssurl)

def lsepisodes(args):
    scoop.printepisodes(dbfile=args.dbfile, podcasttitle=args.podcasttitle, episodetitle=args.episodetitle)

def dloldepisodes(args):
    # Explode idranges to a list of numbers.
    if args.ids is None:
        idlist = []
    else:
        idlist = numberrangestolist(args.ids)
    scoop.dloldepisodes(dbfile=args.dbfile, idlist=idlist, podcasttitle=args.podcasttitle, episodetitle=args.episodetitle)

def dlnewepisodes(args):
    scoop.dlnewepisodes(dbfile=args.dbfile)

def lsdl(args):
    # Convert args to status list.
    if any([args.downloaded, args.errored, args.skipped, args.waiting]):
        # Find the ones selected and put in our list.
        statelist = list(filter(None, ['d' if args.downloaded else None,
                                       'e' if args.errored else None,
                                       's' if args.skipped else None,
                                       'w' if args.waiting else None]))
    else:
        # Show all by default.
        statelist = None
    ts = daystotimestamp(args.newerthan)
    scoop.printdls(dbfile=args.dbfile, podcasttitle=args.podcasttitle, episodetitle=args.episodetitle, statelist=statelist, newerthan=ts)

def printallconfig(args):
    scoop.printallconfig(dbfile=args.dbfile)

def printconfig(args):
    scoop.printconfig(args.key, dbfile=args.dbfile)

def setconfig(args):
    scoop.setconfig(args.key, args.value, dbfile=args.dbfile)

def syncpodcasts(args):
    scoop.syncpodcasts(dbfile=args.dbfile, title=args.podcasttitle, limit=args.limit)

def syncdls(args):
    scoop.syncdls(dbfile=args.dbfile, updateindex=args.updateindex)

def makeplaylist(args):
    ts = daystotimestamp(args.newerthan)
    playlist.makeplaylist(dbfile=args.dbfile, outfile=args.outfile, podcasttitle=args.podcast, episodetitle=args.episode, newerthan=ts)

def main():
    dbfile = os.path.expanduser('~/.scoop.db')
    parser = argparse.ArgumentParser()
    parser.add_argument('--dbfile', default=dbfile, help='scoop db file. Default: %(default)s')
    command = nestedarg.NestedSubparser(parser.add_subparsers())
    with command('config', aliases=['c'], help='scoop configuration') as c:
        subcommand = nestedarg.NestedSubparser(c.add_subparsers())
        with subcommand('get', aliases=['g'], help='get config value') as s:
            s.add_argument('key', help='config item name')
            s.set_defaults(command=printconfig)
        with subcommand('set', aliases=['s'], help='set config value') as s:
            s.add_argument('key', help='config item name')
            s.add_argument('value', help='new value')
            s.set_defaults(command=setconfig)
        c.set_defaults(command=printallconfig)
    with command('init', aliases=['i'], help='initialise scoop db') as c:
        c.set_defaults(command=init)
    with command('podcast', aliases=['p'], help='podcast actions') as c:
        subcommand = nestedarg.NestedSubparser(c.add_subparsers())
        with subcommand('add', aliases=['new', 'a', 'n'], help='add a new podcast') as c:
            c.add_argument('rssurl', help='url for the rss feed')
            c.add_argument('--limit', default=False, type=int, help='number of newest episodes to get. Default: get all')
            c.set_defaults(command=addpodcast)
        with subcommand('ls', aliases=['l'], help='list podcasts') as c:
            c.add_argument('title', nargs='?', default=None, type=str, help='title search string')
            c.set_defaults(command=lspodcasts)
        with subcommand('edit', aliases=['e'], help='edit fields of a podcast') as c:
            c.add_argument('podtitle', help='podcast title or search string')
            c.add_argument('--title', type=str, help='set podcast title name')
            c.add_argument('--rssurl', type=str, help='set podcast rssurl')
            c.set_defaults(command=editpodcast)
        with subcommand('sync', aliases=['get', 'g', 's'], help='find new episodes for podcasts') as c:
            c.add_argument('--podcasttitle', default=None, type=str, help='podcast title search string')
            c.add_argument('--limit', default=False, type=int, help='number of newest episodes to get. Default: get all')
            c.set_defaults(command=syncpodcasts)
    with command('episode', aliases=['e'], help='episode actions') as c:
        subcommand = nestedarg.NestedSubparser(c.add_subparsers())
        with subcommand('ls', aliases=['l'], help='list episodes') as c:
            # TODO --new, --waiting, --skipped, --error, --dled
            c.add_argument('--podcasttitle', default=None, type=str, help='podcast title search string')
            c.add_argument('episodetitle', nargs='?', default=None, type=str, help='episode title search string')
            c.set_defaults(command=lsepisodes)
        with subcommand('get', aliases=['g', 'dl', 'd'], help='make download orders for old episodes') as c:
            # Create dl orders based on all kinds of criteria.
            c.add_argument('--podcasttitle', default=None, type=str, help='podcast title search string')
            c.add_argument('--episodetitle', default=None, type=str, help='episode title search string')
            c.add_argument('--ids', default=None, type=str, help='episode id number list. eg, 1,4-7,9,10')
            c.set_defaults(command=dloldepisodes)
    with command('dl', aliases=['d', 'q'], help='download queue actions') as c:
        subcommand = nestedarg.NestedSubparser(c.add_subparsers())
        with subcommand('ls', aliases=['l'], help='list download orders') as c:
            c.add_argument('--podcasttitle', default=None, type=str, help='podcast title search string')
            c.add_argument('--episodetitle', default=None, type=str, help='episode title search string')
            c.add_argument('--newerthan', default=None, type=int, metavar='DAYS', help='only episodes downloaded within DAYS')
            c.add_argument('--downloaded', default=False, action='store_true', help='show downloaded orders')
            c.add_argument('--errored', default=False, action='store_true', help='show errored orders')
            c.add_argument('--skipped', default=False, action='store_true', help='show skipped orders')
            c.add_argument('--waiting', default=False, action='store_true', help='show waiting orders')
            c.set_defaults(command=lsdl)
        with subcommand('sync', aliases=['s', 'get', 'g'], help='action waiting download orders') as c:
            c.add_argument('--updateindex', default=False, action='store_true', help='update playlist indexes')
            c.set_defaults(command=syncdls)
    with command('listgen', aliases=['l'], help='generate playlist from download items') as c:
        c.add_argument('outfile', default=None, type=str, metavar='FILE', help='write playlist to FILE')
        c.add_argument('--podcast', default=None, type=str, metavar='TITLE', help='podcast title filter string')
        c.add_argument('--episode', default=None, type=str, metavar='TITLE', help='episode title filter string')
        c.add_argument('--newerthan', default=None, type=int, metavar='DAYS', help='only episodes downloaded within DAYS')
        c.set_defaults(command=makeplaylist)
    args = parser.parse_args()
    args.command(args)
