import os
import time

import cv2
import numpy as np
import torch
from multiprocessing import Pool, cpu_count
from functools import partial
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from backend import config
from backend.inpaint.sttn.auto_sttn import InpaintGenerator
from backend.inpaint.utils.sttn_utils import Stack, ToTorchFormatTensor

# 定义一个辅助函数来进行图像的预处理和后处理
def preprocess_image(image, model_input_size):
    """缩放图像并进行归一化"""
    image_resized = cv2.resize(image, model_input_size)  # 缩放
    image_transposed = image_resized.transpose(2, 0, 1)  # 转置为CHW
    image_normalized = (image_transposed / 255.0) * 2 - 1  # 归一化到[-1, 1]
    return image_normalized

def postprocess_image(image_normalized):
    """将归一化后的图像还原"""
    image = (image_normalized + 1) / 2 * 255  # 反归一化
    image = image.clip(0, 255).astype(np.uint8)
    image = image.transpose(1, 2, 0)  # 转置回HWC
    return image

def batch_inpaint(model, device, batch_frames, neighbor_stride):
    """批量处理图像填充"""
    batch_size = len(batch_frames)
    if batch_size == 0:
        return []
    # 将数据转换为张量
    tensor_frames = torch.tensor(np.stack(batch_frames, axis=0)).float().to(device)
    # 添加一个假的批次维度，并将数据送到模型
    tensor_frames = tensor_frames.unsqueeze(0)  # 假设模型接受NCHW格式
    with torch.no_grad():
        # 执行模型前向传播
        outputs = model(tensor_frames)
    # 将输出转换回图像
    processed_frames = [postprocess_image(output.cpu().numpy()) for output in outputs.squeeze(0)]
    return processed_frames

def process_video_chunk(model, device, frames, model_input_size, neighbor_stride):
    """处理视频片段的函数，适用于多进程"""
    processed_frames = []
    for frame in frames:
        processed_frame = preprocess_image(frame, model_input_size)
        processed_frames.append(processed_frame)
    # 批量填充处理
    output_frames = batch_inpaint(model, device, processed_frames, neighbor_stride)
    return output_frames

class OptimizedSTTNVideoInpaint:

    def read_frame_info_from_video(self):
        # 使用opencv读取视频
        reader = cv2.VideoCapture(self.video_path)
        # 获取视频的宽度, 高度, 帧率和帧数信息并存储在frame_info字典中
        frame_info = {
            'W_ori': int(reader.get(cv2.CAP_PROP_FRAME_WIDTH) + 0.5),  # 视频的原始宽度
            'H_ori': int(reader.get(cv2.CAP_PROP_FRAME_HEIGHT) + 0.5),  # 视频的原始高度
            'fps': reader.get(cv2.CAP_PROP_FPS),  # 视频的帧率
            'len': int(reader.get(cv2.CAP_PROP_FRAME_COUNT) + 0.5)  # 视频的总帧数
        }
        # 返回视频读取对象、帧信息和视频写入对象
        return reader, frame_info

    def __init__(self, video_path, mask_path=None, clip_gap=None):
        self.video_path = video_path
        self.mask_path = mask_path
        # 设置输出视频文件的路径
        self.video_out_path = os.path.join(
            os.path.dirname(os.path.abspath(self.video_path)),
            f"{os.path.basename(self.video_path).rsplit('.', 1)[0]}_no_sub.mp4"
        )
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.model = InpaintGenerator().to(self.device)
        # 加载模型
        self.model.load_state_dict(torch.load(config.STTN_MODEL_PATH, map_location=self.device)['netG'])
        self.model.eval()
        # 配置
        self.model_input_size = (640, 360)  # 假设的模型输入尺寸
        self.neighbor_stride = 5  # 假设的相邻帧步长
        if clip_gap is None:
            self.clip_gap = 50  # 假设的片段间隔
        else:
            self.clip_gap = clip_gap

    def __call__(self):
        # 读取视频
        # 读取视频帧信息
        reader, frame_info = self.read_frame_info_from_video()
        cap = cv2.VideoCapture(self.video_path)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frames = [cap.read()[1] for _ in range(frame_count)]
        cap.release()

        # 多进程处理
        pool = Pool(processes=cpu_count())
        # 创建分块处理的任务
        chunks = [frames[i:i + self.clip_gap] for i in range(0, len(frames), self.clip_gap)]
        func = partial(process_video_chunk, self.model, self.device, model_input_size=self.model_input_size, neighbor_stride=self.neighbor_stride)
        result_frames = pool.map(func, chunks)
        pool.close()
        pool.join()

        # 将处理后的帧合并成一个列表
        processed_frames = [frame for chunk in result_frames for frame in chunk]

        # 写入处理后的视频
        out = cv2.VideoWriter(self.video_out_path, cv2.VideoWriter_fourcc(*"mp4v"), frame_info['fps'],
                                 (frame_info['W_ori'], frame_info['H_ori']))

        for frame in processed_frames:
            out.write(frame)

        out.release()
        print('Video processing complete and saved.')

if __name__ == '__main__':
    mask_path = '../../test/test.png'
    video_path = '../../test/test.mp4'
    # 记录开始时间
    start = time.time()
    sttn_video_inpaint = OptimizedSTTNVideoInpaint(video_path, mask_path, clip_gap=config.STTN_MAX_LOAD_NUM)
    sttn_video_inpaint()
    print(f'video generated at {sttn_video_inpaint.video_out_path}')
    print(f'time cost: {time.time() - start}')