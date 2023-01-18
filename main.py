from pathlib import Path

import gradio as gr
from moviepy.editor import *
from pytube import YouTube

from helpers import *


def Pipeline(yt_url, timestamps, filter_selected):
    input_file_path = './input.mp4'
    output_filename = 'sample.mp4'
    output_aspect = '9:16'
    container_ram_limit = '13g'

    # try:
    # timestamps = convert_times_to_seconds("HH:MM:SS, HH:MM:SS, ...") ==> [0, 50, 120, 150]
    # timestamps = convert_times_to_seconds(timestamps)

    # # Download the YouTube video and chop it into multiple segments
    # original_filename = DownloadChop_YT_Video(yt_url, timestamps)

    # # # Crop the footage to a 9:16 aspect ratio
    # CropFootage(input_file_path, output_filename,
    #             output_aspect, container_ram_limit)

    # # Take the video and generate srt
    # GetTranscriptionSRT(f"./output/{output_filename}")

    # ApplyFilter
    ApplyFilter(f"./output/{output_filename}", filter_selected)

    # im = Image.open('sample.jpg')
    # trans_filter(Image.open('sample.jpg'), "brannan").save("output.jpg")

    # # Upload the final video to Box Drive
    # UploadToDrive(output_filename, original_filename)

    # # Perform a local clean up
    # CleanUpOp()

    return ["Success!", f"./output/{output_filename}"]

    # except:
    #     return ["Unsuccessful"]


if __name__ == '__main__':

    ig_filters = ['_1977', 'aden', 'brannan', 'brooklyn', 'clarendon', 'earlybird', 'gingham', 'hudson', 'inkwell', 'kelvin', 'lark', 'lofi',
                  'maven', 'mayfair', 'moon', 'nashville', 'perpetua', 'reyes', 'rise', 'slumber', 'stinson', 'toaster', 'valencia', 'walden', 'willow', 'xpro2']

    # inputs = [
    #     gr.Text(label="YouTube Link",
    #             placeholder="https://www.youtube.com/watch?v=FJi1H66qgHM"),
    #     gr.Text(label="Timestamps",
    #             placeholder="HH:MM:SS, HH:MM:SS, 00:02:31, 00:02:41, ..."),
    #     gr.Radio(ig_filters, label="Instagram Filter", default=ig_filters[0])
    # ]

    # app = gr.Interface(fn=Pipeline, inputs=inputs, outputs=[
    #                    "text", gr.Video()], cache_examples=True).queue(2)

    # app.launch(share=True)

    # # Pipeline("https://www.youtube.com/watch?v=FJi1H66qgHM",
    # #          "00:00:08,00:00:24,00:01:14,00:01:21,00:02:36,00:02:41")

    new_srt_filename = PreProcessSRT("./subs.srt")


    ApplyFilter(f"./sample_out4.mp4", "kelvin")

    AddSubs(new_srt_filename)


    # CleanUpOp()
