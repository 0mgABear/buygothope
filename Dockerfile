FROM --platform=linux/amd64 mcr.microsoft.com/playwright/python:v1.45.0-jammy

# Install required libraries for Chromium in Lambda
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk1.0-0 \
    libcups2 \
    libx11-6 \
    libxcomposite1 \
    libdrm2 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libxkbcommon0 \
    libasound2 \
    fonts-noto-color-emoji \
    --no-install-recommends && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install awslambdaric
RUN python3 -m pip install playwright==1.45.0
RUN python3 -m playwright install chromium

WORKDIR /var/task
COPY lambda_function.py .

CMD ["python3", "-m", "awslambdaric", "lambda_function.lambda_handler"]