FROM python:3.12  
ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app
COPY main/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt 
COPY . .
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "3", "main:app"]