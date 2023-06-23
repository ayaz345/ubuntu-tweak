import os
import glob
import logging

log = logging.getLogger('utils.ppa')

PPA_URL = 'ppa.launchpad.net'

def is_ppa(url):
    return PPA_URL in url

def get_list_name(url):
    arch = 'amd64' if os.uname()[-1] == 'x86_64' else 'i386'
    section = url.split('/')
    name = f'/var/lib/apt/lists/ppa.launchpad.net_{section[3]}_{section[4]}_*{arch}_Packages'
    log.debug(f"lists name: {name}")
    names = glob.glob(name)
    log.debug(f"lists names: {names}")
    return names[0] if len(names) == 1 else ''

def get_basename(url):
    section = url.split('/')
    return f'{section[3]}/{section[4]}'

def get_short_name(url):
    return f'ppa:{get_basename(url)}'

def get_long_name(url):
    basename = get_basename(url)

    return '<b>%s</b>\nppa:%s' % (basename, basename)

def get_homepage(url):
    section = url.split('/')
    return f'https://launchpad.net/~{section[3]}/+archive/{section[4]}'

def get_source_file_name(url):
    section = url.split('/')
    return f'{section[3]}-{section[4]}'

def get_ppa_origin_name(url):
    section = url.split('/')
    # Due to the policy of ppa orgin naming, if an ppa is end with "ppa", so ignore it
    if section[4] == 'ppa':
        return f'LP-PPA-{section[3]}'
    else:
        return f'LP-PPA-{section[3]}-{section[4]}'
