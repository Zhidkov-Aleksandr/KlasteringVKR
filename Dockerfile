FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN grep -q streamlit requirements.txt || echo "\nstreamlit" >> requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --default-timeout=100 -r requirements.txt
COPY . .
RUN mkdir -p output
ENV STREAMLIT_THEME_BASE="light"
ENV STREAMLIT_THEME_PRIMARY_COLOR="#3b82f6"
ENV STREAMLIT_THEME_BACKGROUND_COLOR="#f8fafc"
ENV STREAMLIT_THEME_SECONDARY_BACKGROUND_COLOR="#f1f5f9"
ENV STREAMLIT_THEME_TEXT_COLOR="#1e293b"
ENV STREAMLIT_CLIENT_TOOLBAR_MODE="viewer"
EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--client.toolbarMode=viewer"]