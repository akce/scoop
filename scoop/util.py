"""
Utility functions.
Copyright (c) 2018 Akce. See LICENSE file for allowable usage.
"""
import os

from . import sql

def getdestdir(db, podtitle):
    return os.path.join(os.path.expanduser(sql.getconfig(db, 'downloaddir')['value']), podtitle)
