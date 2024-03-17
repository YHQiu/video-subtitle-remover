import json
import sys

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import FileResponse
import uuid
import uvicorn
from starlette.middleware.cors import CORSMiddleware
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db import db_api

# check 环境
from paddle import fluid
fluid.install_check.run_check()

# 你的FastAPI代码...
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 仅用于示例，实际部署时应限制为真实的前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 上传视频并去除水印
@app.post("/remove-watermark")
async def remove_watermark(file: UploadFile = File(...), area: str = Form(...)):
    area_list = json.loads(area)  # 将JSON字符串解析为Python列表
    # minY maxY minX maxX
    subtitle_area = (area_list[0], area_list[1], area_list[2], area_list[3])
    # 检查文件类型
    if not file.filename.endswith(('.mp4', '.mov')):
        raise HTTPException(status_code=400, detail="Invalid file type.")

    try:
        # 生成唯一的文件名
        temp_filename = os.path.join(db_api.get_temp_dir(), f"temp_{uuid.uuid4()}.mp4")
        with open(temp_filename, "wb") as buffer:
            buffer.write(await file.read())

        # 调用去水印函数
        import backend.main
        output_file = backend.main.SubtitleRemover(temp_filename, subtitle_area, True).run()
        # output_file = temp_filename

        # 清理临时文件
        os.remove(temp_filename)

        return FileResponse(output_file, media_type="application/octet-stream", filename=output_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 主页路由，简单返回一个文本信息
@app.get("/")
async def main():
    return {"message": "Welcome to the watermark removal API!"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info", reload=False)
