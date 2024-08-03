import pyaudio
import numpy as np
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import pygame

class MicrophoneMonitor:
    def __init__(self, root):
        self.root = root
        self.root.title("Microphone Monitor")
        self.root.geometry("400x300")

        self.stream = None
        self.audio = pyaudio.PyAudio()
        self.device_index = None
        self.peak_level = 50
        self.sensitivity = 0.5
        self.monitoring = False
        self.cooldown = False

        pygame.mixer.init()
        
        self.create_widgets()

    def create_widgets(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.device_selector = ttk.Combobox(frame, state="readonly", font=('Arial', 10))
        self.device_selector.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))
        self.device_selector['values'] = self.get_input_devices()
        self.device_selector.bind("<<ComboboxSelected>>", self.select_device)

        self.sensitivity_scale = ttk.Scale(frame, from_=0, to=1, orient="horizontal", command=self.adjust_sensitivity)
        self.sensitivity_scale.set(0.5)
        self.sensitivity_scale.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky=(tk.W, tk.E))

        ttk.Label(frame, text="Peak Level:", font=('Arial', 10)).grid(row=2, column=0, padx=5, pady=5, sticky=tk.W)
        self.peak_entry = ttk.Entry(frame, width=10, font=('Arial', 10))
        self.peak_entry.grid(row=2, column=1, padx=5, pady=5, sticky=tk.E)
        self.peak_entry.insert(0, "50")

        self.current_level_label = ttk.Label(frame, text="Current Level: 0", font=('Arial', 10))
        self.current_level_label.grid(row=3, column=0, columnspan=2, padx=5, pady=5)

        self.start_button = ttk.Button(frame, text="Start", command=self.start_monitoring, state="disabled", font=('Arial', 10))
        self.start_button.grid(row=4, column=0, padx=5, pady=5)
        
        self.stop_button = ttk.Button(frame, text="Stop", command=self.stop_monitoring, state="disabled", font=('Arial', 10))
        self.stop_button.grid(row=4, column=1, padx=5, pady=5)

        self.debug_label = ttk.Label(frame, text="", font=('Arial', 10))
        self.debug_label.grid(row=5, column=0, columnspan=2, padx=5, pady=5)

    def get_input_devices(self):
        devices = []
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info['maxInputChannels'] > 0:
                devices.append(f"{device_info['index']}: {device_info['name']}")
        return devices

    def select_device(self, event):
        selected_device = self.device_selector.get()
        self.device_index = int(selected_device.split(":")[0])
        self.start_button.config(state="normal")
        self.debug_label.config(text=f"Selected Device Index: {self.device_index}")

    def adjust_sensitivity(self, value):
        self.sensitivity = float(value)

    def start_monitoring(self):
        if self.device_index is None:
            messagebox.showerror("Error", "No input device selected")
            return

        self.peak_level = int(self.peak_entry.get())
        self.monitoring = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")

        self.stream = self.audio.open(format=pyaudio.paInt16,
                                      channels=1,
                                      rate=44100,
                                      input=True,
                                      input_device_index=self.device_index,
                                      frames_per_buffer=1024)

        self.monitor_thread = threading.Thread(target=self.monitor_microphone)
        self.monitor_thread.start()

    def stop_monitoring(self):
        self.monitoring = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None

    def monitor_microphone(self):
        while self.monitoring:
            data = np.frombuffer(self.stream.read(1024), dtype=np.int16)
            peak = np.abs(np.max(data))
            current_level = peak * self.sensitivity / 32768.0 * 100
            self.current_level_label.config(text=f"Current Level: {current_level:.2f}")

            if current_level > self.peak_level and not self.cooldown:
                threading.Thread(target=self.play_beep).start()
                self.cooldown = True
                threading.Timer(3, self.reset_cooldown).start()

            time.sleep(0.1)

    def play_beep(self):
        pygame.mixer.music.load("beep.mp3")
        pygame.mixer.music.play()

    def reset_cooldown(self):
        self.cooldown = False

    def on_closing(self):
        self.stop_monitoring()
        pygame.mixer.quit()
        self.audio.terminate()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = MicrophoneMonitor(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
