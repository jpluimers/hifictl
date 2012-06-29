#!/usr/bin/env python2

"""
Manage I/O between a collection of A/V devices.

The A/V devices (and some not-so-A/V devices) are each represented by a class
instance derived from the AV_Device API.

The A/V devices are controlled by an AV_Loop instance, which mediates
communication and runtime between the instantiated devices.

Devices may submit commands (strings of the form "$namespace $subcommand") to
the AV_Loop, which then dispatches the command to the command handler registered
for $namepace (or falls back to the empty ('') namespace command handler if
no handler is registered for $namespace).

Additionally, AV_Devices may register I/O handlers with the AV_Loop, which will
then listen for I/O events on the given file descriptors.
"""

import sys
import os
import time
import select
import argparse

from hdmi_switch import HDMI_Switch
from avr_device import AVR_Device
from av_fifo import AV_FIFO
from http_server import AV_HTTPServer
from av_loop import AV_Loop


Devices = (
	("hdmi", HDMI_Switch),
	("avr",  AVR_Device),
	("fifo", AV_FIFO),
	("http", AV_HTTPServer),
)

AVR_Device.DefaultTTY = "/dev/ttyUSB1"
AV_FIFO.DefaultFIFOPath = "/tmp/av_control"


def main(args):
	parser = argparse.ArgumentParser(
		description = "Controller daemon for A/V devices")
	for name, cls in Devices:
		cls.register_args(name, parser)

	mainloop = AV_Loop(vars(parser.parse_args(args)))
	devices = {} # Map device names to AV_Device objects.

	def cmd_catch_all(namespace, cmd):
		"""Handle commands that are not handled elsewhere."""
		print "*** Unknown A/V command: '%s %s'" % (namespace, cmd)
	mainloop.add_cmd_handler('', cmd_catch_all)

	for name, cls in Devices:
		try:
			print "*** Initializing %s..." % (cls.Description),
			dev = cls(mainloop, name)
			devices[name] = dev
			print "done"
		except Exception as e:
			print e

	if not devices:
		print "No A/V devices found. Aborting..."
		return 1

	print "Starting A/V controller main loop."
	return mainloop.run()


if __name__ == '__main__':
	sys.exit(main(sys.argv[1:]))
