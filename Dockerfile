# 使用與本機相同的 Python 版本作為底層 image
FROM python:3.11

# 設定工作目錄
WORKDIR /app

# 複製相依套件清單並安裝
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式原始碼
COPY app.py .

# 開放 Flask 使用的 port
EXPOSE 5000

# 啟動 Flask 應用程式
CMD ["python", "app.py"]
