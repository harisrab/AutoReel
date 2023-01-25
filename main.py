from pathlib import Path

import gradio as gr
from moviepy.editor import *
from pytube import YouTube

from helpers import *


def Pipeline(yt_url, timestamps, subtitles, filter_selected):
    input_file_path = './input.mp4'
    output_filename = 'sample.mp4'
    output_aspect = '9:16'
    container_ram_limit = '13g'

    # Convert the timestamps to seconds -> ["HH:MM:SS", ...] -> [0, 16, 74, 81, 156, 161]
    timestamps = convert_times_to_seconds(timestamps)

    # Download the YouTube video and chop it into multiple segments
    print("[+] Downloading and chopping")
    original_filename = DownloadChop_YT_Video(yt_url, timestamps)

    # Crop the footage to a 9:16 aspect ratio
    print("[+] Cropping the footage")
    CropFootage(input_file_path, output_filename,
                output_aspect, container_ram_limit)

    if subtitles:
        # Take the video and generate srt
        print("[+] Generating Transcription")
        GetTranscriptionSRT(f"./output/{output_filename}")

        # Cut and shorten the subtitles
        print("[+] Preprocessing the transcription")
        new_srt_filename = PreProcessSRT("./tmp_audio.srt")

        # Apply the Instagram filter to the video
        print("[+] Apply filter")
        ApplyFilter(f"./output/{output_filename}", filter_selected)

        # Add the subtitles to the video
        print("[+] Add subtitles")
        AddSubs(new_srt_filename)

        # Add Audio From a YouTube


        CleanUpOp()
        
        return ["Success!", f"./output.mp4"]
    else:
        # Apply the Instagram filter to the video
        print("[+] Apply filter")
        ApplyFilter(f"./output/{output_filename}", filter_selected)

        # CleanUpOp()

        return ["Success!", f"./tmp_output.mp4"]

    # # Upload the final video to Box Drive
    # print("[+] Upload to the drive.")
    # UploadToDrive("./output.mp4", original_filename)

    # Perform a local clean up


    # except:
    #     return ["Unsuccessful"]


if __name__ == '__main__':

    ig_filters = ['_1977', 'aden', 'brannan', 'brooklyn', 'clarendon', 'earlybird', 'gingham', 'hudson', 'inkwell', 'kelvin', 'lark', 'lofi',
                  'maven', 'mayfair', 'moon', 'nashville', 'perpetua', 'reyes', 'rise', 'slumber', 'stinson', 'toaster', 'valencia', 'walden', 'willow', 'xpro2']

    inputs = [
        gr.Text(label="YouTube Link",
                placeholder="https://www.youtube.com/watch?v=FJi1H66qgHM"),
        gr.Text(label="Timestamps",
                placeholder="HH:MM:SS, HH:MM:SS, 00:02:31, 00:02:41, ..."),
        gr.Checkbox(label="Subtitles?"),
        gr.Radio(ig_filters, label="Instagram Filter", default=ig_filters[0]),
                                                                          
                                                                          
    ]

    app = gr.Interface(fn=Pipeline, inputs=inputs, outputs=[
                       "text", gr.Video()], cache_examples=True).queue(1)

    app.launch(share=True)

    # output_filename = 'sample.mp4'


    # # Take the video and generate srt
    # GetTranscriptionSRT(f"./output/{output_filename}")




    # input_file_path = './input.mp4'
    # output_filename = 'sample5.mp4'
    # output_aspect = '9:16'
    # container_ram_limit = '13g'

    # yt_url = "https://www.youtube.com/watch?v=65U5byDZ55M"
    # timestamps = "00:00:00,00:00:10,00:00:20,00:00:40"

    # # Convert the timestamps to seconds -> ["HH:MM:SS", ...] -> [0, 16, 74, 81, 156, 161]
    # timestamps = convert_times_to_seconds(timestamps)

    # # Download the YouTube video and chop it into multiple segments
    # original_filename = DownloadChop_YT_Video(yt_url, timestamps)

    # CropFootage("tdarkk_sample.mp4", output_filename,
    #             output_aspect, container_ram_limit)

    # Pipeline("https://www.youtube.com/watch?v=65U5byDZ55M",
    #          "00:00:00,00:00:40", "aden")


    # AddSubs("video_new.srt")