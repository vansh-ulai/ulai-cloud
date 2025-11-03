# ===============================
# BASE IMAGE: Playwright + Python
# ===============================
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

USER root
ENV DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# ===============================
# 1. Core System Dependencies
# ===============================
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        dbus-x11 \
        xvfb \
        pulseaudio \
        pulseaudio-utils \
        ffmpeg \
        sox \
        alsa-utils \
        portaudio19-dev \
        python3-dev \
        libasound-dev \
        libpulse-dev \
        libasound2-plugins \
        build-essential \
        git \
        curl \
        ca-certificates \
        x11vnc \
        v4l2loopback-dkms \
        v4l2loopback-utils \
        linux-headers-generic \
        pipewire \
        wireplumber \
        libpipewire-0.3-dev \
        xdg-desktop-portal \
        xdg-desktop-portal-gtk \
        fonts-noto-color-emoji \
        fonts-noto-cjk \
        tzdata && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# ===============================
# 2. Audio & Access Permissions
# ===============================
RUN adduser root pulse-access && \
    usermod -aG audio,pulse,pulse-access pwuser

# ===============================
# 3. Working Directory
# ===============================
WORKDIR /app
COPY . /app

# ===============================
# 4. Python Dependencies
# ===============================
RUN python3 -m pip install --upgrade pip setuptools wheel && \
    if [ -f fixed_requirements.txt ]; then \
        pip install --extra-index-url https://download.pytorch.org/whl/cu124 -r fixed_requirements.txt ; \
    elif [ -f requirements_linux.txt ]; then \
        pip install --extra-index-url https://download.pytorch.org/whl/cu124 -r requirements_linux.txt ; \
    else \
        pip install --extra-index-url https://download.pytorch.org/whl/cu124 -r requirements.txt || true ; \
    fi

# ===============================
# 5. Install Playwright Browsers
# ===============================
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN mkdir -p /ms-playwright && chown -R pwuser:pwuser /ms-playwright
USER pwuser
RUN PLAYWRIGHT_BROWSERS_PATH=/ms-playwright python3 -m playwright install chromium
USER root

# ===============================
# 6. Permissions & Entry
# ===============================
RUN mkdir -p /tmp/pulse /run/user/1000 && \
    chown -R pwuser:pwuser /tmp/pulse /run/user/1000 /app && \
    chmod -R 777 /tmp/pulse /run/user/1000 && \
    chmod +x /app/entrypoint.sh

# ===============================
# 7. Environment Setup
# ===============================
ENV DISPLAY=:99
ENV XDG_RUNTIME_DIR=/run/user/1000
ENV XDG_SESSION_TYPE=x11
ENV PIPEWIRE_RUNTIME_DIR=/run/user/1000
ENV PULSE_SERVER=unix:/tmp/pulse/native
ENV PULSE_COOKIE=/home/pwuser/.config/pulse/cookie
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1
ENV TZ=Etc/UTC

# ===============================
# 8. Kernel Module Check
# ===============================
RUN modprobe -r v4l2loopback || true && \
    echo "✅ Kernel module placeholder loaded."

# ===============================
# 9. Entrypoint
# ===============================
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python3", "-m", "core.meet_bot"]
