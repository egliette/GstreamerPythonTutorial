# 🚀 GStreamer with Python Tutorial 🎥🐍

This repository contains Python implementations of the GStreamer tutorials from the [official GStreamer documentation](https://gstreamer.freedesktop.org/documentation/tutorials/basic/index.html?gi-language=python).

## 📌 Prerequisites
📦 This tutorial runs inside a **Docker container** on **WSL2**.
🛠️ Assumes basic knowledge of **Docker, WSL, and Python**.

⚠️ **Warning**: Tested on **Windows 11 WSL** using Docker. If you face issues on another OS while building the Docker image, check `docker-compose.yaml` and adjust **volumes** and **environment variables**.

## 🛠️ Setup

1️⃣ Change to this repository’s directory and start WSL.

2️⃣ Run:
```bash
make init
```
3️⃣ Check if GStreamer is installed:
```bash
gst-launch-1.0 --version
```

📼 **Video Assets**: Some tutorials use different videos for better visualization. 📥 [Download them here](https://drive.google.com/drive/folders/1jbqnScW60jC6H3wJ_yCsgATLO1MHAbff?usp=sharing) and save them in the `videos` folder.

▶️ **Run a tutorial**:
```bash
python bt01_hello_world.py
```

## 📚 References

🔗 [Official GStreamer Documentation](https://gstreamer.freedesktop.org/documentation/tutorials/index.html?gi-language=python)

🔗 [GStreamer Repository](https://gitlab.freedesktop.org/gstreamer/gstreamer)

🔗 [Python GStreamer Tutorial Repo](https://github.com/gkralik/python-gst-tutorial)

🔗 [GStreamer Code Snippets](https://github.com/rubenrua/GstreamerCodeSnippets)
