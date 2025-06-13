FROM python:3.11-slim

# Настрой работната директория
WORKDIR /app

# Копирай файловете с изисквания и инсталирай зависимостите
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирай целия проект
COPY . .

# Стартирай бота
CMD ["python", "bot.py"]
