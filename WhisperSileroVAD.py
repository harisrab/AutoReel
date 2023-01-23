import json
import urllib.request
import datetime
from tqdm import tqdm
import srt
import ffmpeg
import os
import whisper
import torch
import tensorflow as tf
import subprocess


def WhisperTranscribe(audio_path):
    audio_path = audio_path  # @param {type:"string"}
    model_size = "medium.en"  # @param ["medium", "large"]
    language = "english"  # @param {type:"string"}
    # @param ["End-to-end Whisper (default)", "Whisper -> DeepL", "No translation"]
    translation_mode = "End-to-end Whisper (default)"
    # @markdown Advanced settings:
    deepl_authkey = ""  # @param {type:"string"}
    source_separation = False  # @param {type:"boolean"}
    vad_threshold = 0.4  # @param {type:"number"}
    chunk_threshold = 3.0  # @param {type:"number"}
    deepl_target_lang = "EN-US"  # @param {type:"string"}
    max_attempts = 1  # @param {type:"integer"}
    initial_prompt = ""  # @param {type:"string"}

    # Configuration
    assert max_attempts >= 1
    assert vad_threshold >= 0.01
    assert chunk_threshold >= 0.1
    assert audio_path != ""
    assert language != ""
    if translation_mode == "End-to-end Whisper (default)":
        task = "translate"
        run_deepl = False
    elif translation_mode == "Whisper -> DeepL":
        task = "transcribe"
        run_deepl = True
    elif translation_mode == "No translation":
        task = "transcribe"
        run_deepl = False
    else:
        raise ValueError("Invalid translation mode")
    if initial_prompt.strip() == "":
        initial_prompt = None

    if "http://" in audio_path or "https://" in audio_path:
        print("Downloading audio...")
        urllib.request.urlretrieve(audio_path, "input_file")
        audio_path = "input_file"
    else:
        if not os.path.exists(audio_path):
            try:
                audio_path = uploaded_file
                if not os.path.exists(audio_path):
                    raise ValueError(
                        "Input audio not found. Is your audio_path correct?")
            except NameError:
                raise ValueError(
                    "Input audio not found. Did you upload a file?")

    out_path = os.path.splitext(audio_path)[0] + ".srt"
    out_path_pre = os.path.splitext(audio_path)[0] + "_Untranslated.srt"
    if source_separation:
        print("Separating vocals...")

        os.system(
            f'ffprobe -i "{audio_path}" -show_entries format=duration -v quiet -of csv="p=0" > input_length')

        with open("input_length") as f:
            input_length = int(float(f.read())) + 1

        os.system(
            f'spleeter separate -d {input_length} -p spleeter:2stems -o output "{audio_path}"')

        spleeter_dir = os.path.basename(os.path.splitext(audio_path)[0])
        audio_path = "output/" + spleeter_dir + "/vocals.wav"

    print("Encoding audio...")
    if not os.path.exists("vad_chunks"):
        os.mkdir("vad_chunks")
    ffmpeg.input(audio_path).output(
        "vad_chunks/silero_temp.wav",
        ar="16000",
        ac="1",
        acodec="pcm_s16le",
        map_metadata="-1",
        fflags="+bitexact",
    ).overwrite_output().run(quiet=True)

    print("Running VAD...")
    model, utils = torch.hub.load(
        repo_or_dir="snakers4/silero-vad", model="silero_vad", onnx=False
    )

    (get_speech_timestamps, save_audio, read_audio,
     VADIterator, collect_chunks) = utils

    # Generate VAD timestamps
    VAD_SR = 16000
    wav = read_audio("vad_chunks/silero_temp.wav", sampling_rate=VAD_SR)
    t = get_speech_timestamps(
        wav, model, sampling_rate=VAD_SR, threshold=vad_threshold)

    # Add a bit of padding, and remove small gaps
    for i in range(len(t)):
        t[i]["start"] = max(0, t[i]["start"] - 3200)  # 0.2s head
        t[i]["end"] = min(wav.shape[0] - 16, t[i]["end"] + 20800)  # 1.3s tail
        if i > 0 and t[i]["start"] < t[i - 1]["end"]:
            t[i]["start"] = t[i - 1]["end"]  # Remove overlap

    # If breaks are longer than chunk_threshold seconds, split into a new audio file
    # This'll effectively turn long transcriptions into many shorter ones
    u = [[]]
    for i in range(len(t)):
        if i > 0 and t[i]["start"] > t[i - 1]["end"] + (chunk_threshold * VAD_SR):
            u.append([])
        u[-1].append(t[i])

    # Merge speech chunks
    for i in range(len(u)):
        save_audio(
            "vad_chunks/" + str(i) + ".wav",
            collect_chunks(u[i], wav),
            sampling_rate=VAD_SR,
        )
    os.remove("vad_chunks/silero_temp.wav")

    # Convert timestamps to seconds
    for i in range(len(u)):
        time = 0.0
        offset = 0.0
        for j in range(len(u[i])):
            u[i][j]["start"] /= VAD_SR
            u[i][j]["end"] /= VAD_SR
            u[i][j]["chunk_start"] = time
            time += u[i][j]["end"] - u[i][j]["start"]
            u[i][j]["chunk_end"] = time
            if j == 0:
                offset += u[i][j]["start"]
            else:
                offset += u[i][j]["start"] - u[i][j - 1]["end"]
            u[i][j]["offset"] = offset

    # Run Whisper on each audio chunk
    print("Running Whisper...")
    model = whisper.load_model(model_size)
    subs = []
    segment_info = []
    sub_index = 1
    suppress_low = [
        "Thank you",
        "Thanks for",
        "ike and ",
        "Bye.",
        "Bye!",
        "Bye bye!",
        "lease sub",
        "The end.",
        "視聴",
    ]
    suppress_high = [
        "ubscribe",
        "my channel",
        "the channel",
        "our channel",
        "ollow me on",
        "for watching",
        "hank you for watching",
        "for your viewing",
        "r viewing",
        "Amara",
        "next video",
        "full video",
        "ranslation by",
        "ranslated by",
        "ee you next week",
        "ご視聴",
        "視聴ありがとうございました",
    ]

    for i in tqdm(range(len(u))):
        line_buffer = []  # Used for DeepL
        for x in range(max_attempts):
            result = model.transcribe(
                "vad_chunks/" + str(i) + ".wav", task=task, language=language, initial_prompt=initial_prompt
            )
            # Break if result doesn't end with severe hallucinations
            if len(result["segments"]) == 0:
                break
            elif result["segments"][-1]["end"] < u[i][-1]["chunk_end"] + 10.0:
                break
            elif x+1 < max_attempts:
                print("Retrying chunk", i)
        for r in result["segments"]:
            # Skip audio timestamped after the chunk has ended
            if r["start"] > u[i][-1]["chunk_end"]:
                continue
            # Reduce log probability for certain words/phrases
            for s in suppress_low:
                if s in r["text"]:
                    r["avg_logprob"] -= 0.15
            for s in suppress_high:
                if s in r["text"]:
                    r["avg_logprob"] -= 0.35
            # Keep segment info for debugging
            del r["tokens"]
            segment_info.append(r)
            # Skip if log prob is low or no speech prob is high
            if r["avg_logprob"] < -1.0 or r["no_speech_prob"] > 0.7:
                continue
            # Set start timestamp
            start = r["start"] + u[i][0]["offset"]
            for j in range(len(u[i])):
                if (
                    r["start"] >= u[i][j]["chunk_start"]
                    and r["start"] <= u[i][j]["chunk_end"]
                ):
                    start = r["start"] + u[i][j]["offset"]
                    break
            # Prevent overlapping subs
            if len(subs) > 0:
                last_end = datetime.timedelta.total_seconds(subs[-1].end)
                if last_end > start:
                    subs[-1].end = datetime.timedelta(seconds=start)
            # Set end timestamp
            end = u[i][-1]["end"] + 0.5
            for j in range(len(u[i])):
                if r["end"] >= u[i][j]["chunk_start"] and r["end"] <= u[i][j]["chunk_end"]:
                    end = r["end"] + u[i][j]["offset"]
                    break

            # Add to SRT list
            subs.append(
                srt.Subtitle(
                    index=sub_index,
                    start=datetime.timedelta(seconds=start),
                    end=datetime.timedelta(seconds=end),
                    content=r["text"].strip(),
                )
            )

            sub_index += 1

    with open("segment_info.json", "w", encoding="utf8") as f:
        json.dump(segment_info, f, indent=4)

    # Removal of garbage lines
    garbage_list = [
        "a",
        "aa",
        "ah",
        "ahh",
        "ha",
        "haa",
        "hah",
        "haha",
        "hahaha",
        "mmm",
        "mm",
        "m",
        "h",
        "o",
        "mh",
        "mmh",
        "hm",
        "hmm",
        "huh",
        "oh",
    ]
    need_context_lines = [
        "feelsgod",
        "godbye",
        "godnight",
        "thankyou",
    ]
    clean_subs = list()
    last_line_garbage = False
    for i in range(len(subs)):
        c = subs[i].content
        c = (
            c.replace(".", "")
            .replace(",", "")
            .replace(":", "")
            .replace(";", "")
            .replace("!", "")
            .replace("?", "")
            .replace("-", " ")
            .replace("  ", " ")
            .replace("  ", " ")
            .replace("  ", " ")
            .lower()
            .replace("that feels", "feels")
            .replace("it feels", "feels")
            .replace("feels good", "feelsgood")
            .replace("good bye", "goodbye")
            .replace("good night", "goodnight")
            .replace("thank you", "thankyou")
            .replace("aaaaaa", "a")
            .replace("aaaa", "a")
            .replace("aa", "a")
            .replace("aa", "a")
            .replace("mmmmmm", "m")
            .replace("mmmm", "m")
            .replace("mm", "m")
            .replace("mm", "m")
            .replace("hhhhhh", "h")
            .replace("hhhh", "h")
            .replace("hh", "h")
            .replace("hh", "h")
            .replace("oooooo", "o")
            .replace("oooo", "o")
            .replace("oo", "o")
            .replace("oo", "o")
        )
        is_garbage = True
        for w in c.split(" "):
            if w.strip() == "":
                continue
            if w.strip() in garbage_list:
                continue
            elif w.strip() in need_context_lines and last_line_garbage:
                continue
            else:
                is_garbage = False
                break
        if not is_garbage:
            clean_subs.append(subs[i])
        last_line_garbage = is_garbage
    with open(out_path, "w", encoding="utf8") as f:
        f.write(srt.compose(clean_subs))
    print("\nDone! Subs written to", out_path)
    print("Downloading SRT file:")
