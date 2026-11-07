FROM python:3.11-slim

WORKDIR /app

# ติดตั้ง dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกโค้ดทั้งหมด
COPY . .

# สร้างภาพตัวอย่างและไอคอน (หากยังไม่มี)
RUN python create_samples.py && python create_icons.py

EXPOSE 7860
ENV PORT=7860

CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "2", "app:app"]
