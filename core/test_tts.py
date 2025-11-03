"""
Test script to verify TTS is working with VB-Cable
Run this to test audio output
"""
import subprocess
import logging

logging.basicConfig(level=logging.INFO)

def test_tts_vbcable():
    """Test TTS through VB-Cable"""
    test_message = "Testing VB-Cable audio output. If you hear this in Google Meet, it's working correctly."
    
    print("🎙️ Testing TTS through VB-Cable...")
    print(f"📢 Message: {test_message}")
    print("\n⚠️ IMPORTANT: Make sure VB-Cable is set as your DEFAULT PLAYBACK DEVICE")
    print("   1. Right-click speaker icon in taskbar")
    print("   2. Select 'Sound settings'")
    print("   3. Under 'Output', select 'CABLE Input (VB-Audio Virtual Cable)'\n")
    
    try:
        # Escape single quotes for PowerShell
        escaped_text = test_message.replace("'", "''")
        
        # PowerShell script with faster speech
        ps_script = f"""
Add-Type -AssemblyName System.Speech
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
$synth.Rate = 2
$synth.Volume = 100
$synth.Speak('{escaped_text}')
$synth.Dispose()
"""
        
        print("🔊 Speaking now...")
        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ TTS completed successfully!")
            print("   If you heard the message, VB-Cable is working correctly.")
        else:
            print(f"❌ Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Failed: {e}")
        print("\n💡 Troubleshooting:")
        print("   - Is VB-Cable installed?")
        print("   - Is VB-Cable set as default playback device?")
        print("   - Check Windows Sound settings")

if __name__ == "__main__":
    test_tts_vbcable()