#!/usr/bin/env python3
import os
# Show error and log messages
os.environ["GST_DEBUG"] = "2"
import sys
import logging
logging.basicConfig(level=logging.DEBUG, format="[%(name)s] [%(levelname)s] - %(message)s")
logger = logging.getLogger(__name__)

import sys
import gi
gi.require_version("Gst", "1.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gst, GLib


def print_field(field, value, pfx):
    str = Gst.value_serialize(value)
    logger.debug(f"{pfx}  {GLib.quark_to_string(field):15s}: {str}")
    return True


def print_caps(caps, pfx):
    if not caps:
        return

    if caps.is_any():
        logger.debug(f"{pfx}ANY")
        return

    if caps.is_empty():
        logger.debug(f"{pfx}EMPTY")
        return

    for i in range(caps.get_size()):
        structure = caps.get_structure(i)
        logger.debug(f"{pfx}{structure.get_name()}")
        structure.foreach(print_field, pfx)


# prints information about a pad template (including its capabilities)
def print_pad_templates_information(factory):
    logger.debug(f"Pad templates for {factory.get_name()}")
    if factory.get_num_pad_templates() == 0:
        logger.debug("  none")
        return

    pads = factory.get_static_pad_templates()
    for pad in pads:
        padtemplate = pad.get()

        if pad.direction == Gst.PadDirection.SRC:
            logger.debug(f"  SRC template: {padtemplate.name_template}")
        elif pad.direction == Gst.PadDirection.SINK:
            logger.debug(f"  SINK template: {padtemplate.name_template}")
        else:
            logger.debug(f"  UNKNOWN template: {padtemplate.name_template}")

        if padtemplate.presence == Gst.PadPresence.ALWAYS:
            logger.debug("    Availability: Always")
        elif padtemplate.presence == Gst.PadPresence.SOMETIMES:
            logger.debug("    Availability: Sometimes")
        elif padtemplate.presence == Gst.PadPresence.REQUEST:
            logger.debug("    Availability: On request")
        else:
            logger.debug("    Availability: UNKNOWN")

        if padtemplate.get_caps():
            logger.debug("    Capabilities:")
            print_caps(padtemplate.get_caps(), "      ")

        logger.debug("")


# shows the current capabilities of the requested pad in the given element
def print_pad_capabilities(element, pad_name):
    # retrieve pad
    pad = element.get_static_pad(pad_name)
    if not pad:
        logger.error(f"Could not retrieve pad '{pad_name}'")
        return

    # retrieve negotiated caps (or acceptable caps if negotiation is not
    # yet finished)
    caps = pad.get_current_caps()
    if not caps:
        caps = pad.get_allowed_caps()

    # print
    logger.debug(f"Caps for the {pad_name} pad:")
    print_caps(caps, "      ")


def main():
    # initialize GStreamer
    Gst.init(sys.argv)

    # create the element factories
    source_factory = Gst.ElementFactory.find("audiotestsrc")
    sink_factory = Gst.ElementFactory.find("autoaudiosink")
    if not source_factory or not sink_factory:
        logger.error("Not all element factories could be created")
        return -1

    # print information about the pad templates of these factories
    print_pad_templates_information(source_factory)
    print_pad_templates_information(sink_factory)

    # ask the factories to instantiate the actual elements
    source = source_factory.create("source")
    sink = sink_factory.create("sink")

    # create the empty pipeline
    pipeline = Gst.Pipeline.new("test-pipeline")
    if not pipeline or not source or not sink:
        logger.error("Not all elements could be created")
        return -1

    # build the pipeline
    pipeline.add(source)
    pipeline.add(sink)
    if not source.link(sink):
        logger.error("Could not link source to sink")
        return -1

    # print initial negotiated caps (in NULL state)
    logger.debug("In NULL state:")
    print_pad_capabilities(sink, "sink")

    # start playing
    ret = pipeline.set_state(Gst.State.PLAYING)
    if ret == Gst.StateChangeReturn.FAILURE:
        logger.error("Unable to set the pipeline to the playing state")

    # wait until error, EOS or State-Change
    terminate = False
    bus = pipeline.get_bus()
    while True:
        try:
            msg = bus.timed_pop_filtered(
                0.5 * Gst.SECOND,
                Gst.MessageType.ERROR | Gst.MessageType.EOS | Gst.MessageType.STATE_CHANGED)

            if msg:
                t = msg.type
                if t == Gst.MessageType.ERROR:
                    err, dbg = msg.parse_error()
                    logger.error(f"{msg.src.get_name()} : {err.message}")
                    if dbg:
                        logger.debug(f"Debug information: {dbg}")
                    terminate = True
                elif t == Gst.MessageType.EOS:
                    logger.debug("End-Of-Stream reached")
                    terminate = True
                elif t == Gst.MessageType.STATE_CHANGED:
                    # we are only interested in state-changed messages from the
                    # pipeline
                    if msg.src == pipeline:
                        old, new, pending = msg.parse_state_changed()
                        logger.debug(f"Pipeline state changed from {Gst.Element.state_get_name(old)} to {Gst.Element.state_get_name(new)} :")

                        # print the current capabilities of the sink
                        print_pad_capabilities(sink, "sink")
                else:
                    # should not get here
                    logger.error("Unexpected message received")
        except KeyboardInterrupt:
            terminate = True

        if terminate:
            break

    pipeline.set_state(Gst.State.NULL)


if __name__ == '__main__':
    main()
