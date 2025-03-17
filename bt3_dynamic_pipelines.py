#!/usr/bin/env python3
import os
# Show error and log messages
os.environ["GST_DEBUG"] = "2"
import time
import logging
logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)s] - %(message)s")
logger = logging.getLogger(__name__)

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst


class Player():

    def __init__(self):
        # initialize GStreamer
        Gst.init(None)

        # create the elements
        self.source = Gst.ElementFactory.make("uridecodebin", "source")
        self.video_convert = Gst.ElementFactory.make("videoconvert", "video_convert")
        self.video_sink = Gst.ElementFactory.make("autovideosink", "video_sink")
        self.audio_convert = Gst.ElementFactory.make("audioconvert", "audio_convert")
        self.audio_sink = Gst.ElementFactory.make("autoaudiosink", "audio_sink")

        # create empty pipeline
        self.pipeline = Gst.Pipeline.new("test-pipeline")

        # build the pipeline. we are NOT linking the source at this point.
        # will do it later
        self.pipeline.add(self.source)
        self.pipeline.add(self.video_convert)
        self.pipeline.add(self.video_sink)
        self.pipeline.add(self.audio_convert)
        self.pipeline.add(self.audio_sink)

        self.video_convert.link(self.video_sink)
        self.audio_convert.link(self.audio_sink)

        # set the URI to play
        self.source.set_property("uri", "file:///app/videos/chime_2min.mp4")

        # connect to the pad-added signal
        self.source.connect("pad-added", self.on_pad_added)

    # handler for the pad-added signal
    def on_pad_added(self, src, new_pad):
        logger.info(f"Received new pad '{new_pad.get_name()}' from '{src.get_name()}'")

        # check the new pad's type
        new_pad_caps = new_pad.get_current_caps()
        new_pad_struct = new_pad_caps.get_structure(0)
        new_pad_type = new_pad_struct.get_name()

        logger.info(f"Found {new_pad_type = }, trying to link...")
        if new_pad_type.startswith("audio/x-raw"):
            sink_pad = self.audio_convert.get_static_pad("sink")
        else:
            sink_pad = self.video_convert.get_static_pad("sink")

        # attempt the link
        ret = new_pad.link(sink_pad)
        if ret != Gst.PadLinkReturn.OK:
            logger.info(f"Type is '{new_pad_type}' but link failed")
        else:
            logger.info(f"Link succeeded (type '{new_pad_type}')")

        return

    def play(self):
       # start playing
        self.pipeline.set_state(Gst.State.PLAYING)

        # listen to the bus
        bus = self.pipeline.get_bus()

        while True:
            msg = bus.timed_pop_filtered(
                Gst.CLOCK_TIME_NONE,
                Gst.MessageType.STATE_CHANGED | Gst.MessageType.EOS | Gst.MessageType.ERROR
            )

            if not msg:
                # sleep to prevent CPU overhead
                time.sleep(0.01)
                continue

            t = msg.type
            if t == Gst.MessageType.ERROR:
                err, dbg = msg.parse_error()
                logger.error(f"ERROR: {msg.src.get_name()}, {err.message}")
                if dbg:
                    logger.debug(f"Debugging info:  {dbg}")
                break
            elif t == Gst.MessageType.EOS:
                logger.info("End-Of-Stream reached")
                break
            elif t == Gst.MessageType.STATE_CHANGED:
                # we are only interested in STATE_CHANGED messages from the pipeline
                if msg.src == self.pipeline:
                    old_state, new_state, pending_state = msg.parse_state_changed()
                    logger.info(
                        f"Pipeline state changed from {Gst.Element.state_get_name(old_state)} "
                        f"to {Gst.Element.state_get_name(new_state)}"
                    )
            else:
                logger.info("ERROR: Unexpected message received")
                break

        self.pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    p = Player()
    p.play()