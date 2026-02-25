"""
ELLIOT Launcher
Double-click this file to start ELLIOT.
It will install everything it needs automatically, then open your browser.
"""

import sys
import os
import subprocess
import importlib.util
import time
import webbrowser
import threading

# ─── Friendly error popup if something goes wrong ─────────────────────────────
def show_error(title, message):
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(title, message)
        root.destroy()
    except:
        pass  # If tkinter fails, we tried

def show_info(title, message):
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        messagebox.showinfo(title, message)
        root.destroy()
    except:
        pass

# ─── Progress window ──────────────────────────────────────────────────────────
class LaunchWindow:
    def __init__(self):
        self.root = None
        self.label = None

    def show(self):
        try:
            import tkinter as tk
            self.root = tk.Tk()
            self.root.title("ELLIOT is starting...")
            self.root.geometry("420x160")
            self.root.resizable(False, False)
            self.root.configure(bg="#0f1117")

            # Center on screen
            self.root.eval('tk::PlaceWindow . center')

            title = tk.Label(self.root, text="🔧 ELLIOT", font=("Helvetica", 22, "bold"),
                             bg="#0f1117", fg="#4ade80")
            title.pack(pady=(20, 4))

            self.label = tk.Label(self.root, text="Starting up...",
                                  font=("Helvetica", 11), bg="#0f1117", fg="#9ca3af")
            self.label.pack()

            sub = tk.Label(self.root, text="Your browser will open automatically",
                           font=("Helvetica", 9), bg="#0f1117", fg="#4b5563")
            sub.pack(pady=(6, 0))

            self.root.update()
        except:
            pass  # No tkinter, just run silently

    def set_status(self, text):
        try:
            if self.label:
                self.label.config(text=text)
                self.root.update()
        except:
            pass

    def close(self):
        try:
            if self.root:
                self.root.destroy()
        except:
            pass


