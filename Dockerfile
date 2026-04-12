# Используем официальный образ Python 3.10
FROM python:3.10-slim

# Устанавливаем рабочую директорию в контейнере
WORKDIR /app

# Обновляем pip и устанавливаем зависимости с увеличенным таймаутом
COPY requirements.txt .

RUN grep -q streamlit requirements.txt || echo "\nstreamlit" >> requirements.txt

# Добавляем --default-timeout=100 чтобы избежать обрывов соединения
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 -r requirements.txt

# Копируем весь проект в контейнер
COPY . .

# Создаем папку output если ее нет (на всякий случай)
RUN mkdir -p output

# Указываем порт на котором будет работать Streamlit
EXPOSE 8501

# Команда для запуска приложения
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]