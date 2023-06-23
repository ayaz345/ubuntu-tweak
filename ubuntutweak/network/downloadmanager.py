#!/usr/bin/python
# coding: utf-8

import os
import logging
import urllib
import thread
import socket

from gi.repository import Gtk
from gi.repository import GObject

from ubuntutweak.gui.dialogs import BusyDialog
from ubuntutweak.common import consts

log = logging.getLogger('downloadmanager')
socket.setdefaulttimeout(60)

class Downloader(GObject.GObject):
    __gsignals__ = {
      'downloading': (GObject.SignalFlags.RUN_FIRST, None, (GObject.TYPE_FLOAT,)),
      'downloaded': (GObject.SignalFlags.RUN_FIRST, None, ()),
      'error': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }

    tempdir = os.path.join(consts.CONFIG_ROOT, 'temp')

    def __init__(self, url=None):
        if url:
            self.url = url
        super(Downloader, self).__init__()

    def create_tempdir(self):
        if not os.path.exists(self.tempdir):
            os.makedirs(self.tempdir)
        elif not os.path.isdir(self.tempdir): 
            os.remove(self.tempdir)
            os.makedirs(self.tempdir)

    def clean_tempdir(self):
        for root, dirs, files in os.walk(self.tempdir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))

    def start(self, url=None):
        if not os.path.exists(self.tempdir) or os.path.isfile(self.tempdir):
            self.create_tempdir()
        self.clean_tempdir()

        if url:
            self.url = url

        self.save_to = os.path.join(self.tempdir, os.path.basename(self.url))
        try:
            urllib.urlretrieve(self.url, self.save_to, self.update_progress)
        except socket.timeout:
            self.emit('error')

    def update_progress(self, blocks, block_size, total_size):
        percentage = float(blocks*block_size)/total_size
        if percentage >= 0:
            if percentage < 1:
                self.emit('downloading', percentage)
            else:
                self.emit('downloaded')
        else:
            self.emit('error')

    def get_downloaded_file(self):
        return self.save_to

class DownloadDialog(BusyDialog):
    time_count = 1
    downloaded = False
    error = False

    def __init__(self, url=None, title=None, parent=None):
        BusyDialog.__init__(self, parent=parent)

        self.set_size_request(320, -1)
        self.set_title('')
        self.set_resizable(False)
        self.set_border_width(8)

        vbox = self.get_child()
        vbox.set_spacing(6)

        if title:
            label = Gtk.Label()
            label.set_alignment(0, 0.5)
            label.set_markup(f'<big><b>{title}</b></big>')
            vbox.pack_start(label, False, False, 0)

        self.wait_text = _('Connecting to server')
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_text(self.wait_text)
        vbox.pack_start(self.progress_bar, True, False, 0)

        if url:
            self.url = url
            self.downloader = Downloader(url)
        else:
            self.downloader = Downloader()

        self.downloader.connect('downloading', self.on_downloading)
        self.downloader.connect('downloaded', self.on_downloaded)
        self.downloader.connect('error', self.on_error_happen)

        self.add_button(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL)
        self.show_all()

        GObject.timeout_add(1000, self.on_network_connect)

    def on_network_connect(self):
        if self.time_count != -1:
            self.progress_bar.set_text(self.wait_text+'.' * self.time_count)
            if self.time_count < 3:
                self.time_count += 1
            else:
                self.time_count = 1

            return True

    def run(self):
        thread.start_new_thread(self._download_thread, ())
        return super(DownloadDialog, self).run()

    def destroy(self):
        super(DownloadDialog, self).destroy()

    def set_url(self, url):
        self.url = url

    def on_downloading(self, widget, percentage):
        log.debug(f"Downloading: {percentage}")
        if self.time_count != -1:
            self.time_count = -1

        if percentage < 1:
            self.progress_bar.set_text(_('Downloading...%d') % int(percentage * 100)+ '%')
            self.progress_bar.set_fraction(percentage)

    def on_downloaded(self, widget):
        log.debug("Downloaded")
        self.progress_bar.set_text(_('Downloaded!'))
        self.progress_bar.set_fraction(1)
        self.response(Gtk.ResponseType.DELETE_EVENT)
        self.downloaded = True

    def on_error_happen(self, widget):
        log.debug("Error happened")
        self.progress_bar.set_text(_('Error happened!'))
        self.progress_bar.set_fraction(1)
        self.response(Gtk.ResponseType.DELETE_EVENT)
        self.downloaded = False
        self.error = True

    def _download_thread(self):
        self.downloader.start(self.url)

    def get_downloaded_file(self):
        return self.downloader.get_downloaded_file()
