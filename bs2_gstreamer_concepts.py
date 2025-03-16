#!/usr/bin/env python3
import os
# Show error and log messages
os.environ["GST_DEBUG"] = "2"
import sys
import logging
logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)s] - %(message)s")
logger = logging.getLogger(__name__)

import gi
gi.require_version('GLib', '2.0')
gi.require_version('GObject', '2.0')
gi.require_version('Gst', '1.0')
from gi.repository import Gst


# initialize GStreamer
Gst.init(sys.argv[1:])

# Create the elements
source = Gst.ElementFactory.make("videotestsrc", "source")
vertigotv = Gst.ElementFactory.make("vertigotv", "vertigotv")
videoconvert = Gst.ElementFactory.make("videoconvert", "videoconvert")
sink = Gst.ElementFactory.make("autovideosink", "sink")

# Build the pipeline
pipeline = Gst.Pipeline.new("test-pipeline")
pipeline.add(source)
pipeline.add(vertigotv)
pipeline.add(videoconvert)
pipeline.add(sink)

# Link elements
source.link(vertigotv)
vertigotv.link(videoconvert)
videoconvert.link(sink)

# Modify the source's properties
source.props.pattern = "ball"
# Can alternatively be done using `source.set_property("pattern", 0)`
# or using `Gst.util_set_object_arg(source, "pattern", 0)`

# start playing
pipeline.set_state(Gst.State.PLAYING)

# wait until EOS or error
bus = pipeline.get_bus()
msg = bus.timed_pop_filtered(
    Gst.CLOCK_TIME_NONE,
    Gst.MessageType.ERROR | Gst.MessageType.EOS
)
# Parse message
if msg:
    if msg.type == Gst.MessageType.ERROR:
        err, debug_info = msg.parse_error()
        logger.error(f"Error received from element {msg.src.get_name()}: {err.message}")
        logger.error(f"Debugging information: {debug_info if debug_info else 'none'}")
    elif msg.type == Gst.MessageType.EOS:
        logger.info("End-Of-Stream reached.")
    else:
        # This should not happen as we only asked for ERRORs and EOS
        logger.error("Unexpected message received.")
    
# free resources
pipeline.set_state(Gst.State.NULL)
