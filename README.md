# Gstreamer with Python Tutorial

How to re-implement all gstreamer basic tutorials.

**Prerequisites:** This tutorial is designed to run inside a Docker container on WSL2. It assumes that readers have a basic understanding of Docker, WSL, and Python.

## Setup

After change the working directory into this repository and start WSL, run:

```
make build
make run
make attach
```

Check if Gstreamer is already installed by running:
```
gst-launch-1.0 --version
```

## TCP Stream

Server:
```
gst-launch-1.0 videotestsrc !   x264enc tune=zerolatency !   rtph264pay config-interval=1 pt=96 !  "application/x-rtp, media=video, encoding-name=H264, clock-rate=90000, payload=96" !   udpsink host=127.0.0.1 port=5000

```

Client:
```
gst-launch-1.0 -v udpsrc port=5000 caps="application/x-rtp, media=video, encoding-name=H264, clock-rate=90000, payload=96" ! rtph264depay ! avdec_h264 ! videoconvert ! autovideosink
```


Endpoint: `tcp://127.0.0.1:5000`


