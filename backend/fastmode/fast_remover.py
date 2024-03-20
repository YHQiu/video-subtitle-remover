import cv2


def fast_remove_subtitles(video_file_path, area):
    """
    使用OpenCV模糊视频中的特定区域（如字幕）
    :param video_file_path: 视频文件路径
    :param area: 要模糊的区域，格式为(startY, endY, startX, endX)
    :return: process_video_file_path 处理后视频的路径
    """
    # 读取视频
    cap = cv2.VideoCapture(video_file_path)

    # 获取视频的基本属性
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    codec = cv2.VideoWriter_fourcc(*'mp4v')  # 用于mp4格式的编解码器

    # 输出视频的路径
    process_video_file_path = video_file_path.rsplit('.', 1)[0] + '_blurred_subs.mp4'

    # 创建视频写入对象
    out = cv2.VideoWriter(process_video_file_path, codec, fps, (width, height))

    startY, endY, startX, endX = area

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # 对指定区域应用高斯模糊
        subtitle_area = frame[startY:endY, startX:endX]
        blurred_subtitle = cv2.GaussianBlur(subtitle_area, (25, 25), 3)  # 可以调整高斯模糊的参数
        frame[startY:endY, startX:endX] = blurred_subtitle

        # 写入新的视频文件
        out.write(frame)

    # 释放资源
    cap.release()
    out.release()
    return process_video_file_path

if __name__ == "__main__":
    video_file_path = '23.mp4'
    fast_remove_subtitles(video_file_path, (1100,1280, 0, 720))