import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
import subprocess
import sys
import os
import platform
import threading
# import json # Not used directly in this version
from pathlib import Path
import shutil # Needed for brew check

class UlaiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 Ulai Meet AI")
        self.root.geometry("750x700")
        self.root.resizable(False, False)

        # Detect OS
        self.is_macos = platform.system() == "Darwin"
        self.is_windows = platform.system() == "Windows"

        # Check if already installed
        self.is_installed = self.check_installation()

        # Apply styling
        style = ttk.Style()
        style.theme_use('clam')

        # Show appropriate screen
        if self.is_installed:
            self.show_launcher_screen()
        else:
            self.show_setup_screen()

    def check_installation(self):
        """Check if the project is already set up"""
        # Assume current working directory is the project directory
        project_dir = Path.cwd()
        venv_exists = (project_dir / ".venv").exists()
        env_exists = (project_dir / ".env").exists()
        core_exists = (project_dir / "core").exists() and (project_dir / "core" / "meet_main.py").exists()

        deps_installed = False
        if venv_exists:
            if self.is_macos:
                pip_path = project_dir / ".venv" / "bin" / "pip"
            else:
                pip_path = project_dir / ".venv" / "Scripts" / "pip.exe"

            if pip_path.exists():
                try:
                    result = subprocess.run(
                        [str(pip_path), "show", "playwright"], # Check a key dependency
                        capture_output=True, text=True, check=False, timeout=5
                    )
                    deps_installed = result.returncode == 0
                except Exception as e:
                    print(f"Warning: Could not check dependencies: {e}")
                    deps_installed = False # Assume not installed if check fails

        fully_installed = venv_exists and env_exists and core_exists and deps_installed

        if not fully_installed and (venv_exists or env_exists or core_exists):
            self.show_partial_installation_warning()

        return fully_installed

    def show_partial_installation_warning(self):
        """Show warning for partial installation"""
        response = messagebox.askyesno(
            "Partial Installation Detected",
            "It looks like a previous installation was incomplete.\n\n"
            "Would you like to:\n"
            "• YES - Clean and Reinstall (Recommended)\n"
            "• NO - Try to use existing setup (May fail)\n\n"
            "Reinstalling is safer."
        )
        if response:
            # User wants to reinstall - clean first
            # We need project_path to be set; assume current dir if not setup yet
            if not hasattr(self, 'project_path'):
                self.project_path = tk.StringVar(value=os.getcwd())
            self.clean_installation()
            # The flow will then naturally proceed to show_setup_screen

    # ============================================================
    # SETUP SCREEN (First-time installation)
    # ============================================================

    def show_setup_screen(self):
        """Show the initial setup screen"""
        self.clear_window()

        # Header
        header = tk.Frame(self.root, bg="#2c3e50", height=80)
        header.pack(fill=tk.X)

        os_emoji = "🍎" if self.is_macos else "🪟"

        title = tk.Label(
            header,
            text=f"🤖 Ulai Meet AI - First Time Setup {os_emoji}",
            font=("Arial", 20, "bold"),
            bg="#2c3e50",
            fg="white"
        )
        title.pack(pady=20)

        # Main container
        main = tk.Frame(self.root, bg="white", padx=20, pady=20)
        main.pack(fill=tk.BOTH, expand=True)

        # Welcome message
        welcome = tk.Label(
            main,
            text="Welcome! Let's set up your AI bot in a few steps:",
            font=("Arial", 13),
            bg="white",
            fg="#2c3e50"
        )
        welcome.pack(pady=10)

        # Step 1: Select project folder
        self.create_section(main, "📁 Step 1: Select Project Folder", 0)

        folder_frame = tk.Frame(main, bg="white")
        folder_frame.pack(fill=tk.X, padx=20, pady=10)

        self.project_path = tk.StringVar(value=os.getcwd())
        tk.Entry(folder_frame, textvariable=self.project_path, width=50, state='readonly').pack(side=tk.LEFT, padx=5)
        tk.Button(
            folder_frame,
            text="📂 Browse",
            command=self.select_folder,
            bg="#3498db",
            fg="white",
            cursor="hand2"
        ).pack(side=tk.LEFT)

        # Step 2: API Keys
        self.create_section(main, "🔑 Step 2: Enter API Keys", 1)

        keys_frame = tk.Frame(main, bg="white")
        keys_frame.pack(fill=tk.X, padx=20, pady=5)

        tk.Label(keys_frame, text="Gemini API Key:", bg="white", width=18, anchor='w').grid(row=0, column=0, pady=5)
        self.gemini_key = tk.Entry(keys_frame, width=45, show="*")
        self.gemini_key.grid(row=0, column=1, pady=5, padx=5)

        tk.Label(keys_frame, text="Deepgram API Key:", bg="white", width=18, anchor='w').grid(row=1, column=0, pady=5)
        self.deepgram_key = tk.Entry(keys_frame, width=45, show="*")
        self.deepgram_key.grid(row=1, column=1, pady=5, padx=5)

        help_btn = tk.Button(
            keys_frame,
            text="❓ How to get keys?",
            command=self.show_api_help,
            bg="#3498db",
            fg="white",
            relief=tk.FLAT,
            cursor="hand2"
        )
        help_btn.grid(row=2, column=1, sticky="w", pady=5)

        # Step 3: Audio driver
        self.create_section(main, "🔊 Step 3: Audio Setup (Optional but Recommended)", 2)

        audio_driver = "BlackHole (via Homebrew)" if self.is_macos else "VB-Cable (Manual Download)"
        self.install_audio = tk.BooleanVar(value=True)

        tk.Checkbutton(
            main,
            text=f"Attempt to install {audio_driver}",
            variable=self.install_audio,
            bg="white",
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=40, pady=5)

        # Progress section
        self.create_section(main, "📊 Installation Progress", 3)

        self.progress = ttk.Progressbar(main, length=650, mode='indeterminate')
        self.progress.pack(pady=10)

        self.log = scrolledtext.ScrolledText(main, height=8, width=80, state='disabled', font=("Courier", 9))
        self.log.pack(pady=10)

        # Install button (Ensure it's created and packed correctly)
        self.install_btn = tk.Button(
            main, # Make sure parent is 'main'
            text="🚀 Install Everything",
            command=self.start_installation,
            bg="#27ae60",
            fg="white",
            font=("Arial", 16, "bold"),
            width=25,
            height=2,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.install_btn.pack(pady=20) # Pack it into the main frame

        # --- THE FIX ---
        # Force Tkinter to update the display NOW to ensure the button is drawn
        self.root.update_idletasks()
        # --- END FIX ---

    # ============================================================
    # LAUNCHER SCREEN
    # ============================================================

    def show_launcher_screen(self):
         """Show the main launcher screen"""
         self.clear_window()

         # Header
         header = tk.Frame(self.root, bg="#27ae60", height=100)
         header.pack(fill=tk.X)

         title = tk.Label(
             header,
             text="🤖 Ulai Meet AI Bot",
             font=("Arial", 26, "bold"),
             bg="#27ae60",
             fg="white"
         )
         title.pack(pady=30)

         # Main container
         main = tk.Frame(self.root, bg="white", padx=30, pady=20)
         main.pack(fill=tk.BOTH, expand=True)

         # Instructions
         tk.Label(
             main,
             text="Enter your meeting details to start the AI bot:",
             font=("Arial", 13),
             bg="white",
             fg="#2c3e50"
         ).pack(pady=15)

         # Input fields
         fields = tk.Frame(main, bg="white")
         fields.pack(fill=tk.X, pady=10)

         # Meet URL
         tk.Label(fields, text="Google Meet URL:", bg="white", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=8)
         self.meet_url = tk.Entry(fields, width=55, font=("Arial", 10))
         self.meet_url.grid(row=0, column=1, pady=8, padx=10)
         self.meet_url.insert(0, "https://meet.google.com/")

         # Website to demo
         tk.Label(fields, text="Website to Demo:", bg="white", font=("Arial", 11, "bold")).grid(row=1, column=0, sticky="w", pady=8)
         self.demo_url = tk.Entry(fields, width=55, font=("Arial", 10))
         self.demo_url.grid(row=1, column=1, pady=8, padx=10)
         self.demo_url.insert(0, "https://")

         # Credentials
         tk.Label(fields, text="Login Email:", bg="white", font=("Arial", 11, "bold")).grid(row=2, column=0, sticky="w", pady=8)
         self.demo_email = tk.Entry(fields, width=55, font=("Arial", 10))
         self.demo_email.grid(row=2, column=1, pady=8, padx=10)

         tk.Label(fields, text="Password:", bg="white", font=("Arial", 11, "bold")).grid(row=3, column=0, sticky="w", pady=8)
         self.demo_password = tk.Entry(fields, width=55, font=("Arial", 10), show="●")
         self.demo_password.grid(row=3, column=1, pady=8, padx=10)

         # Status log
         tk.Label(main, text="📊 Bot Status:", bg="white", font=("Arial", 11, "bold")).pack(anchor="w", pady=(20, 5))
         self.status_log = scrolledtext.ScrolledText(main, height=6, width=80, state='disabled', font=("Courier", 9))
         self.status_log.pack(pady=5)

         # Buttons frame
         btn_frame = tk.Frame(main, bg="white")
         btn_frame.pack(pady=25)

         # Launch button
         self.launch_btn = tk.Button(
             btn_frame,
             text="🎬 Launch Bot",
             command=self.launch_bot,
             bg="#27ae60",
             fg="white",
             font=("Arial", 16, "bold"),
             width=20,
             height=2,
             relief=tk.FLAT,
             cursor="hand2"
         )
         self.launch_btn.grid(row=0, column=0, padx=10)

         # Settings button
         tk.Button(
             btn_frame,
             text="⚙ Settings",
             command=self.show_settings,
             bg="#3498db",
             fg="white",
             font=("Arial", 14),
             width=15,
             height=2,
             relief=tk.FLAT,
             cursor="hand2"
         ).grid(row=0, column=1, padx=10)

         # Reinstall button
         tk.Button(
             btn_frame,
             text="🔄 Reinstall",
             command=self.reinstall_prompt,
             bg="#e67e22",
             fg="white",
             font=("Arial", 14),
             width=15,
             height=2,
             relief=tk.FLAT,
             cursor="hand2"
         ).grid(row=0, column=2, padx=10)

    # ============================================================
    # INSTALLATION LOGIC (UPDATED METHODS)
    # ============================================================

    def start_installation(self):
        """Start the installation process"""
        if not self.gemini_key.get().strip():
            messagebox.showerror("Error", "Gemini API Key is required!")
            return

        if not self.deepgram_key.get().strip():
            messagebox.showerror("Error", "Deepgram API Key is required!")
            return

        confirm = messagebox.askyesno(
            "Start Installation?",
            "This will setup the project environment and install dependencies (approx. 2-3 minutes).\nContinue?"
        )
        if not confirm: return

        self.install_btn.config(state='disabled', text="Installing...", bg="#95a5a6")
        self.progress.start()

        thread = threading.Thread(target=self.install_process)
        thread.daemon = True
        thread.start()

    def run_command(self, command):
        """Run shell command and stream output/errors to log in real-time"""
        self.log_message(f"$ {command}") # Log the command being run
        stderr_output = []
        try:
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, # Capture stderr separately
                text=True,
                bufsize=1,
                encoding='utf-8', # Explicitly set encoding
                errors='replace'   # Handle potential decoding errors
            )

            # Thread to read stderr without blocking stdout
            def read_stderr():
                for err_line in process.stderr:
                    err_line = err_line.strip()
                    if err_line:
                        # Schedule logging stderr on the main thread
                        self.root.after(0, lambda line=err_line: self.log_message(f"⚠️ STDERR: {line}"))
                        stderr_output.append(err_line)

            stderr_thread = threading.Thread(target=read_stderr)
            stderr_thread.daemon = True
            stderr_thread.start()

            # Stream stdout
            for line in process.stdout:
                # Schedule logging stdout on the main thread
                self.root.after(0, lambda l=line.strip(): self.log_message(l))

            process.wait() # Wait for process to complete
            stderr_thread.join() # Wait for stderr reader to finish

            return process.returncode == 0, "\n".join(stderr_output) # Return success and captured stderr

        except Exception as e:
            error_msg = f"❌ Command execution failed: {str(e)}"
            # Schedule logging the exception on the main thread
            self.root.after(0, lambda msg=error_msg: self.log_message(msg))
            return False, error_msg

    def install_process(self):
        """Main installation logic with live logs and improved robustness"""
        try:
            project_dir = self.project_path.get()
            os.chdir(project_dir)

            python_cmd = "python3" if self.is_macos else "python"

            # Step 1: Check Python
            self.log_message("--- 🐍 Checking Python ---")
            success, stderr = self.run_command(f"{python_cmd} --version")
            if not success:
                self.log_message(f"❌ Python not found or command failed!\n{stderr}")
                self.installation_failed()
                return

            # Step 2: Create virtual environment
            self.log_message("\n--- 🔧 Creating Virtual Environment ---")
            venv_path = ".venv"
            if not os.path.exists(venv_path):
                success, stderr = self.run_command(f"{python_cmd} -m venv {venv_path}")
                if not success:
                    self.log_message(f"❌ Failed to create virtual environment.\n{stderr}")
                    self.installation_failed()
                    return
            self.log_message("✅ Virtual environment ready.")

            # Define venv paths
            venv_path_abs = Path(project_dir) / venv_path # Use absolute paths
            if self.is_macos:
                pip_cmd = venv_path_abs / "bin" / "pip"
                playwright_cmd = venv_path_abs / "bin" / "playwright"
                python_venv_cmd = venv_path_abs / "bin" / python_cmd
            else: # Windows
                pip_cmd = venv_path_abs / "Scripts" / "pip.exe"
                playwright_cmd = venv_path_abs / "Scripts" / "playwright.exe"
                python_venv_cmd = venv_path_abs / "Scripts" / (python_cmd + ".exe")

            # Escape paths with spaces for shell commands
            pip_cmd_str = f'"{pip_cmd}"'
            playwright_cmd_str = f'"{playwright_cmd}"'
            python_venv_cmd_str = f'"{python_venv_cmd}"'


            # Step 3: Upgrade pip
            self.log_message("\n--- ⬆️ Upgrading pip ---")
            success, stderr = self.run_command(f'{python_venv_cmd_str} -m pip install --upgrade pip')
            if not success:
                 self.log_message(f"⚠️ Pip upgrade potentially failed, continuing...\n{stderr}")


            # Step 4: Install dependencies (all at once)
            self.log_message("\n--- 📦 Installing Dependencies (this takes a few minutes) ---")
            deps = [
                "playwright", "python-dotenv", "google-generativeai",
                "deepgram-sdk", "sounddevice", "soundfile", "gtts",
                "websockets", "notion-client", "Pillow"
            ]
            install_command = f'{pip_cmd_str} install {" ".join(deps)}'
            success, stderr = self.run_command(install_command)
            if not success:
                self.log_message(f"❌ Failed to install dependencies.\n{stderr}")
                self.installation_failed()
                return
            self.log_message("✅ Dependencies installed.")

            # Step 5: Install Playwright browsers
            self.log_message("\n--- 🌐 Installing Playwright Chromium ---")
            success, stderr = self.run_command(f'{playwright_cmd_str} install chromium')
            if not success:
                self.log_message(f"⚠️ Chromium installation potentially failed, check logs.\n{stderr}")
            else:
                 self.log_message("✅ Chromium installed.")

            # Step 6: Audio driver (Improved logic)
            if self.install_audio.get():
                self.log_message("\n--- 🔊 Setting up Virtual Audio Driver ---")
                if self.is_macos:
                    self.log_message("   Checking for Homebrew...")
                    if not self.check_brew():
                        self.log_message("   ❌ Homebrew not found. Please install it ('/bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"')")
                        self.log_message("   Skipping BlackHole installation.")
                    else:
                        self.log_message("   Attempting to install BlackHole via Homebrew...")
                        success, stderr = self.run_command("brew install blackhole-2ch")
                        if success:
                            self.log_message("   ✅ BlackHole installed (requires configuration in Audio MIDI Setup).")
                        else:
                            self.log_message(f"   ⚠️ BlackHole installation failed (maybe already installed?). Check manually.\n{stderr}")
                            self.log_message("   Manual install: https://existential.audio/blackhole/")
                else: # Windows
                    self.log_message("   ℹ️ For audio routing on Windows, VB-Cable is recommended.")
                    self.log_message("   Please download and install it manually from:")
                    self.log_message("   ➡️ https://vb-audio.com/Cable/")
                    self.log_message("   After installation, ensure 'CABLE Input' is your default recording device and 'CABLE Output' is used by the bot.")

            # Step 7: Save configuration
            self.log_message("\n--- 🔐 Saving Configuration ---")
            self.create_env_file()
            self.log_message("✅ Configuration saved to .env file.")

            # Step 8: Create project structure
            self.log_message("\n--- 🏗️ Setting Up Project Files ---")
            self.create_project_structure()
            self.log_message("✅ Project structure ready.")

            # Installation complete
            self.log_message("\n" + "="*60)
            self.log_message("🎉 Installation Complete!")
            self.log_message("   You can now launch the bot from the main screen.")
            self.log_message("="*60)
            self.installation_complete()

        except Exception as e:
            self.log_message(f"\n❌ An unexpected error occurred during installation: {str(e)}")
            self.installation_failed()

    def check_brew(self):
        """Check if Homebrew is installed on macOS"""
        if not self.is_macos: return False
        return shutil.which("brew") is not None

    def reinstall_prompt(self):
         """Prompt user before reinstalling."""
         confirm = messagebox.askyesno(
              "Confirm Reinstall",
              "This will delete the current setup (venv, .env, core files) and start the installation fresh.\n\nAre you sure you want to proceed?"
         )
         if confirm:
              self.clean_installation() # Clean first
              self.show_setup_screen() # Then show setup screen

    def clean_installation(self):
         """Delete existing venv, .env, and core for a clean reinstall."""
         print("🧹 Cleaning previous installation...")
         project_root = Path(self.project_path.get()) if hasattr(self, 'project_path') else Path.cwd()
         paths_to_remove = [".venv", ".env", "core"]
         for path_name in paths_to_remove:
              full_path = project_root / path_name
              try:
                   if full_path.is_dir():
                        shutil.rmtree(full_path)
                        print(f"   🗑️ Removed directory: {full_path}")
                   elif full_path.is_file():
                        os.remove(full_path)
                        print(f"   🗑️ Removed file: {full_path}")
              except Exception as e:
                   print(f"   ⚠️ Error removing {path_name}: {e}")
         print("✅ Cleaning complete.")
         self.is_installed = False # Reset installed state

    # ============================================================
    # HELPER METHODS
    # ============================================================

    def clear_window(self):
        """Clear all widgets from window"""
        for widget in self.root.winfo_children():
            widget.destroy()

    def create_section(self, parent, title, row):
        """Create a section header"""
        frame = tk.Frame(parent, bg="white")
        frame.pack(fill=tk.X, pady=(15, 5))
        label = tk.Label(frame, text=title, font=("Arial", 12, "bold"), bg="white", fg="#2c3e50")
        label.pack(anchor="w")
        ttk.Separator(frame, orient='horizontal').pack(fill=tk.X, pady=(5, 0))

    def select_folder(self):
        """Select project folder"""
        folder = filedialog.askdirectory(initialdir=os.getcwd(), title="Select Project Folder")
        if folder:
            self.project_path.set(folder)

    def show_api_help(self):
        """Show API key help"""
        help_text = """🔑 How to Get API Keys:

1. Gemini API (Required):
   • Visit: https://aistudio.google.com/app/apikey
   • Sign in -> Create API Key -> Copy

2. Deepgram API (Required):
   • Visit: https://console.deepgram.com/signup
   • Sign up -> API Keys -> Create & Copy"""
        messagebox.showinfo("API Keys Help", help_text)

    def show_settings(self):
        """Show settings dialog"""
        settings_win = tk.Toplevel(self.root)
        settings_win.title("⚙ Settings")
        settings_win.geometry("500x300")
        settings_win.resizable(False, False)
        settings_win.transient(self.root) # Keep on top of main window
        settings_win.grab_set() # Modal behavior

        tk.Label(settings_win, text="⚙ Settings", font=("Arial", 18, "bold")).pack(pady=20)

        tk.Label(settings_win, text="API Keys (Stored in .env file):", font=("Arial", 12, "bold")).pack(anchor="w", padx=20, pady=(10, 5))

        try:
            # Determine project path correctly
            project_root = Path(self.project_path.get()) if hasattr(self, 'project_path') and self.project_path.get() else Path.cwd()
            env_path = project_root / ".env"

            if env_path.exists():
                with open(env_path) as f:
                    env_content = f.read()
                keys_found = False
                for line in env_content.splitlines(): # Use splitlines for reliability
                    line = line.strip()
                    if "API_KEY" in line and "=" in line:
                        parts = line.split("=", 1)
                        key_name = parts[0].strip()
                        key_val = parts[1].strip()
                        # Mask the key better
                        masked_key = key_val[:4] + "●" * (len(key_val) - 8) + key_val[-4:] if len(key_val) > 8 else "●" * len(key_val)
                        tk.Label(settings_win, text=f"{key_name}: {masked_key}", font=("Courier", 10)).pack(anchor="w", padx=40)
                        keys_found = True
                if not keys_found:
                     tk.Label(settings_win, text="No API keys found in .env.", font=("Arial", 10)).pack(anchor="w", padx=40)
            else:
                 tk.Label(settings_win, text=".env file not found.", font=("Arial", 10)).pack(anchor="w", padx=40)
        except Exception as e:
            tk.Label(settings_win, text=f"Error reading .env: {e}", font=("Arial", 10, "italic")).pack(anchor="w", padx=40)

        tk.Button(
            settings_win,
            text="🔄 Edit Keys / Reinstall",
            command=lambda: [settings_win.destroy(), self.reinstall_prompt()],
            bg="#3498db", fg="white"
        ).pack(pady=20)

        tk.Button(settings_win, text="Close", command=settings_win.destroy).pack()


    def log_message(self, message):
        """Log message to console safely from any thread"""
        def update_log():
            # Check if the log widget exists and hasn't been destroyed
            if hasattr(self, 'log') and self.log and self.log.winfo_exists():
                 try:
                      current_state = self.log.cget('state')
                      self.log.config(state='normal')
                      self.log.insert(tk.END, message + "\n")
                      self.log.see(tk.END) # Scroll to the end
                      self.log.config(state=current_state) # Restore previous state
                 except tk.TclError:
                      # Widget might be destroyed between check and config
                      print(message) # Fallback if error occurs
            else:
                 print(message) # Fallback to console

        # Schedule the UI update on the main thread if the root window exists
        if self.root and self.root.winfo_exists():
             self.root.after(0, update_log)
        else:
             print(message) # Fallback if root window is gone


    def installation_complete(self):
        """Handle installation success"""
        def update_ui():
            if hasattr(self, 'progress') and self.progress.winfo_exists(): self.progress.stop()
            if hasattr(self, 'install_btn') and self.install_btn.winfo_exists():
                 self.install_btn.config(state='normal', text="✅ Complete! Restart App", bg="#27ae60")
            messagebox.showinfo(
                 "Success!",
                 "Installation complete!\n\nPlease restart the application to launch the bot."
            )
            # Don't switch automatically, force restart to ensure env vars load etc.
            # self.is_installed = True
            # self.show_launcher_screen()
        if self.root and self.root.winfo_exists():
             self.root.after(0, update_ui)

    def installation_failed(self):
        """Handle installation failure"""
        def update_ui():
            if hasattr(self, 'progress') and self.progress.winfo_exists(): self.progress.stop()
            if hasattr(self, 'install_btn') and self.install_btn.winfo_exists():
                 self.install_btn.config(state='normal', text="❌ Failed. Check Logs & Retry.", bg="#e74c3c")
            messagebox.showerror(
                "Installation Failed",
                "Something went wrong. Please check the logs in the window for details.\n\n"
                "Common issues:\n"
                "- Internet connection problem\n"
                "- Python/pip not configured correctly\n"
                "- Permissions issues\n\n"
                "Try running the installation again."
            )
        if self.root and self.root.winfo_exists():
             self.root.after(0, update_ui)

    # ============================================================
    # CODE GENERATION
    # ============================================================

    def get_meet_main_code(self):
        """Return the core/meet_main.py code"""
        # --- IMPORTANT: PASTE YOUR ACTUAL meet_main.py / meet_bot.py CODE HERE ---
        # --- This placeholder will NOT work ---
        return '''# Placeholder for core/meet_main.py
# !!! REPLACE THIS WITH YOUR ACTUAL meet_bot.py CODE !!!
import os, sys, argparse, asyncio, time, logging
from dotenv import load_dotenv

# Example structure - adapt to your meet_bot.py
# from core.meet_bot import run_meet_agent

if __name__ == "__main__":
    load_dotenv() # Load .env file created by the installer
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser()
    parser.add_argument("--meet-url", required=True)
    parser.add_argument("--headful", action="store_true")
    args = parser.parse_args()
    
    # Get credentials from environment (set by launcher)
    demo_url = os.getenv("DEMO_URL")
    demo_email = os.getenv("DEMO_EMAIL")
    demo_password = os.getenv("DEMO_PASSWORD")
    
    if not all([demo_url, demo_email, demo_password]):
        logging.error("❌ ERROR: Missing DEMO_URL, DEMO_EMAIL, or DEMO_PASSWORD environment variables.")
        sys.exit(1)
    
    logging.info(f"✅ Launching Ulai Meet Bot...")
    logging.info(f"   Meeting: {args.meet_url}")
    logging.info(f"   Demo Site: {demo_url}")
    logging.info(f"   User: {demo_email}")
    logging.info(f"   Headful: {args.headful}")
    
    try:
        # Replace this with the actual entry point call to your bot logic
        logging.info("\\n--- BOT EXECUTION STARTS HERE (Using placeholder logic) ---")
        
        # Example using your previous structure (assuming run_meet_agent exists)
        # from core.meet_bot import run_meet_agent 
        # asyncio.run(run_meet_agent(args.meet_url, demo_url, (demo_email, demo_password), headful=args.headful))

        print("Simulating bot running for 15 seconds...")
        time.sleep(15) 
        
        logging.info("--- BOT EXECUTION FINISHED (Placeholder logic) ---")
        print("\\nBot simulation finished.")

    except ImportError:
         logging.error("❌ Error: Could not import core modules. Make sure installation was successful and core files exist.")
         print("❌ Error: Could not import core modules.")
    except Exception as e:
         logging.exception(f"❌ An error occurred during bot execution: {e}") # Log full traceback
         print(f"❌ An error occurred: {e}")
    finally:
        input("\\nPress Enter to close this window...") # Keep window open

'''

    def create_core_files(self):
        """Create placeholder or actual core files"""
        core_dir = Path("core")
        core_dir.mkdir(exist_ok=True)

        # --- IMPORTANT: EMBED YOUR ACTUAL CORE FILES HERE ---
        # For a truly standalone app, you'd paste the content of each required .py file.
        # This is a basic example creating placeholders.
        required_files = {
            "__init__.py": "", # Makes 'core' a package
            # "meet_main.py": self.get_meet_main_code(), # Generated separately
            "tts_handler.py": "# Placeholder for Text-to-Speech logic\nimport time\ndef speak_text_vbcable(text):\n    print(f'[TTS Placeholder] Speaking: {text}')\n    time.sleep(1)\n",
            "deepgram_stt.py": "# Placeholder for Deepgram STT subprocess\nimport time\nprint('[STT Placeholder] STT Process Started')\ntry:\n    while True: time.sleep(1)\nexcept KeyboardInterrupt: print('[STT Placeholder] STT Process Stopped')",
            "login_demo.py": "# Placeholder for login automation logic\ndef autonomous_web_flow(*args, **kwargs):\n    print('[Login Demo Placeholder] Running web flow...')\n    return True\ndef autonomous_web_flow_with_narration(*args, **kwargs):\n    print('[Login Demo Placeholder] Running web flow with narration...')\n    return True",
            "qa_handler.py": "# Placeholder for Q&A logic using Gemini\nasync def ask_gemini_question(question, context):\n    print(f'[QA Placeholder] Answering: {question}')\n    return f'Placeholder answer about {context.splitlines()[0]}'",
            "utils.py": "# Placeholder for utility functions\nasync def safe_click(page, selectors, **kwargs):\n    print(f'[Utils Placeholder] Trying to click one of: {selectors}')\n    # Simulate finding and clicking the first selector\n    try: await page.locator(selectors[0]).first.click(timeout=1000)\n    except Exception: print('  -> Failed')\n    return True" ,
            "meet_bot.py": "# Placeholder for the main meet bot logic\n# Needs to contain the run_meet_agent async function\nasync def run_meet_agent(*args, **kwargs):\n    print('[Meet Bot Placeholder] Running meet agent...')\n    await asyncio.sleep(10)\n    print('[Meet Bot Placeholder] Finished.')"
        }

        for filename, content in required_files.items():
            file_path = core_dir / filename
            if not file_path.exists():
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)
                    self.log_message(f"   ✅ Created placeholder: core/{filename}")

        # Specifically write meet_main.py
        meet_main_path = core_dir / "meet_main.py"
        with open(meet_main_path, "w", encoding="utf-8") as f:
             f.write(self.get_meet_main_code())
             self.log_message(f"   ✅ Created core/meet_main.py")


    def create_env_file(self):
        """Create .env file"""
        env_content = f"""# Ulai Meet AI Configuration
GEMINI_API_KEY={self.gemini_key.get().strip()}
DEEPGRAM_API_KEY={self.deepgram_key.get().strip()}

# Add any other environment variables your bot needs here
# e.g., AUTO_LOGIN_USERNAME=your_demo_username
# e.g., AUTO_LOGIN_PASSWORD=your_demo_password
"""
        # Determine project path correctly
        project_root = Path(self.project_path.get()) if hasattr(self, 'project_path') and self.project_path.get() else Path.cwd()
        env_path = project_root / ".env"
        with open(env_path, "w") as f:
            f.write(env_content)

    # ============================================================
    # LAUNCH LOGIC
    # ============================================================

    def launch_bot(self):
        """Launch the bot in a separate process"""
        meet_url = self.meet_url.get().strip()
        demo_url = self.demo_url.get().strip()
        email = self.demo_email.get().strip()
        password = self.demo_password.get().strip()

        if not all([meet_url, demo_url, email, password]):
            messagebox.showerror("Error", "All fields are required!"); return
        if "meet.google.com" not in meet_url:
            messagebox.showerror("Error", "Invalid Google Meet URL!"); return

        confirm = messagebox.askyesno("Launch Bot?", f"Ready to launch?\n\nMeet: {meet_url}\nDemo: {demo_url}\nUser: {email}\n")
        if not confirm: return

        try:
            # Determine project path correctly
            project_root = Path(self.project_path.get()) if hasattr(self, 'project_path') and self.project_path.get() else Path.cwd()
            venv_path = project_root / ".venv"

            if self.is_macos:
                python_executable = venv_path / "bin" / "python3"
            else:
                python_executable = venv_path / "Scripts" / "python.exe"

            if not python_executable.exists():
                 messagebox.showerror("Error", f"Python executable not found in .venv!\nExpected at: {python_executable}\n\nTry reinstalling.")
                 return

            # Prepare environment variables specifically for the subprocess
            bot_env = os.environ.copy()
            bot_env["DEMO_URL"] = demo_url
            bot_env["DEMO_EMAIL"] = email
            bot_env["DEMO_PASSWORD"] = password
            # Ensure API keys from .env are available if meet_main needs them directly
            # (although it's better if meet_main reads .env itself using dotenv)
            bot_env["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY", "") # Pass from current env if set
            bot_env["DEEPGRAM_API_KEY"] = os.getenv("DEEPGRAM_API_KEY", "")

            bot_script = project_root / "core" / "meet_main.py"
            bot_cmd = [str(python_executable), str(bot_script), "--meet-url", meet_url, "--headful"]

            self.status_log.config(state='normal')
            self.status_log.delete(1.0, tk.END)
            self.status_log.insert(tk.END, f"🚀 Launching bot...\n📍 Meet: {meet_url}\n🌐 Demo: {demo_url}\n✅ Bot starting in a new window...\n")
            self.status_log.config(state='disabled')

            # Launch bot in a new console window
            if self.is_windows:
                 subprocess.Popen(bot_cmd, env=bot_env, creationflags=subprocess.CREATE_NEW_CONSOLE, cwd=project_root)
            elif self.is_macos:
                 # More robust osascript command
                 cmd_str = " ".join(f'\\"{arg}\\"' for arg in bot_cmd) # Escape args for shell
                 env_exports = "; ".join([f"export {k}='{v}'" for k, v in bot_env.items() if k.startswith("DEMO_") or k.endswith("API_KEY")])
                 full_osascript_cmd = f'''osascript -e 'tell application "Terminal" to do script "{env_exports}; cd \\"{project_root}\\"; {cmd_str}"' '''
                 subprocess.Popen(full_osascript_cmd, shell=True, cwd=project_root)
            else: # Linux/Other
                 subprocess.Popen(bot_cmd, env=bot_env, start_new_session=True, cwd=project_root)

            messagebox.showinfo("Bot Launched!", "The bot should be starting in a new window/terminal.\n\nYou can monitor its progress there.")
            # Optionally close the launcher window after successful launch
            # self.root.destroy()

        except Exception as e:
            messagebox.showerror("Launch Error", f"Failed to launch bot:\n{str(e)}")


# ============================================================
# MAIN
# ============================================================

def main():
    root = tk.Tk()
    app = UlaiApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()