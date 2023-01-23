import moviepy.video.VideoClip as clip
import moviepy.video.compositing.CompositeVideoClip as mpComp
from moviepy.editor import VideoFileClip
import pysrt
import re
import youtube_dl
from WhisperSileroVAD import WhisperTranscribe


from moviepy.editor import VideoFileClip, concatenate_videoclips
import os.path as os
from pytube import YouTube
from moviepy.editor import *
import docker
from whisper.utils import write_srt
import whisper
from boxsdk import CCGAuth, Client
import os
from pathlib import Path
import subprocess
import tarfile

import cv2
from tqdm import tqdm
from PIL import Image
import pilgram

import av
import PIL

import numpy as np


def to_docker_copy(src, dest, container_id):
    subprocess.run([
        'docker',
        'cp',
        src,
        f'{container_id}:{dest}'])


def from_docker_copy(src, dest, container_id):
    subprocess.run([
        'docker',
        'cp',
        f'{container_id}:{src}', dest])


def populate_missing_files_in_docker(id):
    to_docker_copy('./missing_data/ssdlite_object_detection.tflite',
                   '/mediapipe/mediapipe/models/', id)
    to_docker_copy('./missing_data/ssdlite_object_detection_labelmap.txt',
                   '/mediapipe/mediapipe/models/', id)


def UploadToDrive(output_filename, original_filename):
    auth = CCGAuth(
        client_id='s41b9e5adk0bl7djcayy59892kcz7g7z',
        client_secret='tZ9ISDIM9gcCMnGu4C6mt5x6aTd3W31U',
        enterprise_id='985783711'
    )

    client = Client(auth)
    user = client.user().get()
    print(f'The current user ID is {user.id}')
    folder_id = '190344925182'
    new_file = client.folder(folder_id).upload(
        f'{output_filename}', file_name=original_filename)
    print(f'File "{new_file.name}" uploaded to Box with file ID {new_file.id}')


def split_and_stitch_video(video_file=None, seconds_array=None):
    clips = []
    for i in range(0, len(seconds_array), 2):
        start_time = seconds_array[i]
        end_time = seconds_array[i + 1]
        clip = VideoFileClip(video_file).subclip(start_time, end_time)
        clips.append(clip)
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile('input.mp4', threads=20)


def DownloadChop_YT_Video(yt_url, timestamps):
    yt = YouTube(yt_url)
    # download_path = yt.streams.filter(
    #     only_audio=False, file_extension='mp4', res='480p').first().download()

    download_path = yt.streams.filter(
        progressive=True, file_extension='mp4')[-1].download()

    # print(download_path)

    split_and_stitch_video(download_path, timestamps)
    Path(download_path).unlink()

    return os.path.basename(download_path)


def convert_times_to_seconds(time_str):
    times = time_str.split(',')
    seconds_list = []
    for t in times:
        t_arr = t.strip().split(':')
        seconds_list.append(
            int(t_arr[0]) * 3600 + int(t_arr[1]) * 60 + int(t_arr[2]))
    return seconds_list


def GetTranscriptionSRT(source_video):
    # load model
    model = whisper.load_model('medium.en')
    # convert video to audio
    subprocess.run([
        'ffmpeg',
        '-y',
        '-i',
        source_video,
        '-vn',
        '-acodec',
        'libmp3lame',
        './tmp_audio.mp3'])

    # # transcribe audio
    # transcription = model.transcribe('tmp_audio.mp3')

    # # save SRT
    # with open(os.path.join("./", "tmp_srt" + ".srt"), "w", encoding="utf-8") as srt:
    #     write_srt(transcription["segments"], file=srt)

    WhisperTranscribe("./tmp_audio.mp3")


