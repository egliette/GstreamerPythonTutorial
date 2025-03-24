"""
This Python script is based on the GStreamer tutorial:
https://gstreamer.freedesktop.org/documentation/tutorials/basic/short-cutting-the-pipeline.html?gi-language=python
"""

import os
from array import array

os.environ["GST_DEBUG"] = "2"
import logging
import sys

logging.basicConfig(
    level=logging.DEBUG, format="[%(name)s] [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)

import gi

gi.require_version("Gst", "1.0")
gi.require_version("GstAudio", "1.0")
from gi.repository import GLib, Gst, GstAudio

# Constants
CHUNK_SIZE = 1024  # bytes per buffer
SAMPLE_RATE = 44100  # samples per second


class Generator:
    def __init__(self):
        Gst.init(sys.argv)

        # Waveform generation variables
        self.num_samples = 0
        self.a = 0.0
        self.b = 1.0
        self.c = 0.0
        self.d = 1.0
        self.sourceid = None  # will hold the GLib source ID for the idle callback

        # Create elements
        self.app_source = Gst.ElementFactory.make("appsrc", "audio_source")
        self.tee = Gst.ElementFactory.make("tee", "tee")
        self.audio_queue = Gst.ElementFactory.make("queue", "audio_queue")
        self.audio_convert1 = Gst.ElementFactory.make("audioconvert", "audio_convert1")
        self.audio_resample = Gst.ElementFactory.make("audioresample", "audio_resample")
        self.audio_sink = Gst.ElementFactory.make("autoaudiosink", "audio_sink")
        self.video_queue = Gst.ElementFactory.make("queue", "video_queue")
        self.audio_convert2 = Gst.ElementFactory.make("audioconvert", "audio_convert2")
        self.visual = Gst.ElementFactory.make("wavescope", "visual")
        self.video_convert = Gst.ElementFactory.make("videoconvert", "video_convert")
        self.video_sink = Gst.ElementFactory.make("autovideosink", "video_sink")
        self.app_queue = Gst.ElementFactory.make("queue", "app_queue")
        self.app_sink = Gst.ElementFactory.make("appsink", "app_sink")

        self.pipeline = Gst.Pipeline.new("test-pipeline")

        # Configure wavescope
        self.visual.set_property("shader", 0)
        self.visual.set_property("style", 0)

        # Configure appsrc with audio caps (mono, S16, SAMPLE_RATE)
        info = GstAudio.AudioInfo()
        info.set_format(GstAudio.AudioFormat.S16, SAMPLE_RATE, 1, None)
        audio_caps = info.to_caps()
        self.app_source.set_property("caps", audio_caps)
        self.app_source.set_property("format", Gst.Format.TIME)

        # Connect appsrc signals for pushing data
        self.app_source.connect("need-data", self.start_feed)
        self.app_source.connect("enough-data", self.stop_feed)

        # Configure appsink
        self.app_sink.set_property("emit-signals", True)
        self.app_sink.set_property("caps", audio_caps)
        self.app_sink.connect("new-sample", self.new_sample)

        # Add elements to pipeline
        self.pipeline.add(self.app_source)
        self.pipeline.add(self.tee)
        self.pipeline.add(self.audio_queue)
        self.pipeline.add(self.audio_convert1)
        self.pipeline.add(self.audio_resample)
        self.pipeline.add(self.audio_sink)
        self.pipeline.add(self.video_queue)
        self.pipeline.add(self.audio_convert2)
        self.pipeline.add(self.visual)
        self.pipeline.add(self.video_convert)
        self.pipeline.add(self.video_sink)
        self.pipeline.add(self.app_queue)
        self.pipeline.add(self.app_sink)

        # Link static pads
        self.app_source.link(self.tee)

        self.audio_queue.link(self.audio_convert1)
        self.audio_convert1.link(self.audio_resample)
        self.audio_resample.link(self.audio_sink)

        self.video_queue.link(self.audio_convert2)
        self.audio_convert2.link(self.visual)
        self.visual.link(self.video_convert)
        self.video_convert.link(self.video_sink)

        self.app_queue.link(self.app_sink)

        # Manually link tee's request pads to respective queues
        tee_src_pad_template = self.tee.get_pad_template("src_%u")

        self.tee_audio_pad = self.tee.request_pad(tee_src_pad_template, None, None)
        logger.info(
            f"Obtained request pad {self.tee_audio_pad.get_name()} for audio branch"
        )
        audio_queue_pad = self.audio_queue.get_static_pad("sink")
        self.tee_audio_pad.link(audio_queue_pad)

        self.tee_video_pad = self.tee.request_pad(tee_src_pad_template, None, None)
        logger.info(
            f"Obtained request pad {self.tee_video_pad.get_name()} for video branch"
        )
        video_queue_pad = self.video_queue.get_static_pad("sink")
        self.tee_video_pad.link(video_queue_pad)

        self.tee_app_pad = self.tee.request_pad(tee_src_pad_template, None, None)
        logger.info(
            f"Obtained request pad {self.tee_app_pad.get_name()} for app branch"
        )
        app_queue_pad = self.app_queue.get_static_pad("sink")
        self.tee_app_pad.link(app_queue_pad)

        # Set up bus for error messages and create main loop
        self.main_loop = GLib.MainLoop()
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message::error", self.error_cb)

    def push_data(self, _):
        """Pushes CHUNK_SIZE bytes of generated waveform data into appsrc."""
        n_samples = CHUNK_SIZE // 2  # each sample is 2 bytes (16 bits)

        # Generate waveform data
        self.c += self.d
        self.d -= self.c / 1000.0
        freq = 1100 + 1000 * self.d

        raw = array("H")
        for i in range(n_samples):  # Replace xrange with range
            self.a += self.b
            self.b -= self.a / freq
            a5 = (int(500 * self.a)) % 65535
            raw.append(a5)

        b_data = raw.tobytes()

        self.num_samples += n_samples

        # Set its timestamp and duration
        buffer = Gst.Buffer.new_allocate(None, len(b_data), None)
        buffer.fill(0, b_data)
        buffer.pts = Gst.util_uint64_scale(self.num_samples, Gst.SECOND, SAMPLE_RATE)
        buffer.duration = Gst.util_uint64_scale(n_samples, Gst.SECOND, SAMPLE_RATE)

        ret = self.app_source.emit("push-buffer", buffer)
        if ret != Gst.FlowReturn.OK:
            return False
        return True

    def start_feed(self, src, size):
        """Callback when appsrc needs data."""
        if self.sourceid is None:
            logger.info("Start feeding")
            self.sourceid = GLib.idle_add(self.push_data, None)

    def stop_feed(self, src):
        """Callback when appsrc has enough data."""
        if self.sourceid is not None:
            logger.info("Stop feeding")
            GLib.source_remove(self.sourceid)
            self.sourceid = None

    def new_sample(self, sink):
        """Callback when appsink receives a new sample."""
        sample = sink.emit("pull-sample")
        if sample:
            logger.info("*")
            return Gst.FlowReturn.OK
        return Gst.FlowReturn.ERROR

    def error_cb(self, bus, msg):
        """Error callback for the bus."""
        err, debug_info = msg.parse_error()
        logger.error(f"Error received from element {msg.src.get_name()}: {err.message}")
        logger.error(f"Debugging information: {debug_info if debug_info else 'none'}")
        self.main_loop.quit()

    def run(self):
        """Starts the pipeline and runs the main loop."""
        self.pipeline.set_state(Gst.State.PLAYING)
        try:
            self.main_loop.run()
        except KeyboardInterrupt:
            pass
        self.stop()

    def stop(self):
        """Stops the pipeline and cleans up resources."""
        # Release request pads from tee
        self.tee.release_request_pad(self.tee_audio_pad)
        self.tee.release_request_pad(self.tee_video_pad)
        self.tee.release_request_pad(self.tee_app_pad)
        self.pipeline.set_state(Gst.State.NULL)
        self.pipeline.unref()


if __name__ == "__main__":
    generator = Generator()
    generator.run()
