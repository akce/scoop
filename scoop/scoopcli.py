import argparse
import os

from . import nestedarg
from . import scoop

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

def dlnewepisodes(args):
    scoop.dlnewepisodes(dbfile=args.dbfile)

def lsdl(args):
    scoop.printdls(dbfile=args.dbfile, podcasttitle=args.podcasttitle, episodetitle=args.episodetitle)

def printallconfig(args):
    scoop.printallconfig(dbfile=args.dbfile)

def printconfig(args):
    scoop.printconfig(args.key, dbfile=args.dbfile)

def setconfig(args):
    scoop.setconfig(args.key, args.value, dbfile=args.dbfile)

def syncpodcasts(args):
    scoop.syncpodcasts(dbfile=args.dbfile, title=args.podcasttitle, limit=args.limit)

def syncdls(args):
    scoop.syncdls(dbfile=args.dbfile)

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
        with subcommand('get', aliases=['g', 'dl', 'd'], help='make download orders for new episodes') as c:
            # TODO Create dl orders based on all kinds of criteria.
            #c.add_argument('--podcasttitle', default=None, type=str, help='podcast title search string')
            #c.add_argument('--episodetitle', default=None, type=str, help='episode title search string')
            #c.add_argument('--limit', default=False, type=int, help='how many of the latest articles per podcast to retrieve. Default: get all')
            c.set_defaults(command=dlnewepisodes)
    with command('dl', aliases=['d', 'q'], help='download queue actions') as c:
        subcommand = nestedarg.NestedSubparser(c.add_subparsers())
        with subcommand('ls', aliases=['l'], help='list download orders') as c:
            # TODO -all, --new, --waiting, --skipped, --error, --dled
            c.add_argument('--podcasttitle', default=None, type=str, help='podcast title search string')
            c.add_argument('--episodetitle', default=None, type=str, help='episode title search string')
            c.set_defaults(command=lsdl)
        with subcommand('sync', aliases=['s', 'get', 'g'], help='action waiting download orders') as c:
            c.set_defaults(command=syncdls)
    args = parser.parse_args()
    args.command(args)
