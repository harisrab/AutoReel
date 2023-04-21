# Reels Generator Engine

To Do:

- [ ] (Manual for now) Re-train the UMT model https://github.com/TencentARC/UMT Unified-Multi Modal Transformer Model on political content to extract high click potential content.
- [x] Perform video cropping, automated to 9:16 aspect
- [x] Integrate Speech to Text engine Whisper (English, Urdu, Hindi, etc.)
- [x] Generate --.srt files
- [x] Chop SRT to < 8 words, 2 lines per frame.
- [x] Animate srt ontop of the video in Python.
- [x] Add Instagram style filters. A range of them.
- [x] An interface to download videos to upload on accounts.


Installation:

1. Setup a VM
2. Install and setup Docker

All mediapipe missing files can be found here.
- https://storage.googleapis.com/mediapipe-assets/

Compiled AutoFlip Docker Image can be found at this link
- https://hub.docker.com/repository/docker/harisrab/autoflip_compiled/general
