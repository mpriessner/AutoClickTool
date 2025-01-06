import tkinter as tk
from tkinter import filedialog, messagebox
import json
import time
import pyautogui
import os

class MacroPlayerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Macro Player")
        self.root.geometry("500x300")
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        
        # Initialize variables
        self.macro_file = None
        self.macro_data = None
        self.is_playing = False
        self.pressed_keys = set()  # Track which keys are currently pressed
        
        # Default macro directory
        self.macro_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "macro_recording")
        
        # Create GUI elements
        self.create_gui()
        
    def create_gui(self):
        # File selection
        self.file_frame = tk.Frame(self.root)
        self.file_frame.pack(pady=10, padx=10, fill=tk.X)
        
        self.file_label = tk.Label(self.file_frame, text="No file selected", wraplength=400)
        self.file_label.pack(side=tk.LEFT, expand=True, fill=tk.X)
        
        self.browse_button = tk.Button(self.file_frame, text="Browse", command=self.browse_file)
        self.browse_button.pack(side=tk.RIGHT, padx=5)
        
        # Playback controls
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(pady=10)
        
        self.play_button = tk.Button(self.control_frame, text="Play Macro", 
                                   command=self.play_macro, state=tk.DISABLED,
                                   bg='green', fg='white', font=('Arial', 12))
        self.play_button.pack(pady=5)
        
        # Delay before start
        self.delay_frame = tk.Frame(self.root)
        self.delay_frame.pack(pady=5)
        
        self.delay_label = tk.Label(self.delay_frame, text="Start delay (seconds):")
        self.delay_label.pack(side=tk.LEFT, padx=5)
        
        self.delay_var = tk.StringVar(value="1")
        self.delay_entry = tk.Entry(self.delay_frame, textvariable=self.delay_var, width=5)
        self.delay_entry.pack(side=tk.LEFT)
        
        # Speed control
        self.speed_frame = tk.Frame(self.root)
        self.speed_frame.pack(pady=5)
        
        self.speed_label = tk.Label(self.speed_frame, text="Playback speed:")
        self.speed_label.pack(side=tk.LEFT, padx=5)
        
        self.speed_var = tk.StringVar(value="1.0")
        self.speed_entry = tk.Entry(self.speed_frame, textvariable=self.speed_var, width=5)
        self.speed_entry.pack(side=tk.LEFT)
        
        # Status
        self.status_label = tk.Label(self.root, text="Status: Ready", font=('Arial', 10))
        self.status_label.pack(pady=10)
        
        self.action_label = tk.Label(self.root, text="Current action: None", font=('Arial', 10))
        self.action_label.pack(pady=5)
        
        # Stop hotkey info
        self.hotkey_label = tk.Label(self.root, 
            text="Press 'esc' at any time to stop playback",
            font=('Arial', 9))
        self.hotkey_label.pack(pady=5)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            initialdir=self.macro_dir,
            title="Select Macro File",
            filetypes=(("JSON files", "*.json"), ("All files", "*.*"))
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    self.macro_data = json.load(f)
                self.macro_file = filename
                self.file_label.config(text=f"Selected: {os.path.basename(filename)}")
                self.play_button.config(state=tk.NORMAL)
                self.status_label.config(text=f"Status: Loaded {len(self.macro_data)} actions")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load macro file: {str(e)}")
    
    def execute_action(self, action):
        """Execute a single action from the macro"""
        action_type = action['action_type']
        
        if action_type in ['button_down', 'button_up', 'drag']:
            # Mouse action
            x, y = action['x'], action['y']
            button = action['button']
            
            # Move mouse to position (with smooth movement)
            pyautogui.moveTo(x, y, duration=action['wait_time'])
            
            # Perform the mouse action
            if action_type == 'button_down':
                pyautogui.mouseDown(button=button)
            elif action_type == 'button_up':
                pyautogui.mouseUp(button=button)
            # For drag, we just move the mouse since button state is handled by down/up
        
        elif action_type in ['key_down', 'key_up']:
            # Keyboard action
            key = action['key'].lower()
            
            # Special key mapping for PyAutoGUI
            key_mapping = {
                'vanster windows': 'win',
                'hoger windows': 'win',
                'windows': 'win',
                'enter': 'enter',
                'mellanslag': 'space',
                'space': 'space',
                'shift': 'shift',
                'ctrl': 'ctrl',
                'alt': 'alt',
                'tab': 'tab',
                'escape': 'esc',
                'esc': 'esc',
                'backspace': 'backspace',
                'delete': 'del',
                'up': 'up',
                'down': 'down',
                'left': 'left',
                'right': 'right',
            }
            
            # Get the correct key (either special key or character)
            actual_key = key_mapping.get(key, key)
            
            try:
                # Special handling for Windows key
                if actual_key == 'win' and action_type == 'key_down':
                    pyautogui.press('win')
                    time.sleep(0.05)  # Small delay after Windows key press
                    self.pressed_keys.add(actual_key)
                elif actual_key == 'win' and action_type == 'key_up':
                    self.pressed_keys.discard(actual_key)
                else:
                    # Normal key handling for non-Windows keys
                    if action_type == 'key_down':
                        pyautogui.keyDown(actual_key)
                        time.sleep(0.05)  # Small delay after key press
                        self.pressed_keys.add(actual_key)
                    else:  # key_up
                        if actual_key in self.pressed_keys:  # Only release if we pressed it
                            time.sleep(0.05)  # Small delay before key release
                            pyautogui.keyUp(actual_key)
                            self.pressed_keys.discard(actual_key)
            except Exception as e:
                print(f"Error with key {actual_key}: {str(e)}")
                # Try to release the key if there was an error
                if actual_key in self.pressed_keys:
                    try:
                        pyautogui.keyUp(actual_key)
                        self.pressed_keys.discard(actual_key)
                    except:
                        pass

    def cleanup_keys(self):
        """Ensure all pressed keys are released"""
        for key in list(self.pressed_keys):
            try:
                pyautogui.keyUp(key)
            except:
                pass
        self.pressed_keys.clear()

    def stop_playback(self):
        """Stop macro playback and ensure all keys are released"""
        if self.is_playing:
            self.is_playing = False
            self.cleanup_keys()
            self.status_label.config(text="Status: Playback stopped by user")

    def play_macro(self):
        if not self.macro_data or self.is_playing:
            return
        
        try:
            delay = float(self.delay_var.get())
            speed = float(self.speed_var.get())
            if speed <= 0:
                raise ValueError("Speed must be greater than 0")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}")
            return
        
        self.is_playing = True
        self.play_button.config(state=tk.DISABLED)
        self.status_label.config(text=f"Status: Starting in {delay} seconds...")
        self.root.update()
        
        # Initial delay
        time.sleep(delay)
        
        try:
            # Play the macro
            for action_id in sorted(self.macro_data.keys(), key=int):
                if not self.is_playing:  # Check if we should stop
                    break
                    
                action = self.macro_data[action_id]
                
                # Update status
                if 'key' in action:
                    self.action_label.config(
                        text=f"Current action: {action['action_type']} key '{action['key']}'")
                else:
                    self.action_label.config(
                        text=f"Current action: {action['action_type']} {action['button']} at ({action['x']}, {action['y']})")
                self.root.update()
                
                # Execute the action
                self.execute_action(action)
                
                # Wait for next action (if not a movement action)
                if action['action_type'] not in ['drag']:
                    time.sleep(action['wait_time'] / speed)
            
            if self.is_playing:  # Only show success if not stopped
                self.status_label.config(text="Status: Macro completed successfully")
            
        except Exception as e:
            self.status_label.config(text=f"Status: Error - {str(e)}")
            messagebox.showerror("Error", f"Error playing macro: {str(e)}")
        
        finally:
            self.is_playing = False
            self.cleanup_keys()  # Ensure all keys are released when done
            self.play_button.config(state=tk.NORMAL)
            self.action_label.config(text="Current action: None")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    # Fail-safe: Moving mouse to corner will abort
    pyautogui.FAILSAFE = True
    
    app = MacroPlayerGUI()
    app.run()
