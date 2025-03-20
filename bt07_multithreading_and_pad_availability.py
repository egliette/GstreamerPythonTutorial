#!/usr/bin/env python3 
import os
# Show error and log messages
os.environ["GST_DEBUG"] = "2"
import sys
import logging
logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)s] - %(message)s")
logger = logging.getLogger(__name__)
import gi
gi.require_version("Gst", "1.0")
from gi.repository import Gst

def main():
    # initialize GStreamer
    Gst.init(sys.argv)

    # create the elements
    audio_source = Gst.ElementFactory.make("audiotestsrc", "audio_source")
    tee = Gst.ElementFactory.make("tee", "tee")
    audio_queue = Gst.ElementFactory.make("queue", "audio_queue")
    audio_convert = Gst.ElementFactory.make("audioconvert", "audio_convert")
    audio_resample = Gst.ElementFactory.make("audioresample", "audio_resample")
    audio_sink = Gst.ElementFactory.make("autoaudiosink", "audio_sink")
    video_queue = Gst.ElementFactory.make("queue", "video_queue")
    visual = Gst.ElementFactory.make("wavescope", "visual")
    video_convert = Gst.ElementFactory.make("videoconvert", "video_convert")
    video_sink = Gst.ElementFactory.make("autovideosink", "video_sink")

    # create the empty pipeline
    pipeline = Gst.Pipeline.new("test-pipeline")

    if (not pipeline or not audio_source or not tee or not audio_queue
            or not audio_convert or not audio_resample or not audio_sink
            or not video_queue or not visual or not video_convert
            or not video_sink):
        logger.error("Not all elements could be created.")
        sys.exit(1)

    # configure elements
    audio_source.set_property("freq", 215.0)
    visual.set_property("shader", 0)
    visual.set_property("style", 1)

    # link all elements that can be automatically linked because they have
    # always pads
    pipeline.add(audio_source)
    pipeline.add(tee)
    pipeline.add(audio_queue)
    pipeline.add(audio_convert)
    pipeline.add(audio_resample)
    pipeline.add(audio_sink)
    pipeline.add(video_queue)
    pipeline.add(visual)
    pipeline.add(video_convert)
    pipeline.add(video_sink)

    audio_source.link(tee)
    audio_queue.link(audio_convert)
    audio_convert.link(audio_resample)
    audio_resample.link(audio_sink)
    video_queue.link(visual)
    visual.link(video_convert)
    video_convert.link(video_sink)


    # manually link the tee, which has "Request" pads
    tee_src_pad_template = tee.get_pad_template("src_%u")

    tee_audio_pad = tee.request_pad(tee_src_pad_template, None, None)
    logger.info(f"Obtained request pad {tee_audio_pad.get_name()} for audio branch")
    audio_queue_pad = audio_queue.get_static_pad("sink")
    tee_audio_pad.link(audio_queue_pad)

    tee_video_pad = tee.request_pad(tee_src_pad_template, None, None)
    logger.info(f"Obtained request pad {tee_video_pad.get_name()} for video branch")
    video_queue_pad = video_queue.get_static_pad("sink")
    tee_video_pad.link(video_queue_pad)


    # start playing
    pipeline.set_state(Gst.State.PLAYING)

    # wait until error or EOS
    terminate = False
    bus = pipeline.get_bus()
    while True:
        try:
            msg = bus.timed_pop_filtered(
                0.5 * Gst.SECOND,
                Gst.MessageType.ERROR | Gst.MessageType.EOS)
            if msg:
                terminate = True
        except KeyboardInterrupt:
            terminate = True

        if terminate:
            break

    pipeline.set_state(Gst.State.NULL)

if __name__ == '__main__':
    main()