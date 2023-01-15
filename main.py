import subprocess
import os
import docker
import tarfile

from helpers import *


input_file_path = '~/tdarkk_sample.mp4'
output_filename = 'sample.mp4'
output_aspect = '9:16'
container_ram_limit = '1g'


os.environ["GLOG_logtostderr"] = "1"


# start a container and transport the files into it.
client = docker.from_env()
autoflip_container = client.containers.run(
    "autoflip_compiled", detach=True, tty=True, mem_limit=container_ram_limit)

id = autoflip_container.short_id

# Populate the missing files in the docker image
populate_missing_files_in_docker(id)

# Files to transport: config, input video
subprocess.run(["cp", "/home/pebblexsoft/tdarkk_sample.mp4",
               "/home/pebblexsoft/reel_tool_pipeline/data/"])

# Make an archive of the files to transport
with tarfile.open('transport_archive.tar', mode='w') as archive:
    archive.add('./data/')

# Create a directory in the container
print("[+] mkdir /tmp/src",
      autoflip_container.exec_run('mkdir /tmp/src').output.decode())
print("[+] mkdir /tmp/src",
      autoflip_container.exec_run('mkdir /tmp/src/output/').output.decode())

# Copy the files into the container
docker_copy('transport_archive.tar',
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


# Delete and stop all the running containers
# print(client.containers.list(all=True))
for eachContainer in client.containers.list(all=True):
    eachContainer.stop()
    eachContainer.remove()


# os.system(cmd)
