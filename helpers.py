import subprocess

def docker_copy(src, dest, container_id):
    subprocess.run(["docker", 'cp', src, f'{container_id}:{dest}'])


def populate_missing_files_in_docker(id):
    docker_copy("./missing_data/ssdlite_object_detection.tflite", "/mediapipe/mediapipe/models/", container_id=id)
    docker_copy("./missing_data/ssdlite_object_detection_labelmap.txt",
                "/mediapipe/mediapipe/models/", container_id=id)
    