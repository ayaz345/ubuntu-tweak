__all__ = (
    'ModuleLoader',
    'TweakModule',
)
import re
import os
import gtk
import sys
import pango
import inspect
import gobject
import logging
import webbrowser

from new import classobj

from ubuntutweak import system
from ubuntutweak.utils import icon
from ubuntutweak.common.consts import DATA_DIR
from ubuntutweak.common.debug import run_traceback

log = logging.getLogger('ModuleLoader')

def module_cmp(m1, m2):
    return cmp(m1.get_title(), m2.get_title())

class ModuleKeyError(Exception):
    pass

class ModuleLoader:
    module_table = {'broken': []}
    id_table = {}

    def __init__(self, path):
        if os.path.isdir(path):
            for f in os.listdir(path):
                if f.endswith('.py') and f != '__init__.py':
                    module = os.path.splitext(f)[0]
                    log.debug("Try to load module: %s" % module)
                    try:
                        package = __import__('.'.join([__name__, module]), fromlist=['modules'])
                    except Exception, e:
                        Broken = create_broken_module_class(module)
                        self.module_table['broken'].append(Broken)
                        self.id_table['Broken%s' % module.title()] = Broken
                        log.error("Module import error: %s", str(e))
                        continue
                    else:
                        self.do_package_import(package)
        else:
            module = os.path.splitext(os.path.basename(path))[0]
            folder = os.path.dirname(path)
            package = __import__('.'.join([folder, module]))
            self.do_module_import(package, module)

        for k in self.module_table.keys():
            self.module_table[k].sort(module_cmp)

    def do_module_import(self, package, module):
        for k, v in inspect.getmembers(getattr(package, module)):
            self._insert_moduel(k, v)

    def do_package_import(self, package):
        for k, v in inspect.getmembers(package):
            self._insert_moduel(k, v)

    def _insert_moduel(self, k, v):
        if k not in ('TweakModule', 'proxy') and hasattr(v, '__utmodule__'):
            if self.is_supported_desktop(v.__desktop__) and v.__utactive__:
                key = v.__category__
                if self.module_table.has_key(key):
                    self.module_table[key].append(v)
                else:
                    self.module_table[key] = [v]

                self.id_table[v.__name__] = v

    def get_category(self, category):
        return self.module_table.get(category, [])

    def get_module(self, id):
        if not self.id_table.has_key(id):
            raise ModuleKeyError(f'No module with id "{id}"')
        else:
            return self.id_table[id]

    def get_all_module(self):
        return self.id_table.values()

    def is_supported_desktop(self, desktop_name):
        return system.DESKTOP in desktop_name if desktop_name else True

