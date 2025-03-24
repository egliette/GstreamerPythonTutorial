"""
This Python script is based on the GStreamer tutorial:
https://gstreamer.freedesktop.org/documentation/tutorials/basic/playback-speed.html?gi-language=python
"""

import os

# set to 0 to show the USAGE message
os.environ["GST_DEBUG"] = "0"
import logging

logging.basicConfig(
    level=logging.DEBUG, format="[%(name)s] [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)

import gi

gi.require_version("Gst", "1.0")
from gi.repository import GLib, Gst


class VideoPlayer:
    def __init__(self, uri):
        self.pipeline = Gst.parse_launch(f"playbin uri={uri}")
        self.video_sink = None
        self.loop = GLib.MainLoop()
        self.playing = True
        self.rate = 1.0

    def send_seek_event(self):
        success, position = self.pipeline.query_position(Gst.Format.TIME)
        if not success:
            logger.error("Unable to retrieve current position.")
            return

        seek_flags = Gst.SeekFlags.FLUSH | Gst.SeekFlags.ACCURATE
        if self.rate > 0:
            seek_event = Gst.Event.new_seek(
                self.rate,
                Gst.Format.TIME,
                seek_flags,
                Gst.SeekType.SET,
                position,
                Gst.SeekType.END,
                position,
            )
        else:
            seek_event = Gst.Event.new_seek(
                self.rate,
                Gst.Format.TIME,
                seek_flags,
                Gst.SeekType.SET,
                0,
                Gst.SeekType.SET,
                position,
            )

        if self.video_sink is None:
            self.video_sink = self.pipeline.get_property("video-sink")

        self.video_sink.send_event(seek_event)
        logger.info(f"Current rate: {self.rate}")

    def handle_keyboard(self, key):
        if key == "p":
            self.playing = not self.playing
            self.pipeline.set_state(
                Gst.State.PLAYING if self.playing else Gst.State.PAUSED
            )
            logger.info(f"Setting state to {'PLAYING' if self.playing else 'PAUSED'}")
        elif key == "s":
            self.rate /= 2.0
            self.send_seek_event()
        elif key == "S":
            self.rate *= 2.0
            self.send_seek_event()
        elif key == "d":
            self.rate *= -1.0
            self.send_seek_event()
        elif key == "n":
            if self.video_sink is None:
                self.video_sink = self.pipeline.get_property("video-sink")

            step_event = Gst.Event.new_step(
                Gst.Format.BUFFERS, 1, abs(self.rate), True, False
            )
            self.video_sink.send_event(step_event)
            logger.info("Stepping one frame")
        elif key == "q":
            self.loop.quit()

    def run(self):
        logger.info(
            "USAGE: Press a key and hit enter: [P] Play/Pause, [S/s] Speed Up/Down, [D] Reverse, [N] Next Frame, [Q] Quit"
        )
        self.pipeline.set_state(Gst.State.PLAYING)

        while True:
            try:
                key = input().strip()
                self.handle_keyboard(key)
                if key.lower() == "q":
                    break
            except (KeyboardInterrupt, EOFError):
                break

        self.pipeline.set_state(Gst.State.NULL)
        if self.video_sink:
            self.video_sink.set_state(Gst.State.NULL)


if __name__ == "__main__":
    Gst.init(None)
    player = VideoPlayer("file:///app/videos/street_5min.mp4")
    player.run()
