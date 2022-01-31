from __future__ import absolute_import, print_function, unicode_literals

from optparse import OptionParser
import sys
import dbus
import dbus.service
import dbus.mainloop.glib
try:
    from gi.repository import GObject
except ImportError:
    import gobject as GObject

BUS_NAME = 'org.bluez'
AGENT_INTERFACE = 'org.bluez.Agent1'
AGENT_PATH = "/test/agent"

bus = None
device_obj = None
dev_path = None


def ask(prompt):
    try:
        return raw_input(prompt)
    except:
        return input(prompt)


def set_trusted(path):
    props = dbus.Interface(bus.get_object("org.bluez", path),
                           "org.freedesktop.DBus.Properties")
    props.Set("org.bluez.Device1", "Trusted", True)


def dev_connect(path):
    dev = dbus.Interface(bus.get_object("org.bluez", path),
                         "org.bluez.Device1")
    dev.Connect()


class Rejected(dbus.DBusException):
    _dbus_error_name = "org.bluez.Error.Rejected"


class Agent(dbus.service.Object):
    exit_on_release = True

    def set_exit_on_release(self, exit_on_release):
        self.exit_on_release = exit_on_release

    @dbus.service.method(AGENT_INTERFACE,
                         in_signature="", out_signature="")
    def Release(self):
        print("Release")
        if self.exit_on_release:
            mainloop.quit()

    @dbus.service.method(AGENT_INTERFACE,
                         in_signature="os", out_signature="")
    def AuthorizeService(self, device, uuid):
        print("Authorizing Service (%s, %s)" % (device, uuid))
        return

    @dbus.service.method(AGENT_INTERFACE,
                         in_signature="o", out_signature="")
    def RequestAuthorization(self, device):
        print("Authorizing (%s)" % (device))
        return

    @dbus.service.method(AGENT_INTERFACE,
                         in_signature="", out_signature="")
    def Cancel(self):
        print("Cancel")

if __name__ == '__main__':
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)

    bus = dbus.SystemBus()

    capability = "NoInputNoOutput"

    path = "/test/agent"
    agent = Agent(bus, path)

    mainloop = GObject.MainLoop()

    obj = bus.get_object(BUS_NAME, "/org/bluez")
    manager = dbus.Interface(obj, "org.bluez.AgentManager1")
    manager.RegisterAgent(path, capability)

    print("Agent registered")

    manager.RequestDefaultAgent(path)

    mainloop.run()
