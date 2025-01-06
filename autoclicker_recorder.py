import tkinter as tk
import pyautogui
import json
import time
import os
from tkinter import messagebox
import threading
import mouse
import keyboard
from datetime import datetime
import unicodedata

class MacroRecorderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Macro Recorder")
        self.root.geometry("400x250")
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        
        self.recording = False
        self.actions = {}
        self.action_count = 0
        self.start_time = 0
        self.last_action_time = 0
        
        # Track button states
        self.left_button_down = False
        self.right_button_down = False
        self.last_position = None
        
        # Track pressed keys
        self.pressed_keys = set()
        
        # Create macro_recording directory if it doesn't exist
        self.recording_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "macro_recording")
        os.makedirs(self.recording_dir, exist_ok=True)
        
        # Output file will be set when recording starts
        self.output_file = None
        
        # Create GUI elements
        self.status_label = tk.Label(self.root, text="Status: Not Recording", font=('Arial', 12))
        self.status_label.pack(pady=10)
        
        self.record_button = tk.Button(self.root, text="Start Recording", command=self.toggle_recording,
                                     bg='green', fg='white', font=('Arial', 12))
        self.record_button.pack(pady=10)
        
        self.action_count_label = tk.Label(self.root, text="Actions recorded: 0", font=('Arial', 12))
        self.action_count_label.pack(pady=10)
        
        self.current_action_label = tk.Label(self.root, text="Current action: None", font=('Arial', 10))
        self.current_action_label.pack(pady=5)
        
        self.file_label = tk.Label(self.root, text="Output file: None", font=('Arial', 10), wraplength=380)
        self.file_label.pack(pady=5)
        
        # Instructions
        self.instruction_label = tk.Label(self.root, 
            text="Press 'esc' to stop recording\nRecords mouse clicks, drags, and keyboard inputs",
            font=('Arial', 9))
        self.instruction_label.pack(pady=5)
        
    def generate_filename(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return os.path.join(self.recording_dir, f"macro_{timestamp}.json")
        
    def toggle_recording(self):
        if not self.recording:
            # Start recording
            self.recording = True
            self.actions = {}
            self.action_count = 0
            self.start_time = time.time()
            self.last_action_time = self.start_time
            self.left_button_down = False
            self.right_button_down = False
            self.last_position = None
            self.pressed_keys.clear()
            
            # Generate new output file name
            self.output_file = self.generate_filename()
            self.file_label.config(text=f"Output file: {os.path.basename(self.output_file)}")
            
            self.record_button.config(text="Stop Recording", bg='red')
            self.status_label.config(text="Status: Recording")
            
            # Start recording threads
            self.record_thread = threading.Thread(target=self.record_actions)
            self.record_thread.daemon = True
            self.record_thread.start()
            
            # Start keyboard listener
            keyboard.on_press(self.on_key_press)
            keyboard.on_release(self.on_key_release)
        else:
            # Stop recording
            self.stop_recording()
    
    def stop_recording(self):
        """Stop recording and clean up"""
        self.recording = False
        keyboard.unhook_all()
        
        # Clear any remaining pressed keys
        self.pressed_keys.clear()
        
        self.record_button.config(text="Start Recording", bg='green')
        self.status_label.config(text="Status: Not Recording")
        self.current_action_label.config(text="Current action: None")
        self.save_recording()
        messagebox.showinfo("Recording Saved", f"Recording saved to {self.output_file}")
    
    def on_key_press(self, event):
        if not self.recording:
            return
            
        if event.name == 'esc':
            self.root.after(0, self.stop_recording)
            return
            
        # Normalize the key name
        normalized_key = self.normalize_key(event.name)
        
        if normalized_key not in self.pressed_keys:
            self.pressed_keys.add(normalized_key)
            self.record_action("key_down", normalized_key, None)
    
    def on_key_release(self, event):
        if not self.recording or event.name == 'esc':
            return
            
        # Normalize the key name
        normalized_key = self.normalize_key(event.name)
        
        if normalized_key in self.pressed_keys:
            self.pressed_keys.remove(normalized_key)
            self.record_action("key_up", normalized_key, None)
    
    def record_actions(self):
        while self.recording:
            current_pos = pyautogui.position()
            
            # Check for button press events
            if mouse.is_pressed("left"):
                if not self.left_button_down:
                    self.record_action("button_down", "left", current_pos)
                    self.left_button_down = True
                    self.last_position = current_pos
                elif self.last_position and (abs(current_pos[0] - self.last_position[0]) > 5 or 
                                          abs(current_pos[1] - self.last_position[1]) > 5):
                    self.record_action("drag", "left", current_pos)
                    self.last_position = current_pos
            elif self.left_button_down:  # Left button was released
                self.record_action("button_up", "left", current_pos)
                self.left_button_down = False
                self.last_position = None
            
            # Same for right button
            if mouse.is_pressed("right"):
                if not self.right_button_down:
                    self.record_action("button_down", "right", current_pos)
                    self.right_button_down = True
                    self.last_position = current_pos
                elif self.last_position and (abs(current_pos[0] - self.last_position[0]) > 5 or 
                                          abs(current_pos[1] - self.last_position[1]) > 5):
                    self.record_action("drag", "right", current_pos)
                    self.last_position = current_pos
            elif self.right_button_down:  # Right button was released
                self.record_action("button_up", "right", current_pos)
                self.right_button_down = False
                self.last_position = None
            
            time.sleep(0.01)  # Small delay to reduce CPU usage
    
    def normalize_key(self, key):
        """Normalize special characters and key names"""
        # Special cases for composite key names and Windows keys
        key = key.lower()
        
        # Special key mappings
        key_mapping = {
            'left windows': 'vanster windows',
            'right windows': 'hoger windows',
            'vänster windows': 'vanster windows',
            'höger windows': 'hoger windows',
            'left shift': 'shiftleft',
            'right shift': 'shiftright',
            'left ctrl': 'ctrlleft',
            'right ctrl': 'ctrlright',
            'left alt': 'altleft',
            'right alt': 'altright',
            'space': 'space',
            'spacebar': 'space'
        }
        
        # Check for mapped keys
        for original, mapped in key_mapping.items():
            if key == original or key.replace(' ', '') == original.replace(' ', ''):
                return mapped
        
        # For other keys, normalize special characters
        return ''.join(c for c in unicodedata.normalize('NFKD', key)
                      if not unicodedata.combining(c))
    
    def record_action(self, action_type, button, position):
        current_time = time.time()
        wait_time = current_time - self.last_action_time
        
        action_data = {
            "action_type": action_type,
            "wait_time": round(wait_time, 3)
        }
        
        # Add position for mouse actions
        if position is not None:
            action_data["x"] = position[0]
            action_data["y"] = position[1]
            action_data["button"] = button
        else:  # Keyboard action
            action_data["key"] = button
        
        self.actions[str(self.action_count)] = action_data
        self.action_count += 1
        self.last_action_time = current_time
        
        # Update GUI labels
        self.action_count_label.config(text=f"Actions recorded: {self.action_count}")
        if position is not None:
            self.current_action_label.config(
                text=f"Current action: {action_type} {button} at {position}")
        else:
            self.current_action_label.config(
                text=f"Current action: {action_type} key '{button}'")
        
        # Small delay for button_down/up events to avoid duplicates
        if action_type in ["button_down", "button_up", "key_down", "key_up"]:
            time.sleep(0.1)
    
    def save_recording(self):
        if self.actions:
            with open(self.output_file, 'w') as f:
                json.dump(self.actions, f, indent=2)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MacroRecorderGUI()
    app.run()
