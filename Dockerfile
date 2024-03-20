# 使用带有CUDA 11.8支持的Ubuntu 20.04镜像作为基础镜像 https://hub.docker.com/
#FROM pytorch/pytorch:2.1.0-cuda11.8-cudnn8-runtime
#FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu20.04
#FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu20.04
FROM nvidia/cuda:11.7.1-cudnn8-devel-ubuntu20.04

ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Asia/Shanghai

# 安装您的应用程序需要的其他依赖项
RUN apt-get update && apt-get install -y \
    python3-pip build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安装ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# 将您的应用程序代码复制到容器内
COPY . /app
WORKDIR /app

# 安装Python依赖
RUN cd /app
RUN pip install --upgrade cython -i https://pypi.tuna.tsinghua.edu.cn/simple
#RUN pip install --upgrade scikit-learn
RUN pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
RUN python3 -m pip install paddlepaddle-gpu==2.4.2.post117 -f https://www.paddlepaddle.org.cn/whl/linux/mkl/avx/stable.html
RUN pip install torch==2.0.1 torchvision==0.16.0 --index-url https://download.pytorch.org/whl/cu118

EXPOSE 8000

# 指定容器启动时执行的命令
CMD ["python3", "app.py"]
