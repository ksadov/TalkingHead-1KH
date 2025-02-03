#!/bin/bash

in_dir=$1
out_dir=$2

mkdir $out_dir;
for f in $in_dir/*.mp4
do
  y=${f##*/};
  ffmpeg -i $f -c:v copy -c:a copy -map 0 -segment_time 00:01:00 -f segment -reset_timestamps 1 $out_dir/${y/.mp4}_%04d.mp4;
done
