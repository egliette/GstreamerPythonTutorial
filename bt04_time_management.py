"""
This Python script is based on the GStreamer tutorial:
https://gstreamer.freedesktop.org/documentation/tutorials/basic/time-management.html?gi-language=python
"""

import os

os.environ["GST_DEBUG"] = "2"
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG, format="[%(name)s] [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)

import gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst


def format_ns(ns):
    s, ns = divmod(ns, 1000000000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)

    return "%u:%02u:%02u.%09u" % (h, m, s, ns)


class Player(object):

    def __init__(self):
        # are we playing?
        self.playing = False
        # should we terminate execution?
        self.terminate = False
        # is seeking enabled for this media?
        self.seek_enabled = False
        # have we performed the seek already?
        self.seek_done = False
        # media duration (ns)
        self.duration = Gst.CLOCK_TIME_NONE

        # initialize GStreamer
        Gst.init(None)

        # create the elements
        self.playbin = Gst.ElementFactory.make("playbin", "playbin")
        if not self.playbin:
            logger.error("Could not create 'playbin' element")
            sys.exit(1)

        # set the uri to play
        self.playbin.set_property("uri", "file:///app/videos/street_5min.mp4")

    def play(self):
        # don't start again if we are already playing
        if self.playing:
            return

        # start playing
        ret = self.playbin.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            logger.error("Unable to set the pipeline to the playing state")
            sys.exit(1)

        try:
            # listen to the bus
            bus = self.playbin.get_bus()
            while True:
                msg = bus.timed_pop_filtered(
                    100 * Gst.MSECOND,
                    (
                        Gst.MessageType.STATE_CHANGED
                        | Gst.MessageType.ERROR
                        | Gst.MessageType.EOS
                        | Gst.MessageType.DURATION_CHANGED
                    ),
                )

                # parse message
                if msg:
                    self.handle_message(msg)
                else:
                    # we got no message. this means the timeout expired
                    if self.playing:
                        current = -1
                        # query the current position of the stream
                        ret, current = self.playbin.query_position(Gst.Format.TIME)
                        if not ret:
                            logger.error("Could not query current position")

                        # if we don't know it yet, query the stream duration
                        if self.duration == Gst.CLOCK_TIME_NONE:
                            (ret, self.duration) = self.playbin.query_duration(
                                Gst.Format.TIME
                            )
                            if not ret:
                                logger.error("Could not query stream duration")

                        # print current position and total duration
                        logger.info(
                            f"Position {format_ns(current)} / {format_ns(self.duration)}"
                        )

                        # if seeking is enabled, we have not done it yet and the time is right,
                        # seek
                        if (
                            self.seek_enabled
                            and not self.seek_done
                            and current > 10 * Gst.SECOND
                        ):
                            logger.info("Reached 10s, performing seek...")
                            self.playbin.seek_simple(
                                Gst.Format.TIME,
                                Gst.SeekFlags.FLUSH | Gst.SeekFlags.KEY_UNIT,
                                30 * Gst.SECOND,
                            )

                            self.seek_done = True
                if self.terminate:
                    break
        finally:
            self.playbin.set_state(Gst.State.NULL)

    def handle_message(self, msg):
        t = msg.type
        if t == Gst.MessageType.ERROR:
            err, dbg = msg.parse_error()
            logger.error(f"{msg.src.get_name()} : {err}")
            if dbg:
                logger.debug(f"Debug info: {dbg}")
            self.terminate = True
        elif t == Gst.MessageType.EOS:
            logger.info("End-Of-Stream reached")
            self.terminate = True
        elif t == Gst.MessageType.DURATION_CHANGED:
            # the duration has changed, invalidate the current one
            self.duration = Gst.CLOCK_TIME_NONE
        elif t == Gst.MessageType.STATE_CHANGED:
            old_state, new_state, pending_state = msg.parse_state_changed()
            if msg.src == self.playbin:
                logger.info(
                    f"Pipeline state changed from '{Gst.Element.state_get_name(old_state)}' to '{Gst.Element.state_get_name(new_state)}'"
                )

                # remember whether we are in the playing state or not
                self.playing = new_state == Gst.State.PLAYING

                if self.playing:
                    # we just moved to the playing state
                    query = Gst.Query.new_seeking(Gst.Format.TIME)
                    if self.playbin.query(query):
                        fmt, self.seek_enabled, start, end = query.parse_seeking()

                        if self.seek_enabled:
                            logger.info(
                                f"Seeking is ENABLED (from {format_ns(start)} to {format_ns(end)})"
                            )
                        else:
                            logger.info("Seeking is DISABLED for this stream")
                    else:
                        logger.error("Seeking query failed")

        else:
            logger.error("Unexpected message received")


if __name__ == "__main__":
    p = Player()
    p.play()
