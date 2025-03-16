#!/usr/bin/env python3
import os
# Show error and log messages
os.environ["GST_DEBUG"] = "2"
import sys

from colorama import Fore
import gi
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GObject, GLib


# initialize GStreamer
Gst.init(sys.argv[1:])

# build the pipeline
pipeline = Gst.parse_launch(
    "playbin uri=file:///app/videos/street.mp4"
    # "playbin uri=file:///mnt/d/Code/Python/GstreamerPythonTutorial/videos/street.mp4"
)

# start playing
pipeline.set_state(Gst.State.PLAYING)

# wait until EOS or error
bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(
    Gst.CLOCK_TIME_NONE,
    Gst.MessageType.ERROR | Gst.MessageType.EOS
)
if msg.type == Gst.MessageType.ERROR:
    err, debug_info = msg.parse_error()
    print(Fore.RED + f"Error received from element {msg.src.get_name()}: {err}")
    print(Fore.BLUE + f"Debugging information: {debug_info}" + Fore.RESET)
elif msg.type == Gst.MessageType.EOS:
    print(f"End-Of-Stream reached.")
    
# free resources
pipeline.set_state(Gst.State.NULL)
