# 使用带有CUDA 11.8支持的Ubuntu 20.04镜像作为基础镜像 https://hub.docker.com/
FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime

# 安装您的应用程序需要的其他依赖项
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN add-apt-repository ppa:jonathonf/ffmpeg-4 && apt-get update && apt-get install ffmpeg

# 将您的应用程序代码复制到容器内
COPY . /app
WORKDIR /app

# 安装Python依赖
RUN cd /app
RUN python -m pip install paddlepaddle-gpu==2.4.2.post117 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html
RUN pip install torch==2.0.1 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118
RUN pip install -r requirements.txt

# 指定容器启动时执行的命令
CMD ["python", "app.py"]
