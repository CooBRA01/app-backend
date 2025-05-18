FROM python:3.12  
ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt 
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:6000", "--workers", "3", "main:app"]