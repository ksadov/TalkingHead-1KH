import argparse
import multiprocessing as mp
import os
from functools import partial
from time import time as timer
import ffmpeg
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument(
    "--input_dir", type=str, required=True, help="Dir containing youtube clips."
)
parser.add_argument(
    "--clip_info_file",
    type=str,
    required=True,
    help="File containing clip information.",
)
parser.add_argument(
    "--output_dir", type=str, required=True, help="Location to dump outputs."
)
parser.add_argument(
    "--num_workers", type=int, default=8, help="How many multiprocessing workers?"
)
parser.add_argument(
    "--sample_rate", type=int, default=16000, help="Audio sample rate in Hz"
)
args = parser.parse_args()


def get_video_info(filepath):
    probe = ffmpeg.probe(filepath)
    video_stream = next(
        (stream for stream in probe["streams"] if stream["codec_type"] == "video"), None
    )
    height = int(video_stream["height"])
    width = int(video_stream["width"])
    fps = eval(video_stream["r_frame_rate"])  # Convert fraction string to float
    return height, width, fps


def trim_and_crop(input_dir, output_dir, sample_rate, clip_params):
    video_name, H, W, S, E, L, T, R, B = clip_params.strip().split(",")
    H, W, S, E, L, T, R, B = (
        int(H),
        int(W),
        int(S),
        int(E),
        int(L),
        int(T),
        int(R),
        int(B),
    )
    output_filename = "{}_S{}_E{}_L{}_T{}_R{}_B{}.mp4".format(
        video_name, S, E, L, T, R, B
    )
    output_filepath = os.path.join(output_dir, output_filename)
    if os.path.exists(output_filepath):
        print("Output file %s exists, skipping" % (output_filepath))
        return

    input_filepath = os.path.join(input_dir, video_name + ".mp4")
    if not os.path.exists(input_filepath):
        print("Input file %s does not exist, skipping" % (input_filepath))
        return

    h, w, fps = get_video_info(input_filepath)
    t = int(T / H * h)
    b = int(B / H * h)
    l = int(L / W * w)
    r = int(R / W * w)

    # Convert frame numbers to timestamps
    start_time = S / fps
    end_time = (E + 1) / fps

    try:
        # Create input stream
        input_stream = ffmpeg.input(input_filepath)

        # Process video
        v1 = input_stream.video.filter("trim", start_frame=S, end_frame=E + 1)
        v1 = v1.filter("setpts", "PTS-STARTPTS")
        v2 = v1.filter("crop", r - l, b - t, l, t)

        # Process audio using timestamps instead of frames
        a1 = input_stream.audio.filter("atrim", start=start_time, end=end_time)
        a1 = a1.filter("asetpts", "PTS-STARTPTS")
        # Add audio resampling using the provided sample rate
        a1 = a1.filter("aresample", sample_rate)

        # Combine streams
        joined = ffmpeg.concat(v2, a1, v=1, a=1).node
        out = ffmpeg.output(
            joined[0],
            joined[1],
            output_filepath,
            vcodec="libx264",
            acodec="aac",
            video_bitrate="2M",
            ar=sample_rate,  # Set output audio sample rate
        )
        ffmpeg.run(out, overwrite_output=True)
    except ffmpeg.Error as e:
        print(f"Failed to process {video_name}: {str(e)}")
        if os.path.exists(output_filepath):
            os.remove(output_filepath)


if __name__ == "__main__":
    # Read list of videos.
    clip_info = []
    with open(args.clip_info_file) as fin:
        for line in fin:
            clip_info.append(line.strip())

    # Create output folder.
    os.makedirs(args.output_dir, exist_ok=True)

    # Process videos.
    processor = partial(
        trim_and_crop, args.input_dir, args.output_dir, args.sample_rate
    )
    start = timer()
    pool_size = args.num_workers
    print("Using pool size of %d" % (pool_size))
    with mp.Pool(processes=pool_size) as p:
        _ = list(tqdm(p.imap_unordered(processor, clip_info), total=len(clip_info)))
    print("Elapsed time: %.2f" % (timer() - start))
