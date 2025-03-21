#!/usr/bin/env python3
import sys
import logging
logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)s] - %(message)s")
logger = logging.getLogger(__name__)

import gi
gi.require_version('Gst', '1.0')
gi.require_version("GLib", "2.0")
from gi.repository import Gst, GLib

class PipelineHandler:
    def __init__(self, uri):
        # Create a playbin pipeline to play the specified URI
        self.pipeline = Gst.parse_launch(f"playbin uri={uri}")
        self.loop = GLib.MainLoop()
        self.is_live = False
        
        # Setup bus message handling
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)
    
    def on_message(self, bus, message):
        t = message.type
        if t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            logger.error(f"Error received from {message.src.get_name()}: {err.message}")
            logger.error(f"Debug info: {debug if debug else 'none'}")
            self.pipeline.set_state(Gst.State.READY)
            self.loop.quit()
        elif t == Gst.MessageType.EOS:
            logger.info("End-Of-Stream reached.")
            self.pipeline.set_state(Gst.State.READY)
            self.loop.quit()
        elif t == Gst.MessageType.BUFFERING:
            # For non-live streams, adjust the pipeline state based on buffering percent.
            percent = message.parse_buffering()
            logger.info(f"Buffering: {percent}%")
            if percent is None:
                return
            if self.is_live:
                return
       
            if percent < 100:
                self.pipeline.set_state(Gst.State.PAUSED)
            else:
                self.pipeline.set_state(Gst.State.PLAYING)
        elif t == Gst.MessageType.CLOCK_LOST:
            logger.debug("Clock lost, resetting pipeline clock.")
            self.pipeline.set_state(Gst.State.PAUSED)
            self.pipeline.set_state(Gst.State.PLAYING)
        # Other messages are ignored

    def run(self):
        ret = self.pipeline.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            logger.error("Unable to set the pipeline to the playing state.")
            return
        
        # Optionally, if the pipeline returns NO_PREROLL, mark as live stream:
        if ret == Gst.StateChangeReturn.NO_PREROLL:
            self.is_live = True

        try:
            self.loop.run()
        except Exception as e:
            logger.error(f"Main loop error: {e}")
        finally:
            self.pipeline.set_state(Gst.State.NULL)
            logger.info("Pipeline stopped.")

if __name__ == "__main__":
    Gst.init(sys.argv)
    # Change the URI as needed
    uri = "https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm"
    handler = PipelineHandler(uri)
    handler.run()
