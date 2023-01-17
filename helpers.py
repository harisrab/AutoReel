
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
        f'./output/{output_filename}', file_name=original_filename)
    print(f'File "{new_file.name}" uploaded to Box with file ID {new_file.id}')


def split_and_stitch_video(video_file=None, seconds_array=None):
    clips = []
    for i in range(0, len(seconds_array), 2):
        start_time = seconds_array[i]
        end_time = seconds_array[i + 1]
        clip = VideoFileClip(video_file).subclip(start_time, end_time)
        clips.append(clip)
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile('input.mp4')


def DownloadChop_YT_Video(yt_url, timestamps):
    yt = YouTube(yt_url)
    download_path = yt.streams.filter(
        only_audio=False, file_extension='mp4', res='720p').first().download()
    split_and_stitch_video(download_path, timestamps)
    Path(download_path).unlink()

    return os.path.basename(download_path)


def convert_times_to_seconds(time_str):
    times = time_str.split(',')
    seconds_list = []
    for t in times:
        t_arr = t.strip().split(':')
        total_seconds = int(t_arr[0]) * 3600 + \
            int(t_arr[1]) * 60 + int(t_arr[2])
        seconds_list.append(total_seconds)
    return seconds_list


def GetTranscriptionSRT(source_video):
    # Unsupported opcode: BEGIN_FINALLY
    model = whisper.load_model('base')
    subprocess.run([
        'ffmpeg',
        '-y',
        '-i',
        source_video,
        '-vn',
        '-acodec',
        'libmp3lame',
        './tmp_audio.mp3'])

    transcription = model.transcribe('tmp_audio.mp3')

    # save SRT
    with open(os.path.join("./", "tmp_srt" + ".srt"), "w", encoding="utf-8") as srt:
        write_srt(transcription["segments"], file=srt)


def CropFootage(input_file_path, output_filename, output_aspect, container_ram_limit):
    os.environ["GLOG_logtostderr"] = "1"

    # start a container and transport the files into it.
    client = docker.from_env()
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
