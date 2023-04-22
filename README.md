# Reels Generator Engine

# Unified-Multimodal Transformer for Political Content: TikTok Reel Generator

Welcome to the Unified-Multimodal Transformer for Political Content repository! This powerful tool harnesses the latest advancements in artificial intelligence and machine learning to create engaging and high-impact TikTok reels from political videos. By leveraging the power of transformers and multimodal learning, our tool is able to identify the most interesting and click-worthy segments of a video, automatically edit them, and generate a TikTok reel that is both captivating and informative.

https://user-images.githubusercontent.com/62747193/233765410-b4bdc4fa-6aee-4125-8d8f-fdbe104aff8a.mp4

## To Do:

- [ ] (Development under progress) Re-train the UMT model https://github.com/TencentARC/UMT Unified-Multi Modal Transformer Model on political content to extract high click potential content.
- [x] Add the feature to constantly monitor channels for interview/podcast length videos.
- [x] Perform video cropping, automated to 9:16 aspect
- [x] Integrate Speech to Text engine Whisper (English, Urdu, Hindi, etc.) + Integrate ASR model for clear speech cutting.
- [x] Generate --.srt files
- [x] Chop SRT to < 8 words, 2 lines per frame.
- [x] Animate srt ontop of the video in Python.
- [x] Add Instagram style filters. A range of them.
- [x] An interface to download videos to upload on accounts.
- [x] Wrap up the app into Gradio


## The Power of Unified-Multimodal Transformers

This was project that I did to understand the construction of transformers and a key application of it in automation of political campaighing. This tool utilizes state-of-the-art Unified-Multimodal Transformers, which are capable of processing and understanding multiple forms of data simultaneously. This allows the model to analyze and comprehend the intricacies of political content, such as speech, text, and visual cues, resulting in a deeper understanding of the video's context and potential impact on viewers.

## Human-like Editing Capabilities

One of the key features of our tool is its ability to edit the extracted video segments just like a person would. This means that the final TikTok reels will have a professional and polished look, making them more appealing to viewers and increasing the chances of your content going viral.

## Scaled Implications and Potential Impact

The potential power of this tool is immense, especially when considering its applications in the realm of political content. By automating the process of identifying, extracting, and editing high-impact segments from political videos, our tool empowers content creators, journalists, and political analysts to quickly generate engaging and shareable content. This can greatly amplify the reach of important political messages, spur informed discussions, and contribute to a more knowledgeable and engaged electorate.

## Conclusion

We invite you to explore this repository and discover the incredible potential of our Unified-Multimodal Transformer for Political Content. With its advanced capabilities and user-friendly interface, this tool is poised to revolutionize the way political content is created, shared, and consumed on platforms like TikTok. Join us in harnessing the power of AI to make a meaningful impact on the world of politics and beyond.



## Installation:

1. Setup a VM
2. Install and setup Docker

All mediapipe missing files can be found here.
- https://storage.googleapis.com/mediapipe-assets/

Compiled AutoFlip Docker Image can be found at this link
- https://hub.docker.com/repository/docker/harisrab/autoflip_compiled/general