class TweakModule(gtk.VBox):
    __title__ = ''
    __version__ = ''
    __icon__ = ''
    __author__ = ''
    __desc__ = ''
    __url__ = ''
    __urltitle__ = _('More')
    #Identify whether it is a ubuntu tweak module
    __utmodule__ = ''
    __utactive__ = True
    __desktop__ = ''

    #update use internal, and call use between modules
    __gsignals__ = {
            'update': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING,)),
            'call': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_PYOBJECT)),
    }

    def __init__(self, path=None, domain='ubuntu-tweak'):
        gtk.VBox.__init__(self)
        self.set_border_width(6)

        if self.__title__ and self.__desc__:
            self.draw_title()

        self.scrolled_win = gtk.ScrolledWindow()
        self.scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.pack_start(self.scrolled_win)

        self.inner_vbox = gtk.VBox(False, 6)
        self.inner_vbox.set_border_width(6)
        self.scrolled_win.add_with_viewport(self.inner_vbox)
        viewport = self.scrolled_win.get_child()

        if path:
            path = os.path.join(DATA_DIR, 'ui', path)

            self.builder = gtk.Builder()
            self.builder.set_translation_domain(domain)
            self.builder.add_from_file(path)
            self.builder.connect_signals(self)
            for o in self.builder.get_objects():
                if issubclass(type(o), gtk.Buildable):
                    name = gtk.Buildable.get_name(o)
                    setattr(self, name, o)
                else:
                    print >>sys.stderr, "WARNING: can not get name for '%s'" % o

    def add_start(self, child, expand=True, fill=True, padding=0):
        self.inner_vbox.pack_start(child, expand, fill, padding)

    def add_end(self, child, expand=True, fill=True, padding=0):
        self.inner_vbox.pack_end(child, expand, fill, padding)

    def draw_title(self):
        style = gtk.MenuItem().rc_get_style()

        vbox = gtk.VBox()
        vbox.set_style(style)
        self.pack_start(vbox, False, False, 0)

        align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        align.set_padding(5, 5, 5, 5)
        vbox.pack_start(align)

        hbox = gtk.HBox(False, 6)
        align.add(hbox)

        inner_vbox = gtk.VBox(False, 6)
        hbox.pack_start(inner_vbox)

        align = gtk.Alignment(0.5, 0.5, 1.0, 1.0)
        inner_vbox.pack_start(align, False, False, 0)

        inner_hbox = gtk.HBox(False, 0)
        align.add(inner_hbox)

        name = gtk.Label()
        name.set_markup(f'<b><big>{self.__title__}</big></b>')
        name.set_alignment(0, 0.5)
        inner_hbox.pack_start(name, False, False, 0)

        if self.__url__:
            more = gtk.Label()
            more.set_markup(f'<a href="{self.__url__}">{self.__urltitle__}</a>')
            inner_hbox.pack_end(more, False, False, 0)

        desc = gtk.Label(self.__desc__)
        desc.set_ellipsize(pango.ELLIPSIZE_END)
        desc.set_alignment(0, 0.5)
        inner_vbox.pack_start(desc, False, False, 0)

        if self.__icon__:
            if type(self.__icon__) == list:
                pixbuf = icon.get_from_list(self.__icon__, size=48)
                image = gtk.image_new_from_pixbuf(pixbuf)

            elif self.__icon__.endswith('.png'):
                icon_path = os.path.join(DATA_DIR, 'pixmaps', self.__icon__)
                image = gtk.image_new_from_file(icon_path)
            else:
                pixbuf = icon.get_from_name(self.__icon__, size=48)
                image = gtk.image_new_from_pixbuf(pixbuf)
            image.set_alignment(0, 0)
            image.set_padding(5, 5)
            hbox.pack_end(image, False, False, 0)

    def remove_all_children(self):
        for child in self.inner_vbox.get_children():
            self.inner_vbox.remove(child) 

    def reparent(self, widget):
        '''
        If module use glade, it must call this method to reparent the main frame
        '''
        widget.reparent(self.inner_vbox)

    @classmethod
    def get_name(cls):
        '''Return the module name
        class Computer(TweakModule):
            pass
        the "Computer" is the module name
        '''
        return cls.__name__

    @classmethod
    def get_title(cls):
        '''Return the module title, it is for human read with i18n support
        '''
        return cls.__title__

    def get_error(self):
        return self.error_view.get_buffer().get_property('text')

    @classmethod
    def get_pixbuf(cls):
        '''Return gtk Pixbuf'''
        if cls.__icon__:
            if type(cls.__icon__) == list:
                return icon.get_from_list(cls.__icon__)

            elif cls.__icon__.endswith('.png'):
                icon_path = os.path.join(DATA_DIR, 'pixmaps', cls.__icon__)
                return gtk.gd.pixbuf_new_from_file(icon_path)
            else:
                return icon.get_from_name(cls.__icon__)

def show_error_page():
    align = gtk.Alignment(0.5, 0.3)

    hbox = gtk.HBox(False, 12)
    align.add(hbox)

    image = gtk.image_new_from_pixbuf(icon.get_from_name('emblem-ohno', size=64))
    hbox.pack_start(image, False, False, 0)

    label = gtk.Label()
    label.set_markup("<span size=\"x-large\">%s</span>" % 
                     _("This module encountered an error while loading."))
    label.set_justify(gtk.JUSTIFY_FILL)
    hbox.pack_start(label)
        
    return align

def create_broken_module_class(name):
    return classobj(
        f'Broken{name.title()}',
        (BrokenModule,),
        {
            '__name__': name,
            '__title__': name,
            'error_view': run_traceback('error', textview_only=True),
        },
    )

class BrokenModule(TweakModule):
    __icon__ = 'gtk-dialog-error'

    def __init__(self):
        super(BrokenModule, self).__init__('brokenmodule.ui')

        if '/etc/apt/apt.conf.d' in self.get_error():
            p = re.compile('(/etc/apt/apt.conf.d/[\w-]+)')
            broken_file = p.findall(self.get_error())[0]
            self.message_label.set_text(_("Ubuntu Tweak has detected that your apt configuration is broken.\nTry to fix by following steps:\n\n\t1. Open your terminal\n\t2. Run the commands to fix:\n\n\t\tsudo chmod 644 %(broken_file)s\n\t\tsudo chown root:root %(broken_file)s\n\nOr you can submit the Error Message to the developer for help:" % {'broken_file': broken_file}))
        elif '/etc/apt/sources.list.d/' in self.get_error():
            p = re.compile('(/etc/apt/sources.list.d/[\w-]+)')
            broken_file = p.findall(self.get_error())[0]

            self.message_label.set_text(_("Ubuntu Tweak has detected that your apt list file is broken.\nTry to fix by following steps:\n\n\t1. Open your terminal\n\t2. Run the command to open apt list file:\n\n\t\tsudo gedit %s\n\n\t3. Edit the list to make it correctly\n\nOr you can submit the Error Message to the developer for help:" % broken_file))

        self.error_view.reparent(self.scrolled_window)
        self.reparent(self.alignment1)

    def on_report_button_clicked(self, widget):
        webbrowser.open('https://bugs.launchpad.net/ubuntu-tweak/+filebug')