def CropFootage(input_file_path, output_filename, output_aspect, container_ram_limit):
    os.environ["GLOG_logtostderr"] = "1"

    # start a container and transport the files into it.
    # client = docker.from_env()
    
    # Create a client object to interact with the Docker daemon
    client = docker.DockerClient(base_url='unix://var/run/docker.sock')

    autoflip_container = client.containers.run(
        "harisrab/autoflip_compiled", detach=True, tty=True, mem_limit=container_ram_limit)

    id = autoflip_container.short_id

    # Populate the missing files in the docker image
    populate_missing_files_in_docker(id)

    # Files to transport: config, input video
    try:
        subprocess.run(["cp", input_file_path, "./data/"])
    except:
        exit()

    # Make an archive of the files to transport
    with tarfile.open('transport_archive.tar', mode='w') as archive:
        archive.add('./data/')

    # Create a directory in the container
    print("[+] mkdir /tmp/src",
          autoflip_container.exec_run('mkdir /tmp/src').output.decode())
    print("[+] mkdir /tmp/src/output/",
          autoflip_container.exec_run('mkdir /tmp/src/output/').output.decode())

    # Copy the files into the container
    to_docker_copy('transport_archive.tar',
                   '/tmp/src/', container_id=id)

    # Untar the data in docker image and delete the original tar file
    print(autoflip_container.exec_run(
        'tar -xvf /tmp/src/transport_archive.tar -C /tmp/src/').output.decode())
    print(autoflip_container.exec_run(
        'rm -r /tmp/src/transport_archive.tar').output.decode())

    # Run the processing script in the container
    tool_path = 'bazel-bin/mediapipe/examples/desktop/autoflip/run_autoflip'
    graph_source = '/tmp/src/data/autoflip_graph.pbtxt'
    input_video_path = f'/tmp/src/data/{os.path.basename(input_file_path)}'
    output_video_path = f'/tmp/src/output/{output_filename}'

    cmd = f'{tool_path} --calculator_graph_config_file={graph_source} --input_side_packets=input_video_path={input_video_path},output_video_path={output_video_path},aspect_ratio={output_aspect}'

    print(autoflip_container.exec_run(cmd).output.decode())

    # Retrieve the output video from the container.
    print(autoflip_container.exec_run('ls /tmp/src/output/').output.decode())

    from_docker_copy(
        f"/tmp/src/output/{output_filename}", "./output/", container_id=id)

    # Clean the data (input) directory
    for file in Path("./data").glob('*.mp4'):
        file.unlink()

    # Delete and stop all the running containers
    # print(client.containers.list(all=True))
    for eachContainer in client.containers.list(all=True):
        eachContainer.stop()
        eachContainer.remove()

    # os.system(cmd)


def CleanUpOp():
    os.system("sudo rm -f -r transport_archive.tar")


def trans_filter(image: Image, filter_selected) -> Image:
    # This function should be replaced with your own filter function
    # Apply the instagram filters

    # These filters are defined in the `pilgram` library, which we
    # imported at the top of the file.
    filters = {
        "_1977": pilgram._1977,
        "aden": pilgram.aden,
        "brannan": pilgram.brannan,
        "brooklyn": pilgram.brooklyn,
        "clarendon": pilgram.clarendon,
        "earlybird": pilgram.earlybird,
        "gingham": pilgram.gingham,
        "hudson": pilgram.hudson,
        "inkwell": pilgram.inkwell,
        "kelvin": pilgram.kelvin,
        "lark": pilgram.lark,
        "lofi": pilgram.lofi,
        "maven": pilgram.maven,
        "mayfair": pilgram.mayfair,
        "moon": pilgram.moon,
        "nashville": pilgram.nashville,
        "perpetua": pilgram.perpetua,
        "reyes": pilgram.reyes,
        "rise": pilgram.rise,
        "slumber": pilgram.slumber,
        "stinson": pilgram.stinson,
        "toaster": pilgram.toaster,
        "valencia": pilgram.valencia,
        "walden": pilgram.walden,
        "willow": pilgram.willow,
        "xpro2": pilgram.xpro2
    }

    # If the user selected "None", then return the original image.
    if filter_selected == "None":
        return image

    # Otherwise, apply the filter and return the result.
    else:
        return filters[filter_selected](image)


