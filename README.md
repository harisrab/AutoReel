# Unified-Multimodal Transformer Pipeline for Political Content Creation: TikTok Reel Generator (Under-development)

Welcome to the Unified-Multimodal Transformer for Political Content Generation repository! This powerful tool harnesses the latest advancements in artificial intelligence and machine learning 🧠 to create engaging and high-impact TikTok reels 📹 from political videos. By leveraging the power of transformers and multimodal learning, our tool is able to identify the most interesting and click-worthy segments of a video, automatically edit them, and generate a TikTok reel that is both captivating and informative 🤯.

https://user-images.githubusercontent.com/62747193/233765410-b4bdc4fa-6aee-4125-8d8f-fdbe104aff8a.mp4

## 📋 To Do:

- [ ] (Development under progress) Re-train the UMT model https://github.com/TencentARC/UMT Unified-Multi Modal Transformer Model on political content to extract high click potential content ✅.
- [ ] Implement auto-posting on social channels.
- [x] Add the feature to constantly monitor channels for interview/podcast length videos 📺.
- [x] Perform video cropping, automated to 9:16 aspect 🎞️.
- [x] Integrate Speech to Text engine Whisper (English, Urdu, Hindi, etc.) + Integrate ASR model for clear speech cutting 🗣️.
- [x] Generate --.srt files 📄.
- [x] Chop SRT to < 8 words, 2 lines per frame 📐.
- [x] Animate srt on top of the video in Python 🐍.
- [x] Add Instagram style filters. A range of them 🌈.
- [x] An interface to download videos to upload on accounts ⬇️.
- [x] Wrap up the app into Gradio 🎁.

## 💪 The Power of Unified-Multimodal Transformers

This was a project that I did to understand the construction of transformers and a key application of it in automation of political campaigning 📣. This tool utilizes state-of-the-art Unified-Multimodal Transformers, which are capable of processing and understanding multiple forms of data simultaneously 🌐. This allows the model to analyze and comprehend the intricacies of political content, such as speech, text, and visual cues, resulting in a deeper understanding of the video's context and potential impact on viewers 🎯.

## 🤖 Human-like Editing Capabilities

One of the key features of our tool is its ability to edit the extracted video segments just like a person would 🧑‍💻. This means that the final TikTok reels will have a professional and polished look, making them more appealing to viewers and increasing the chances of your content going viral 🚀.

## 💡 Conclusion

This tool coupled with other technologies available such as LLMs can potentially turn the game for political campaigning by automating spread of content. The training costs for the transformer to identify the segments is too high, so this project has been paused and made public for now, and I plan to build this further a bit later.

## 🛠️ Installation:

1. Setup an Azure VM 🖥️
2. Install and setup Docker 🐳
3. Run the following commands

``` pip3 install -r requirements.txt```

All mediapipe missing files can be found here.
- https://storage.googleapis.com/mediapipe-assets/

Compiled AutoFlip Docker Image can be found at this link
- https://hub.docker.com/repository/docker/harisrab/autoflip_compiled/general
