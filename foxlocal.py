#!/usr/bin/env python
# -*- coding: utf-8 -*-

from tempfile import mkdtemp
import subprocess
import re
from urllib import urlopen
import sys
import shutil, os, os.path
import errno

LOCALDIR = os.path.expanduser('~/.local')
LOCALFOXDIR = os.path.expanduser('~/.localFox')
#LOCALDIR = os.path.expanduser('~/.testLocal')
#LOCALFOXDIR = os.path.expanduser('~/.testFox')

BASE = 'http://ftp.mozilla.org'

CHANNELS = {
    'nightly': '/pub/mozilla.org/firefox/nightly/latest-mozilla-central/',
    'aurora': '/pub/mozilla.org/firefox/nightly/latest-mozilla-aurora/',
    'beta': '/pub/mozilla.org/firefox/releases/latest-beta/linux-{0}/en-US/',
    'release': '/pub/mozilla.org/firefox/releases/latest/linux-{0}/en-US/'
}

DESKTOP = '''[Desktop Entry]
Version=1.0
Name=Firefox {0}
GenericName=Web Browser
GenericName[ca]=Navegador web
GenericName[cs]=Webový prohlížeč
GenericName[es]=Navegador web
GenericName[fa]=مرورگر اینترنتی
GenericName[fi]=WWW-selain
GenericName[fr]=Navigateur Web
GenericName[hu]=Webböngésző
GenericName[it]=Browser Web
GenericName[ja]=ウェブ・ブラウザ
GenericName[ko]=웹 브라우저
GenericName[nb]=Nettleser
GenericName[nl]=Webbrowser
GenericName[nn]=Nettlesar
GenericName[no]=Nettleser
GenericName[pl]=Przeglądarka WWW
GenericName[pt]=Navegador Web
GenericName[pt_BR]=Navegador Web
GenericName[sk]=Internetový prehliadač
GenericName[sv]=Webbläsare
Comment=Browse the Web
Comment[ca]=Navegueu per el web
Comment[cs]=Prohlížení stránek World Wide Webu
Comment[de]=Im Internet surfen
Comment[es]=Navegue por la web
Comment[fa]=صفحات شبکه جهانی اینترنت را مرور نمایید
Comment[fi]=Selaa Internetin WWW-sivuja
Comment[fr]=Navigue sur Internet
Comment[hu]=A világháló böngészése
Comment[it]=Esplora il web
Comment[ja]=ウェブを閲覧します
Comment[ko]=웹을 돌아 다닙니다
Comment[nb]=Surf på nettet
Comment[nl]=Verken het internet
Comment[nn]=Surf på nettet
Comment[no]=Surf på nettet
Comment[pl]=Przeglądanie stron WWW
Comment[pt]=Navegue na Internet
Comment[pt_BR]=Navegue na Internet
Comment[sk]=Prehliadanie internetu
Comment[sv]=Surfa på webben
Exec={1} %u
Icon=firefox-{2}
Terminal=false
Type=Application
MimeType=text/html;text/xml;application/xhtml+xml;application/vnd.mozilla.xul+xml;text/mml;x-scheme-handler/http;x-scheme-handler/https;
StartupNotify=true
StartupWMClass=Navigator
Categories=Network;WebBrowser;
Keywords=web;browser;internet;
'''

def get_tarball_url(channel):
    arch = subprocess.Popen(
        "arch", shell=True, stdout=subprocess.PIPE).stdout.read().strip()
    patt = None

    if channel in ['nightly', 'aurora']:
        p = CHANNELS[channel]
        index = urlopen(BASE + p).read()
        patt = re.compile('href="(\S+\.linux-%s.tar.bz2)"' % arch, re.M)
    elif channel in ['release', 'beta']:
        p = CHANNELS[channel].format(arch)
        index = urlopen(BASE + p).read()
        patt = re.compile('href="(\S+\.tar.bz2)"', re.M)

    fname = patt.findall(index)[0]
    return BASE + os.path.join(p, fname)


def install_firefox(channel, tempdir):
    url = get_tarball_url(channel)
    sub = subprocess.Popen("curl -o firefox.tar.bz2 %s" % url, shell=True, cwd=tempdir)
    sub.wait()
    sub = subprocess.Popen("tar xfj firefox.tar.bz2", shell=True, cwd=tempdir)
    sub.wait()
    _mkdir(LOCALFOXDIR)
    shutil.rmtree(os.path.join(LOCALFOXDIR, channel), True)
    shutil.move(os.path.join(tempdir, 'firefox'),
        os.path.join(LOCALFOXDIR, channel))
    shutil.rmtree(tempdir)

def link_icons(channel):
    channeldir = os.path.join(LOCALFOXDIR, channel)
    icons = {
        '16x16': 'browser/chrome/icons/default/default16.png',
        '32x32': 'browser/chrome/icons/default/default32.png',
        '48x48': 'browser/chrome/icons/default/default48.png',
        '128x128': 'browser/icons/mozicon128.png'
    }
    for size in icons:
        destdir = os.path.join(LOCALDIR, 'share/icons/hicolor/%s/apps' % size)
        _mkdir(destdir)
        _unlink(os.path.join(destdir, 'firefox-%s.png' % channel))
        os.symlink(
            os.path.join(channeldir, icons[size]),
            os.path.join(destdir, 'firefox-%s.png' % channel))

def link_binary(channel):
    srcbin = os.path.join(LOCALFOXDIR, channel, 'firefox')
    bindir = os.path.join(LOCALDIR, 'bin')
    destbin = os.path.join(bindir, 'firefox-%s' % channel)
    _mkdir(bindir)
    _unlink(destbin)
    os.symlink(srcbin, destbin)

def create_desktop_file(channel):
    desktop_dir = os.path.join(LOCALDIR, 'share/applications')
    _mkdir(desktop_dir)
    desktop_file = os.path.join(LOCALDIR, desktop_dir, 'firefox-%s.desktop' % channel)
    f = open(desktop_file, 'w')
    f.write(DESKTOP.format(
        channel.capitalize(), os.path.join(LOCALFOXDIR, channel, 'firefox'), channel))

def _mkdir(dirname):
    try:
        os.makedirs(dirname)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise e
        pass

def _unlink(fname):
    try:
        os.unlink(fname)
    except OSError, e:
        if e.errno != errno.ENOENT:
            raise e
        pass

if __name__ == '__main__':
    channel = sys.argv[-1]
    if (channel not in CHANNELS.keys()):
        print 'Please provide a release channel'
        sys.exit(1)

    tempdir = mkdtemp()
    try:
        install_firefox(channel, tempdir)
        link_icons(channel)
        link_binary(channel)
        create_desktop_file(channel)
    finally:
        print 'Cleaning up..', tempdir
        #shutil.rmtree(tempdir)