def ApplyFilter(video_file, filter_selected):
    # Open the video file
    video = cv2.VideoCapture(video_file)

    # Get the video codec information
    codec = cv2.VideoWriter_fourcc(*"mp4v")
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_size = (int(video.get(cv2.CAP_PROP_FRAME_WIDTH)),
                  int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)))

    # Create the output video file
    out = cv2.VideoWriter('./tmp_output.mp4', codec,
                          fps, frame_size, isColor=True)

    # Get the total number of frames in the video
    total_frames = int(video.get(cv2.CAP_PROP_FRAME_COUNT))

    # Iterate over each frame
    with tqdm(total=total_frames, unit='frames') as pbar:
        for frame_num in range(total_frames):
            # Read the current frame
            success, frame = video.read()

            if not success:
                break

            # Convert the frame to a PIL image
            pil_image = Image.fromarray(frame)

            # Pass the PIL image through the trans_filter function
            pil_image = trans_filter(pil_image, filter_selected)

            # Convert the PIL image back to a numpy array
            frame = np.array(pil_image)

            # Write the current frame to the output video file
            out.write(frame)

            pbar.update(1)

    # Release the output video file
    out.release()
    video.release()
    print("Video processing done!")

    # Extract audio from the original video
    audio_file = video_file.split(".")[0] + ".wav"
    command = f"ffmpeg -i {video_file} -vn -ar 44100 -ac 2 -b:a 192k {audio_file}"
    os.system(command)

    # Merge audio and video
    command = f"ffmpeg -y -i tmp_output.mp4 -i {audio_file} -c:v copy -c:a aac -strict experimental tmp_output_with_audio.mp4"
    os.system(command)
    os.remove(audio_file)
    os.remove("tmp_output.mp4")
    os.rename("tmp_output_with_audio.mp4", "tmp_output.mp4")


def AddSubs(new_srt_filename):
    # Load the video
    video = VideoFileClip("tmp_output.mp4")

    # Load the subtitles
    subs = pysrt.open(new_srt_filename)

    # Create a list to hold the subtitle clips
    subtitle_clips = []

    print(clip.TextClip.list('font'))

    # return

    # Iterate through the subtitles
    for sub in subs:
        print(sub.text)
        print("start_time: ", str(sub.start))
        print("end_time: ", str(sub.end))

        # Create a subtitle clip
        padding = 30
        sub_clip = clip.TextClip(
            sub.text, font='Helvetica-Bold', fontsize=16, color='white', method='caption', size=[video.w - (padding * 2), 200])

        # Set the position and duration of the subtitle clip
        sub_clip = sub_clip.set_pos('center').set_start(
            str(sub.start).replace(",", ".")).set_end(str(sub.end).replace(",", "."))

        # Add the subtitle clip to the list
        subtitle_clips.append(sub_clip)

    print(subtitle_clips)

    # # Overlay the subtitle clips on the video
    final_video = mpComp.CompositeVideoClip([video] + subtitle_clips)

    # # Write the final video to disk
    final_video.write_videofile("output.mp4", threads=20)


