import argparse
import multiprocessing as mp
import os
from functools import partial
from time import time as timer

from pytubefix import YouTube
from tqdm import tqdm

parser = argparse.ArgumentParser()
parser.add_argument(
    "--input_list", type=str, required=True, help="List of youtube video ids"
)
parser.add_argument(
    "--output_dir",
    type=str,
    default="data/youtube_videos",
    help="Location to download videos",
)
parser.add_argument(
    "--num_workers", type=int, default=8, help="How many multiprocessing workers?"
)
args = parser.parse_args()


def download_video(output_dir, video_id):
    """Download video with audio."""
    video_path = "%s/%s.mp4" % (output_dir, video_id)
    if not os.path.isfile(video_path):
        try:
            # Download the highest quality progressive stream (includes both video and audio)
            yt = YouTube("https://www.youtube.com/watch?v=%s" % (video_id))
            stream = (
                yt.streams.filter(progressive=True, file_extension="mp4")
                .order_by("resolution")
                .desc()
                .first()
            )
            if stream is None:
                print(
                    f"No progressive stream found for {video_id}, attempting merged download"
                )
                # If no progressive stream, download video and audio separately and merge
                video_stream = (
                    yt.streams.filter(only_video=True, file_extension="mp4")
                    .order_by("resolution")
                    .desc()
                    .first()
                )
                audio_stream = yt.streams.filter(
                    only_audio=True, file_extension="mp4"
                ).first()

                if video_stream and audio_stream:
                    temp_video = f"{output_dir}/{video_id}_temp_video.mp4"
                    temp_audio = f"{output_dir}/{video_id}_temp_audio.mp4"

                    video_stream.download(
                        output_path=output_dir, filename=f"{video_id}_temp_video.mp4"
                    )
                    audio_stream.download(
                        output_path=output_dir, filename=f"{video_id}_temp_audio.mp4"
                    )

                    # Merge using ffmpeg
                    os.system(
                        f"ffmpeg -i {temp_video} -i {temp_audio} -c:v copy -c:a aac {video_path}"
                    )

                    # Clean up temporary files
                    os.remove(temp_video)
                    os.remove(temp_audio)
                else:
                    raise Exception("Could not find suitable video and audio streams")
            else:
                stream.download(output_path=output_dir, filename=video_id + ".mp4")
        except Exception as e:
            print(e)
            print("Failed to download %s" % (video_id))
    else:
        print("File exists: %s" % (video_id))


if __name__ == "__main__":
    # Read list of videos.
    video_ids = []
    with open(args.input_list) as fin:
        for line in fin:
            video_ids.append(line.strip())

    # Create output folder.
    os.makedirs(args.output_dir, exist_ok=True)

    # Download videos.
    downloader = partial(download_video, args.output_dir)

    start = timer()
    pool_size = args.num_workers
    print("Using pool size of %d" % (pool_size))
    with mp.Pool(processes=pool_size) as p:
        _ = list(tqdm(p.imap_unordered(downloader, video_ids), total=len(video_ids)))
    print("Elapsed time: %.2f" % (timer() - start))
