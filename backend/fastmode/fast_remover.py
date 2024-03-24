import subprocess

import cv2
import srt  # 需要安装 python-srt 库

def has_audio_stream(video_path):
    """Check if the file contains an audio stream."""
    command = [
        'ffprobe', '-v', 'error',
        '-select_streams', 'a',
        '-show_entries', 'stream=codec_name',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    result = subprocess.run(command, stdout=subprocess.PIPE, text=True)
    return result.stdout.strip() != ''


def add_audio_to_video(original_video_path, video_without_audio_path, output_video_path):
    """Add audio from one video file to another."""
    audio_stream_exists = has_audio_stream(original_video_path)

    # Define the base command
    command = ['ffmpeg', '-y']

    # Add input file(s)
    command += ['-i', video_without_audio_path]  # Video input

    if audio_stream_exists:
        command += ['-i', original_video_path]  # Audio input

    # Specify codecs and mapping
    command += ['-c:v', 'copy']  # Default to copy video stream; consider '-c:v libx264' for re-encoding

    if audio_stream_exists:
        command += ['-c:a', 'aac', '-strict', 'experimental', '-map', '0:v:0', '-map', '1:a:0']
    else:
        print("No audio stream found in the original video. Proceeding without adding audio.")

    # Specify output file
    command.append(output_video_path)

    # Execute the command
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error during ffmpeg execution: {e}")

def parse_subtitles(subtitle_path):
    """解析SRT字幕文件，返回每条字幕的开始和结束时间（以秒为单位）的列表"""
    with open(subtitle_path, 'r', encoding='utf-8') as file:
        subtitle_generator = srt.parse(file.read())
        subtitles = list(subtitle_generator)
    return [(subtitle.start.total_seconds(), subtitle.end.total_seconds()) for subtitle in subtitles]

def is_within_subtitles(timestamp, subtitles):
    """检查给定的时间戳是否在字幕显示的时间内"""
    for start, end in subtitles:
        if start-0.1 <= timestamp <= end+0.1:
            return True
    return False

def fast_remove_subtitles(video_file_path, area, **kwargs):
    subtitle_path = kwargs.get('subtitle_path', None)
    subtitles = []
    if subtitle_path:
        subtitles = parse_subtitles(subtitle_path)

    cap = cv2.VideoCapture(video_file_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    codec = cv2.VideoWriter_fourcc(*'mp4v')
    process_video_file_path = video_file_path.rsplit('.', 1)[0] + '_blurred_subs.mp4'
    out = cv2.VideoWriter(process_video_file_path, codec, fps, (width, height))
    # 覆盖区域
    startY, endY, startX, endX = area
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Calculate the timestamp of the current frame
        timestamp = frame_count / fps
        frame_count += 1

        # Check if the current frame's timestamp is within any of the subtitle timestamps
        if subtitles and is_within_subtitles(timestamp, subtitles):
            # Apply Gaussian Blur
            subtitle_area = frame[startY:endY, startX:endX]
            blurred_subtitle = cv2.GaussianBlur(subtitle_area, (25, 25), 10)
            frame[startY:endY, startX:endX] = blurred_subtitle

        out.write(frame)

    cap.release()
    out.release()
    out_put_video_path = video_file_path.rsplit('.', 1)[0] + '_blurred_subs_out.mp4'
    add_audio_to_video(video_file_path, process_video_file_path, out_put_video_path)
    return out_put_video_path


if __name__ == "__main__":
    video_file_path = '02.mp4'
    subtitle_path = '02.srt'  # 假设字幕文件与视频文件同目录
    fast_remove_subtitles(video_file_path, (480, 520, 50, 900), subtitle_path=subtitle_path)