# ─── Main launcher ────────────────────────────────────────────────────────────
def main():
    window = LaunchWindow()
    window.show()

    # Step 1: Check Python version
    if sys.version_info < (3, 8):
        window.close()
        show_error(
            "Python Too Old",
            f"ELLIOT needs Python 3.8 or newer.\n\nYou have Python {sys.version}\n\nDownload the latest at python.org"
        )
        sys.exit(1)

    # Step 2: Install required packages
    packages = {
        "anthropic": "anthropic>=0.40.0",
        "streamlit": "streamlit>=1.35.0",
    }

    for import_name, install_spec in packages.items():
        if importlib.util.find_spec(import_name) is None:
            window.set_status(f"Installing {import_name}... (one-time setup)")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", install_spec, "--quiet"],
                    check=True,
                    capture_output=True
                )
            except subprocess.CalledProcessError:
                window.close()
                show_error(
                    "Install Failed",
                    f"ELLIOT couldn't install '{import_name}'.\n\nMake sure you're connected to the internet and try again.\n\nIf this keeps happening, right-click this file and run as Administrator."
                )
                sys.exit(1)

    # Step 3: Write the app file next to this launcher
    window.set_status("Preparing ELLIOT...")

    launcher_dir = os.path.dirname(os.path.abspath(__file__))
    app_path = os.path.join(launcher_dir, "_elliot_app.py")

    app_code = '''
import streamlit as st
import anthropic
import subprocess
import sys
import os
import tempfile
import traceback
import re

st.set_page_config(
    page_title="ELLIOT — Your Maker AI",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #0f1117; }
    .main-header {
        background: linear-gradient(135deg, #1a1f2e 0%, #0d1117 100%);
        border: 1px solid #2d5a27;
        border-radius: 12px;
        padding: 20px 28px;
        margin-bottom: 24px;
    }
    .main-header h1 { color: #4ade80; font-size: 2rem; font-weight: 800; margin: 0; letter-spacing: -1px; }
    .main-header p { color: #6b7280; margin: 4px 0 0 0; font-size: 0.9rem; }
    .user-bubble {
        background: #1e2533;
        border-left: 3px solid #3b82f6;
        border-radius: 8px;
        padding: 12px 16px;
        margin: 10px 0 4px 0;
        color: #e5e7eb;
    }
    .assistant-label {
        color: #4ade80;
        font-weight: 700;
        font-size: 0.9rem;
        margin: 14px 0 4px 0;
    }
    .run-success {
        background: #0d2818;
        border: 1px solid #2d5a27;
        border-radius: 8px;
        padding: 10px 14px;
        font-family: monospace;
        font-size: 0.85rem;
        color: #4ade80;
        margin: 8px 0;
    }
    .run-error {
        background: #1f0d0d;
        border: 1px solid #7f1d1d;
        border-radius: 8px;
        padding: 10px 14px;
        font-family: monospace;
        font-size: 0.85rem;
        color: #f87171;
        margin: 8px 0;
    }
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, #16a34a, #15803d);
        color: white;
        border: none;
        font-weight: 600;
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)

SYSTEM_PROMPT = """You are ELLIOT — an AI assistant built specifically for makers, hobbyists, and DIYers who can build and wire physical things but aren\'t coders.

Your personality:
- Speak plain English, never jargon without explanation
- Explain EVERY decision inline — e.g. "I\'m using pin 6 because it supports PWM, which is what controls brightness"
- Think like an engineer, talk like a friend at the workbench
- Be honest when something might not work; suggest safer alternatives
- Be encouraging — makers are capable people who just hit a code wall

Your expertise:
- Arduino sketches (C++) and MicroPython for microcontrollers
- WS2812B / NeoPixel LED strips and rings — addressing, power sizing, wiring
- Python scripts for serial comms, data logging, sensor reading
- Power supply sizing: 5V/12V, calculating amps from LED count, wire gauge
- Common components: servos, DHT22, PIR sensors, relays, I2C displays, ultrasonic sensors
- 3D printing considerations: tolerances, mounting points, cable routing

When writing code:
1. Comment every significant line explaining what it does in plain English
2. Specify exact library names and how to install them
3. List all required hardware at the top of the code block
4. Describe wiring inline with code comments
5. End with a "What you should see:" section

For Python scripts that can run without hardware, put # RUNNABLE as the very first line of the code block so ELLIOT can test it automatically.

Always end your response with an "⚡ Quick Checklist" using markdown checkboxes covering hardware needed, libraries to install, wiring steps, and expected behavior."""

def run_python_code(code):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(code)
        tmp = f.name
    try:
        result = subprocess.run([sys.executable, tmp], capture_output=True, text=True, timeout=15)
        return {"success": result.returncode == 0, "stdout": result.stdout.strip(), "stderr": result.stderr.strip()}
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Timed out after 15 seconds"}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e)}
    finally:
        os.unlink(tmp)

def extract_runnable_blocks(text):
    blocks = re.findall(r"```python\\n(.*?)```", text, re.DOTALL)
    return [b for b in blocks if b.strip().startswith("# RUNNABLE")]

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...",
        help="Get yours free at console.anthropic.com")
    if not api_key:
        st.warning("Add your API key above to start chatting")
        st.markdown("[Get a free API key →](https://console.anthropic.com)")
    st.markdown("---")
    st.markdown("### 🎯 Project Mode")
    mode = st.selectbox("What are you building?", [
        "💡 LED / Lighting Project",
        "🤖 Arduino / Microcontroller",
        "🐍 Python Script",
        "📊 Data Logger / Dashboard",
        "🏗️ 3D Print + Electronics",
        "🔌 General Wiring Help",
    ])
    st.markdown("---")
    auto_run = st.checkbox("Auto-test Python code", value=True,
        help="Runs Python scripts that don\'t need hardware and shows you the output")
    st.markdown("---")
    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
    st.markdown("---")
    st.caption("ELLIOT v0.1 MVP")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🔧 ELLIOT</h1>
    <p>Your AI workbench partner — describe what you\'re building, get working code + wiring in plain English</p>
</div>
""", unsafe_allow_html=True)

mode_hints = {
    "💡 LED / Lighting Project": "e.g. \'I have 30 WS2812B LEDs on an Arduino Nano pin 6. Make a breathing blue effect.\'",
    "🤖 Arduino / Microcontroller": "e.g. \'Read a DHT22 sensor every 5 seconds and show temp on a small screen.\'",
    "🐍 Python Script": "e.g. \'Read serial data from my Arduino and save to a CSV file with timestamps.\'",
    "📊 Data Logger / Dashboard": "e.g. \'Build a live dashboard showing temperature readings from my Arduino.\'",
    "🏗️ 3D Print + Electronics": "e.g. \'I have a 200mm box. Help me plan LED strip placement and wiring inside.\'",
    "🔌 General Wiring Help": "e.g. \'How do I safely power 3 servo motors from an Arduino Uno?\'",
}
st.info(f"**{mode}** — {mode_hints.get(mode, \'\')}")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f\'<div class="user-bubble">👤 <strong>You:</strong> {msg["content"]}</div>\', unsafe_allow_html=True)
    else:
        st.markdown(\'<div class="assistant-label">🔧 ELLIOT:</div>\', unsafe_allow_html=True)
        st.markdown(msg["content"])
        if "run_results" in msg:
            for r in msg["run_results"]:
                if r["success"]:
                    out = r["stdout"] or "(ran with no output)"
                    st.markdown(f\'<div class="run-success">✅ <strong>Code tested — it works:</strong><br><pre>{out}</pre></div>\', unsafe_allow_html=True)
                else:
                    st.markdown(f\'<div class="run-error">⚠️ <strong>Code issue found:</strong><br><pre>{r["stderr"]}</pre></div>\', unsafe_allow_html=True)

st.markdown("---")

# Quick start buttons
st.markdown("**⚡ Quick starts — click to try:**")
c1, c2, c3, c4 = st.columns(4)
quick = {
    "🌈 Rainbow LEDs": "I have a strip of 30 WS2812B LEDs wired to pin 6 on an Arduino Nano. Write me code for a smooth rainbow cycle effect. Explain every single line so I understand what it does.",
    "🌡️ Temp Sensor": "Help me wire a DHT22 temperature and humidity sensor to an Arduino Uno and write the code to read it. Explain what the numbers mean and what\'s a normal reading.",
    "📋 Serial Logger": "Write a Python script that reads data lines from my Arduino over USB and saves them to a CSV file with timestamps. I want to be able to stop it by closing the window.",
    "🔆 Breathing Effect": "How do I make a WS2812B LED strip slowly fade from off to full brightness and back in a loop — like a breathing effect? Using an Arduino Nano.",
}
triggered = None
for col, (label, prompt) in zip([c1, c2, c3, c4], quick.items()):
    with col:
        if st.button(label, use_container_width=True):
            triggered = prompt

user_input = st.text_area(
    "Your question:",
    height=100,
    placeholder="Describe your project in plain English — what you have, what you want it to do...",
    label_visibility="collapsed"
)
send = st.button("⚡ Ask ELLIOT", type="primary")

final_input = triggered or (user_input.strip() if send else None)

if final_input:
    if not api_key:
        st.error("⚠️ Add your Anthropic API key in the sidebar first. It\'s free at console.anthropic.com")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": final_input})
    api_messages = []
    for i, msg in enumerate(st.session_state.messages):
        content = msg["content"]
        if i == len(st.session_state.messages) - 1:
            content = f"[Project Mode: {mode}]\\n\\n{content}"
        api_messages.append({"role": msg["role"], "content": content})

    with st.spinner("🔧 ELLIOT is thinking..."):
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                messages=api_messages
            )
            reply = response.content[0].text
            run_results = []
            if auto_run:
                for code in extract_runnable_blocks(reply):
                    run_results.append(run_python_code(code))
            entry = {"role": "assistant", "content": reply}
            if run_results:
                entry["run_results"] = run_results
            st.session_state.messages.append(entry)
            st.rerun()
        except anthropic.AuthenticationError:
            st.session_state.messages.pop()
            st.error("❌ That API key didn\'t work. Double-check it at console.anthropic.com")
        except Exception as e:
            st.session_state.messages.pop()
            st.error(f"❌ Something went wrong: {e}")

if not st.session_state.messages:
    st.markdown("""
    <div style="text-align:center; color:#4b5563; padding:48px 0">
        <div style="font-size:3.5rem">🔧</div>
        <div style="font-size:1.1rem; color:#6b7280; margin-top:12px">Describe what you\'re building above</div>
        <div style="font-size:0.85rem; color:#374151; margin-top:6px">Plain English in — working code + wiring out. No coding knowledge needed.</div>
    </div>
    """, unsafe_allow_html=True)
'''

    with open(app_path, "w", encoding="utf-8") as f:
        f.write(app_code)

    # Step 4: Open browser after a short delay
    def open_browser():
        time.sleep(3.5)
        webbrowser.open("http://localhost:8501")

    threading.Thread(target=open_browser, daemon=True).start()

    # Step 5: Close the launch window and start Streamlit
    window.set_status("Opening ELLIOT in your browser...")
    time.sleep(0.5)
    window.close()

    # Run Streamlit — this blocks until the user closes it
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", app_path,
         "--server.headless", "true",
         "--server.port", "8501",
         "--browser.gatherUsageStats", "false"],
        cwd=launcher_dir
    )


if __name__ == "__main__":
    main()
