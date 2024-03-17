# 基础文件保存路径
import os

BASE_FILE_DIR = "/data/playlet"

TEMP_PATH = "tmp"

def get_base_file_dir():
    os.makedirs(BASE_FILE_DIR, exist_ok=True)
    return BASE_FILE_DIR

def get_temp_dir():
    os.makedirs(os.path.join(BASE_FILE_DIR, TEMP_PATH), exist_ok=True)
    return BASE_FILE_DIR