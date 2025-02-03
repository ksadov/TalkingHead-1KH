https://github.com/tcwang0509/TalkingHead-1KH modified to preserve audio in the downloaded videos. For more information about the dataset, see the original repository. Download and processing instructions remain the same:


## Download
### Unzip the video metadata
First, unzip the metadata and put it under the root directory:
```bash
unzip data_list.zip
```

### Unit test
This step downloads a small subset of the dataset to verify the scripts are working on your computer. You can also skip this step if you want to directly download the entire dataset.
```bash
bash videos_download_and_crop.sh small
```
The processed clips should appear in `small/cropped_clips`.

### Download the entire dataset
Please run
```bash
bash videos_download_and_crop.sh train
```
The script will automatically download the YouTube videos, split them into short clips, and then crop and trim them to include only the face regions. The final processed clips should appear in `train/cropped_clips`.


## Evaluation
To download the evaluation set which consists of only 1080p videos, please run
```bash
bash videos_download_and_crop.sh val
```
The processed clips should appear in `val/cropped_clips`.
