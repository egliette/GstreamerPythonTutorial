"""
This Python script is based on the GStreamer tutorial:
https://gstreamer.freedesktop.org/documentation/tutorials/basic/media-information-gathering.html?gi-language=python
"""

import os

os.environ["GST_DEBUG"] = "2"
import logging
import re
import sys

logging.basicConfig(
    level=logging.DEBUG, format="[%(name)s] [%(levelname)s] - %(message)s"
)
logger = logging.getLogger(__name__)

import gi

gi.require_version("Gst", "1.0")
gi.require_version("GLib", "2.0")
gi.require_version("GstPbutils", "1.0")
from gi.repository import GLib, Gst, GstPbutils


def format_ns(ns):
    s, ns = divmod(ns, 1000000000)
    m, s = divmod(s, 60)
    h, m = divmod(m, 60)

    return "%u:%02u:%02u.%09u" % (h, m, s, ns)


def parse_taglist(taglist):
    taglist_str = taglist.to_string()
    taglist_str = taglist_str[len("taglist, ") :].rstrip(";")
    taglist_str = re.sub(r"\([^)]*\)", "", taglist_str)
    taglist_str = taglist_str.replace('"', "")
    taglist_str = taglist_str.replace("\\", "")
    pattern = re.compile(r"\s*(?P<key>[\w-]+)=(?P<value>[^,]+)\s*(?:,|$)")
    parsed_dict = {
        match.group("key"): match.group("value").strip()
        for match in pattern.finditer(taglist_str)
    }
    return parsed_dict


class DiscovererApp:
    def __init__(self, uri, timeout=5 * Gst.SECOND):
        self.uri = uri
        self.loop = GLib.MainLoop()
        # Create the Discoverer instance with the given timeout
        self.discoverer = GstPbutils.Discoverer.new(timeout)
        if not self.discoverer:
            logger.error("Error creating discoverer instance.")
            sys.exit(1)
        # Connect signals
        self.discoverer.connect("discovered", self.on_discovered)
        self.discoverer.connect("finished", self.on_finished)

    def print_stream_info(self, sinfo, depth):
        caps = sinfo.get_caps()
        desc = ""
        if caps:
            if caps.is_fixed():
                desc = GstPbutils.pb_utils_get_codec_description(caps)
            else:
                desc = str(caps)
        logger.info(f"{' ' * 2*depth}{sinfo.get_stream_type_nick()}: {desc}")
        tags = sinfo.get_tags()
        if tags:
            logger.info(f"{' ' * 2*(depth+1)}Tags:")
            tags_dict = parse_taglist(tags)
            for tag_name, tag_value in tags_dict.items():
                logger.info(f"{' ' * 2*(depth+2)}{tag_name}: {tag_value}")

    def print_topology(self, sinfo, depth):
        if not sinfo:
            return
        self.print_stream_info(sinfo, depth)
        next_info = sinfo.get_next()
        if next_info:
            self.print_topology(next_info, depth + 1)
        elif isinstance(sinfo, GstPbutils.DiscovererContainerInfo):
            streams = sinfo.get_streams()
            if streams:
                for s in streams:
                    self.print_topology(s, depth + 1)

    def on_discovered(self, discoverer, info, infile):
        uri = info.get_uri()
        result = info.get_result()

        if result == GstPbutils.DiscovererResult.URI_INVALID:
            logger.info(f"Invalid URI '{uri}'")
        elif result == GstPbutils.DiscovererResult.ERROR:
            logger.info(f"Discoverer error: {info.get_misc()}")
        elif result == GstPbutils.DiscovererResult.TIMEOUT:
            logger.info("Timeout")
        elif result == GstPbutils.DiscovererResult.BUSY:
            logger.info("Busy")
        elif result == GstPbutils.DiscovererResult.MISSING_PLUGINS:
            misc = info.get_misc()
            logger.info(f"Missing plugins: {misc}")
        elif result == GstPbutils.DiscovererResult.OK:
            logger.info(f"Discovered '{uri}'")
        else:
            logger.info("Unknown result")

        if result != GstPbutils.DiscovererResult.OK:
            logger.info("This URI cannot be played")
            return

        duration = info.get_duration()
        duration = format_ns(duration)
        logger.info(f"Duration: {duration}")

        tags = info.get_tags()
        if tags:
            logger.info("Tags:")
            tags_dict = parse_taglist(tags)
            for tag_name, tag_value in tags_dict.items():
                logger.info(f"  {tag_name}: {tag_value}")

        seekable = info.get_seekable()
        logger.info(f"Seekable: {'yes' if seekable else 'no'}")

        sinfo = info.get_stream_info()

        if sinfo:
            logger.info("Stream information:")
            self.print_topology(sinfo, 1)

    def on_finished(self, discoverer):
        logger.info("Finished discovering")
        self.loop.quit()

    def run(self):
        self.discoverer.start()
        ret = self.discoverer.discover_uri_async(self.uri)
        if not ret:
            logger.info(f"Failed to start discovering URI '{self.uri}'")
            sys.exit(1)
        self.loop.run()
        self.discoverer.stop()


def main():
    Gst.init(sys.argv)
    uri = "https://gstreamer.freedesktop.org/data/media/sintel_trailer-480p.webm"
    if len(sys.argv) > 1:
        uri = sys.argv[1]
    logger.info(f"Discovering '{uri}'")
    app = DiscovererApp(uri)
    app.run()


if __name__ == "__main__":
    main()
