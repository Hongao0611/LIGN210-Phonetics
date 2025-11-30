import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sounddevice as sd
import soundfile as sf
import threading
import os
import json
import numpy as np
from datetime import datetime

class AudioRecorderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Audio Recorder")
        self.root.geometry("500x450")
        
        # Recording state variables
        self.is_recording = False
        self.audio_data = None
        self.sample_rate = 44100
        
        # Preset names list
        self.preset_names = []
        self.load_preset_names()
        
        # Setup audio devices
        self.setup_audio_devices()
        
        # Create GUI
        self.create_widgets()
        
    def setup_audio_devices(self):
        """Setup audio devices"""
        try:
            # Get available devices
            devices = sd.query_devices()
            input_devices = []
            
            for i, device in enumerate(devices):
                if device['max_input_channels'] > 0:
                    input_devices.append((i, device['name']))
            
            self.input_devices = input_devices
            if input_devices:
                self.selected_device = input_devices[0][0]
                print(f"Using input device: {input_devices[0][1]}")
            else:
                messagebox.showerror("Error", "No audio input devices found")
                self.selected_device = None
                
        except Exception as e:
            messagebox.showerror("Error", f"Cannot query audio devices: {str(e)}")
            self.selected_device = None
    
    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Audio Recorder", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Device selection (if multiple devices)
        if len(self.input_devices) > 1:
            device_frame = ttk.LabelFrame(main_frame, text="Audio Device", padding="5")
            device_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
            
            self.device_var = tk.StringVar()
            device_names = [f"{name} (ID: {id})" for id, name in self.input_devices]
            device_combo = ttk.Combobox(device_frame, textvariable=self.device_var, values=device_names, state="readonly")
            device_combo.set(device_names[0])
            device_combo.grid(row=0, column=0, sticky=(tk.W, tk.E))
            device_combo.bind('<<ComboboxSelected>>', self.on_device_change)
            
            device_frame.columnconfigure(0, weight=1)
        
        # Recording filename input
        name_frame = ttk.LabelFrame(main_frame, text="Recording Filename", padding="10")
        name_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(name_frame, textvariable=self.name_var, width=50)
        name_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # Use current time as default filename
        default_name = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.name_var.set(default_name)
        
        name_frame.columnconfigure(0, weight=1)
        
        # Preset names list
        preset_frame = ttk.LabelFrame(main_frame, text="Preset Names", padding="10")
        preset_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # List and scrollbar
        list_frame = ttk.Frame(preset_frame)
        list_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.preset_listbox = tk.Listbox(list_frame, height=6)
        self.preset_listbox.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.preset_listbox.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.preset_listbox.configure(yscrollcommand=scrollbar.set)
        
        # Bind list selection event
        self.preset_listbox.bind('<<ListboxSelect>>', self.on_preset_select)
        
        # Update preset list display
        self.update_preset_list()
        
        # Preset names management buttons
        preset_btn_frame = ttk.Frame(preset_frame)
        preset_btn_frame.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        ttk.Button(preset_btn_frame, text="Add to List", command=self.add_to_preset).grid(row=0, column=0, padx=(0, 5))
        ttk.Button(preset_btn_frame, text="Remove from List", command=self.remove_from_preset).grid(row=0, column=1, padx=5)
        ttk.Button(preset_btn_frame, text="Clear List", command=self.clear_preset).grid(row=0, column=2, padx=(5, 0))
        
        preset_frame.columnconfigure(0, weight=1)
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Recording control
        control_frame = ttk.LabelFrame(main_frame, text="Recording Control", padding="10")
        control_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.record_btn = ttk.Button(control_frame, text="Start Recording", command=self.toggle_recording)
        self.record_btn.grid(row=0, column=0, padx=(0, 10))
        
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_label = ttk.Label(control_frame, textvariable=self.status_var)
        status_label.grid(row=0, column=1)
        
        control_frame.columnconfigure(1, weight=1)
        
        # Save path settings
        path_frame = ttk.LabelFrame(main_frame, text="Save Path", padding="10")
        path_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.path_var = tk.StringVar()
        self.path_var.set(os.path.expanduser("~/Recordings"))
        
        path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=40)
        path_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Button(path_frame, text="Browse", command=self.browse_path).grid(row=0, column=1, padx=(10, 0))
        
        # Ensure directory exists
        os.makedirs(self.path_var.get(), exist_ok=True)
        
        path_frame.columnconfigure(0, weight=1)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
    
    def on_device_change(self, event):
        """When device selection changes"""
        selection = event.widget.current()
        if 0 <= selection < len(self.input_devices):
            self.selected_device = self.input_devices[selection][0]
    
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
    
    def start_recording(self):
        # Check filename
        filename = self.name_var.get().strip()
        if not filename:
            messagebox.showerror("Error", "Please enter a filename")
            return
        
        # Check device
        if self.selected_device is None:
            messagebox.showerror("Error", "No audio device available")
            return
        
        # Start recording
        self.is_recording = True
        self.audio_data = None
        
        # Update UI
        self.record_btn.config(text="Stop Recording")
        self.status_var.set("Recording...")
        
        # Start recording in background thread
        self.recording_thread = threading.Thread(target=self.record_audio)
        self.recording_thread.daemon = True
        self.recording_thread.start()
    
    def record_audio(self):
        try:
            # Record using sounddevice
            duration = 10 * 60  # Maximum 10 minutes
            self.audio_data = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=1,
                device=self.selected_device,
                blocking=False
            )
            
            # Wait for user to stop
            while self.is_recording:
                sd.sleep(100)  # Check interval
            
        except Exception as e:
            # Show error in main thread
            self.root.after(0, lambda: messagebox.showerror("Recording Error", str(e)))
            self.root.after(0, self.reset_recording_ui)
    
    def stop_recording(self):
        self.is_recording = False
        
        # Stop recording and get data
        sd.stop()
        
        # Save recording file
        self.save_recording()
        
        # Reset UI
        self.reset_recording_ui()
        
        # Update filename
        new_name = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.name_var.set(new_name)
    
    def reset_recording_ui(self):
        self.record_btn.config(text="Start Recording")
        self.status_var.set("Ready")
    
    def save_recording(self):
        if self.audio_data is None:
            messagebox.showerror("Error", "No recording data to save")
            return
        
        filename = self.name_var.get().strip()
        if not filename.endswith('.wav'):
            filename += '.wav'
        
        save_path = os.path.join(self.path_var.get(), filename)
        
        try:
            # Remove silence if any
            audio_to_save = self.audio_data
            
            # Find non-silent parts
            if len(audio_to_save) > 0:
                # Flatten the array and find where audio exceeds threshold
                audio_flat = audio_to_save.flatten()
                non_silent = np.where(np.abs(audio_flat) > 0.001)[0]
                
                if len(non_silent) > 0:
                    end_point = min(non_silent[-1] + self.sample_rate, len(audio_flat))
                    audio_to_save = audio_flat[:end_point]
                else:
                    audio_to_save = audio_flat
            
            sf.write(save_path, audio_to_save, self.sample_rate)
            messagebox.showinfo("Success", f"Recording saved as:\n{save_path}")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Cannot save recording:\n{str(e)}")
    
    def on_preset_select(self, event):
        selection = self.preset_listbox.curselection()
        if selection:
            index = selection[0]
            name = self.preset_listbox.get(index)
            self.name_var.set(name)
    
    def add_to_preset(self):
        name = self.name_var.get().strip()
        if name and name not in self.preset_names:
            self.preset_names.append(name)
            self.update_preset_list()
            self.save_preset_names()
    
    def remove_from_preset(self):
        selection = self.preset_listbox.curselection()
        if selection:
            index = selection[0]
            del self.preset_names[index]
            self.update_preset_list()
            self.save_preset_names()
    
    def clear_preset(self):
        if messagebox.askyesno("Confirm", "Clear the preset names list?"):
            self.preset_names = []
            self.update_preset_list()
            self.save_preset_names()
    
    def update_preset_list(self):
        self.preset_listbox.delete(0, tk.END)
        for name in self.preset_names:
            self.preset_listbox.insert(tk.END, name)
    
    def browse_path(self):
        folder = filedialog.askdirectory(initialdir=self.path_var.get())
        if folder:
            self.path_var.set(folder)
            os.makedirs(folder, exist_ok=True)
    
    def load_preset_names(self):
        try:
            config_path = os.path.join(os.path.expanduser("~"), ".audio_recorder_config.json")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.preset_names = data.get('preset_names', [])
        except:
            self.preset_names = []
    
    def save_preset_names(self):
        try:
            config_path = os.path.join(os.path.expanduser("~"), ".audio_recorder_config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({'preset_names': self.preset_names}, f, ensure_ascii=False, indent=2)
        except:
            pass

if __name__ == "__main__":
    # Check dependencies
    try:
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
    except ImportError as e:
        print(f"Missing dependencies: {e}")
        print("Please install: pip install sounddevice soundfile numpy")
        exit(1)
    
    root = tk.Tk()
    app = AudioRecorderApp(root)
    root.mainloop()