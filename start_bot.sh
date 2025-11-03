#!/bin/bash
set -euo pipefail

# ========================= FIX START =========================
# 1. Start Xvfb (Virtual Display) IN THE BACKGROUND
# We are now running this manually instead of using xvfb-run
echo "Starting Xvfb on :99..."
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99
sleep 1 # Give Xvfb a second to start
# ========================== FIX END ==========================

echo '===== Xvfb started, Executing as $(whoami) ====='

# A) Set all environment variables
export PULSE_RUNTIME_PATH=/tmp/pulse
export XDG_RUNTIME_DIR=${PULSE_RUNTIME_PATH}
export PULSE_SERVER=unix:${PULSE_RUNTIME_PATH}/native
export PULSE_SINK=TTS_Sink
export PULSE_COOKIE=~/.config/pulse/cookie

# B) Start PulseAudio
echo 'Starting PulseAudio...'
# We MUST unset PULSE_SERVER for the --start command
unset PULSE_SERVER
pulseaudio --start --exit-idle-time=-1 --log-level=info
# Re-export it immediately so all subsequent commands use it
export PULSE_SERVER=unix:${PULSE_RUNTIME_PATH}/native

# C) Wait for PulseAudio server
echo 'Waiting for PulseAudio server...'
retries=10
while ! pactl info > /dev/null 2>&1; do
    sleep 0.5; retries=$((retries - 1))
    if [ $retries -le 0 ]; then
        echo '❌ CRITICAL: PulseAudio server did not start.'
        exit 1
    fi
    echo "Waiting for PulseAudio... ($retries retries left)"
done
echo '✅ PulseAudio server is running.'

# D) Create virtual sinks/sources
echo 'Configuring PulseAudio devices...'
pactl load-module module-null-sink \
    sink_name=TTS_Sink \
    sink_properties=device.description='Bot_TTS_Output'

pactl load-module module-virtual-source \
    source_name=Bot_Mic \
    master=TTS_Sink.monitor \
    source_properties=device.description='Bot_Virtual_Mic'

pactl load-module module-null-sink \
    sink_name=Meet_Output \
    sink_properties=device.description='Bot_Meet_Speakers'

echo '✅ PulseAudio modules loaded.'

# E) Set defaults
echo 'Setting PulseAudio defaults...'
pactl set-default-source Bot_Mic
pactl set-default-sink Meet_Output
echo '✅ Defaults set.'

# F) Verify devices are visible
echo '=== Verifying PulseAudio Devices ==='
echo '--- Sources (Microphones) ---'
pactl list short sources
echo '--- Sinks (Speakers) ---'
pactl list short sinks
echo '================================='

# G) Set PulseAudio cookie permissions
echo 'Setting PulseAudio cookie permissions...'
if [ -f ~/.config/pulse/cookie ]; then
    chmod 644 ~/.config/pulse/cookie
    echo '✅ Cookie permissions set (644)'
else
    sleep 1 # Wait a moment for cookie to be created
    if [ -f ~/.config/pulse/cookie ]; then
        chmod 644 ~/.config/pulse/cookie
        echo '✅ Cookie permissions set (644)'
    else
        echo '⚠️ Warning: PulseAudio cookie not found'
    fi
fi

# H) Log the environment variables that will be used
echo 'Environment prepared. Exported variables:'
echo "  DISPLAY=$DISPLAY"
echo "  PULSE_SERVER=$PULSE_SERVER"
echo "  PULSE_COOKIE=$PULSE_COOKIE"
echo "  XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
echo "  PULSE_SINK=$PULSE_SINK"

# I) Authentication step (Your logic)
PROFILE_DIR='/app/meet_profile'
PROFILE_CHECK_FILE=${PROFILE_DIR}/Default/Preferences

if [ -f "$PROFILE_CHECK_FILE" ]; then
    echo '✅ Authentication profile already exists. Skipping injection.'
else
    echo '🚀 No profile found. Running authentication injector...'
    python3 -m core.inject_auth --headless
    echo '✅ Authentication profile created.'
fi
echo '==================================================================='

# J) Exec the final command
# "$@" is the command passed from the Docker CMD (e.g., "python3 -m core.meet_bot")
echo "Starting bot process: $@"
exec "$@"