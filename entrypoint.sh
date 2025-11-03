#!/bin/bash
set -euo pipefail
echo "===== 🧠 Hornet AI Orchestration Entrypoint (Headless Mode) ====="

# ===============================
# 1. Cleanup
# ===============================
echo "🧹 Cleaning stale runtime state..."
rm -rf /var/run/pulse /tmp/pulse /tmp/.X99-lock /tmp/.X11-unix \
       /tmp/pipewire.log /tmp/wireplumber.log /tmp/pulseaudio.log || true
rm -f /var/run/dbus/pid || true

# ===============================
# 2. D-Bus
# ===============================
echo "🔧 Starting D-Bus..."
dbus-uuidgen --ensure=/var/lib/dbus/machine-id || true
dbus-daemon --system --print-address &>/dev/null &

# ===============================
# 3. Virtual Display (Xvfb)
# ===============================
echo "🖥️ Starting virtual Xvfb display..."
mkdir -p /tmp/.X11-unix && chmod 1777 /tmp/.X11-unix
Xvfb :99 -screen 0 1920x1080x24 +extension RANDR &>/tmp/xvfb.log &
export DISPLAY=:99
sleep 1

# ===============================
# 4. PipeWire + WirePlumber
# ===============================
echo "🎥 Starting PipeWire..."
pipewire &>/tmp/pipewire.log || true
wireplumber &>/tmp/wireplumber.log || true
sleep 2

# ===============================
# 5. Chromium Screen Policies
# ===============================
echo "🪄 Writing Chromium screen-capture policies..."
mkdir -p /etc/opt/chrome/policies/managed /etc/chromium/policies/managed
cat > /etc/opt/chrome/policies/managed/screen_capture_policy.json <<'EOF'
{
  "VideoCaptureAllowed": true,
  "AudioCaptureAllowed": true,
  "ScreenCaptureAllowed": true,
  "ScreenCaptureAllowedByOrigins": ["https://meet.google.com"]
}
EOF
cp /etc/opt/chrome/policies/managed/screen_capture_policy.json /etc/chromium/policies/managed/screen_capture_policy.json || true

# ===============================
# 6. PulseAudio Virtual Devices
# ===============================
echo "🔊 Setting up PulseAudio..."
mkdir -p /tmp/pulse /run/user/1000 /home/pwuser/.config/pulse
chmod -R 777 /tmp/pulse /run/user/1000

export XDG_RUNTIME_DIR=/tmp/pulse
export PULSE_SERVER=unix:/tmp/pulse/native
export PULSE_COOKIE=/home/pwuser/.config/pulse/cookie

if [ -w /etc/pulse ]; then
  cat > /etc/pulse/default.pa <<'EOF'
load-module module-null-sink sink_name=Bot-Output sink_properties=device.description=Bot_Virtual_Speaker
load-module module-remap-source master=Bot-Output.monitor source_name=Bot-Input source_properties=device.description=Bot_Virtual_Mic
set-default-source Bot-Input
set-default-sink Bot-Output
EOF
else
  echo "⚠️ /etc/pulse not writable, skipping global config."
fi

pulseaudio --start --exit-idle-time=-1 --disallow-exit --log-level=info &>/tmp/pulseaudio.log || true

for i in {1..10}; do
    [ -S /tmp/pulse/native ] && echo "✅ PulseAudio ready" && break
    echo "⏳ Waiting for PulseAudio..."
    sleep 1
done

# ===============================
# 7. v4l2loopback + ffmpeg (Virtual Camera)
# ===============================
echo "📸 Checking v4l2loopback..."
modprobe -r v4l2loopback &>/dev/null || true
modprobe v4l2loopback devices=1 video_nr=0 exclusive_caps=1 card_label="HornetVirtualScreen" &>/tmp/v4l2mod.log || true
sleep 1

if [ -e /dev/video0 ]; then
    chmod 666 /dev/video0
    echo "✅ /dev/video0 active"
else
    echo "⚠️ /dev/video0 missing, attempting Xvfb->ffmpeg virtual feed..."
    ffmpeg -y -f x11grab -video_size 1920x1080 -framerate 25 -i :99 \
      -vcodec rawvideo -pix_fmt yuv420p -f v4l2 /dev/video0 \
      -threads 0 -loglevel error &>/tmp/ffmpeg_virtual_screen.log & || true
    sleep 1
fi

# ===============================
# 8. Auth Profile (if missing)
# ===============================
PROFILE_DIR="/app/meet_profile"
PROFILE_CHECK_FILE="${PROFILE_DIR}/Default/Preferences"
if ! su - pwuser -c "[ -f \"$PROFILE_CHECK_FILE\" ]"; then
    echo "🚀 Injecting auth..."
    su - pwuser -c "python3 -m core.inject_auth --headless" || true
fi

# ===============================
# 9. Diagnostics
# ===============================
echo "🔎 Runtime Diagnostics"
echo "  DISPLAY=$DISPLAY"
echo "  PULSE_SERVER=$PULSE_SERVER"
echo "  /dev/video0: $( [ -e /dev/video0 ] && echo yes || echo no )"
echo "  Logs → /tmp/{xvfb,pipewire,wireplumber,pulseaudio}.log"

# ===============================
# 10. Launch Bot
# ===============================
echo "==================================================================="
echo "🚀 Launching Meet Bot..."
exec su -s /bin/bash - pwuser -c "export DISPLAY=${DISPLAY:-:99}; \
  export XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-/tmp/pulse}; \
  export PULSE_SERVER=${PULSE_SERVER:-unix:/tmp/pulse/native}; \
  export PULSE_COOKIE=${PULSE_COOKIE:-/home/pwuser/.config/pulse/cookie}; \
  cd /app; exec $@"