def PreProcessSRT(srt_file):

    abbreviations = ['Dr.', 'Mr.', 'Mrs.', 'Ms.',
                     'etc.', 'Jr.', 'e.g.']  # You get the idea!
    abbrev_replace = ['Dr', 'Mr', 'Mrs', 'Ms', 'etc', 'Jr', 'eg']
    subs = pysrt.open(srt_file)
    # Dictionary to accumulate new sub-titles (start_time:[end_time,sentence])
    subs_dict = {}
    start_sentence = True   # Toggle this at the start and end of sentences

    # regex to remove html tags from the character count
    tags = re.compile(r'<.*?>')

    # regex to split on ".", "?" or "!" ONLY if it is preceded by something else
    # which is not a digit and is not a space. (Not perfect but close enough)
    # Note: ? and ! can be an issue in some languages (e.g. french) where both ? and !
    # are traditionally preceded by a space ! rather than!
    end_of_sentence = re.compile(r'([^\s\0-9][\.\?\!])')

    # End of sentence characters
    eos_chars = set([".", "?", "!"])

    for sub in subs:
        if start_sentence:
            start_time = sub.start
            start_sentence = False
        text = sub.text

        # Remove multiple full-stops e.g. "and ....."
        text = re.sub('\.+', '.', text)

        # Optional
        for idx, abr in enumerate(abbreviations):
            if abr in text:
                text = text.replace(abr, abbrev_replace[idx])
        # A test could also be made for initials in names i.e. John E. Rotten - showing my age there ;)

        multi = re.split(end_of_sentence, text.strip())
        cps = sub.characters_per_second

        # Test for a sub-title with multiple sentences
        if len(multi) > 1:
            # regex end_of_sentence breaks sentence start and sentence end into 2 parts
            # we need to put them back together again.
            # hence the odd range because the joined end part is then deleted
            # e.g. len=3 give 0 | 5 gives 0,1  | 7 gives 0,1,2
            for cnt in range(divmod(len(multi), 2)[0]):
                multi[cnt] = multi[cnt] + multi[cnt+1]
                del multi[cnt+1]

            for part in multi:
                if len(part):  # Avoid blank parts
                    pass
                else:
                    continue
                # Convert start time to seconds
                h, m, s, milli = re.split(':|,', str(start_time))
                s_time = (3600*int(h))+(60*int(m))+int(s)+(int(milli)/1000)

                # test for existing data
                try:
                    existing_data = subs_dict[str(start_time)]
                    end_time = str(existing_data[0])
                    h, m, s, milli = re.split(':|,', str(existing_data[0]))
                    e_time = (3600*int(h))+(60*int(m))+int(s)+(int(milli)/1000)
                except:
                    existing_data = []
                    e_time = s_time

                # End time is the start time or existing end time + the time taken to say the current words
                # based on the calculated number of characters per second
                # use regex "tags" to remove any html tags from the character count.

                e_time = e_time + len(tags.sub('', part)) / cps

                # Convert start to a timestamp
                s, milli = divmod(s_time, 1)
                m, s = divmod(int(s), 60)
                h, m = divmod(m, 60)
                start_time = "{:02d}:{:02d}:{:02d},{:03d}".format(
                    h, m, s, round(milli*1000))

                # Convert end to a timestamp
                s, milli = divmod(e_time, 1)
                m, s = divmod(int(s), 60)
                h, m = divmod(m, 60)
                end_time = "{:02d}:{:02d}:{:02d},{:03d}".format(
                    h, m, s, round(milli*1000))

                # if text already exists add the current text to the existing text
                # if not use the current text to write/rewrite the dictionary entry
                if existing_data:
                    new_text = existing_data[1] + " " + part
                else:
                    new_text = part
                subs_dict[str(start_time)] = [end_time, new_text]

                # if sentence ends re-set the current start time to the end time just calculated
                if any(x in eos_chars for x in part):
                    start_sentence = True
                    start_time = end_time
                    print("Split", start_time, "-->", end_time,)
                    print(new_text)
                    print('\n')
                else:
                    start_sentence = False

        else:   # This is Not a multi-part sub-title

            end_time = str(sub.end)

            # Check for an existing dictionary entry for this start time
            try:
                existing_data = subs_dict[str(start_time)]
            except:
                existing_data = []

            # if it already exists add the current text to the existing text
            # if not use the current text
            if existing_data:
                new_text = existing_data[1] + " " + text
            else:
                new_text = text
            # Create or Update the dictionary entry for this start time
            # with the updated text and the current end time
            subs_dict[str(start_time)] = [end_time, new_text]

            if any(x in eos_chars for x in text):
                start_sentence = True
                print("Single", start_time, "-->", end_time,)
                print(new_text)
                print('\n')
            else:
                start_sentence = False

    # Generate the new sub-title file from the dictionary
    new_srt_filename = 'video_new.srt'
    idx = 0
    outfile = open(new_srt_filename, 'w')
    for key, text in subs_dict.items():
        idx += 1
        outfile.write(str(idx)+"\n")
        outfile.write(key+" --> "+text[0]+"\n")
        outfile.write(text[1]+"\n\n")

    outfile.close()

    return new_srt_filename
