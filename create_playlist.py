import tkinter as tk
from tkinter import ttk
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import random
from tkinter import messagebox
import threading
import os

class SpotifyIntervalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify Interval Trainer")
        
        # Set window size
        self.root.geometry("1200x600")
        
        # Spotify Setup
        self.spotify = None
        self.auth_manager = None  # Auth manager for Spotify
        self.track_cache = {}     # Cache for track info
        self.tracks = {
            'Example_80BPM': [
                'spotify:track:PLACEHOLDER_TRACK_ID_1',
                'spotify:track:PLACEHOLDER_TRACK_ID_2'
            ],
            'Example_84BPM': [
                'spotify:track:PLACEHOLDER_TRACK_ID_3',
                'spotify:track:PLACEHOLDER_TRACK_ID_4'
            ],
            'Pause': [
                'spotify:track:PLACEHOLDER_TRACK_ID_5'
            ]
        }
        
        # Create GUI elements
        self.create_login_frame()
        self.create_interval_frame()
        self.create_playlist_frame()
        self.create_status_frame()
        self.create_track_display_frame()
        
        # Spotify credentials (safe placeholders)
        self.default_client_id = "INSERT_YOUR_CLIENT_ID"
        self.default_client_secret = "INSERT_YOUR_CLIENT_SECRET"
        self.client_id_entry.insert(0, self.default_client_id)
        self.client_secret_entry.insert(0, self.default_client_secret)

    def create_login_frame(self):
        """Creates the login section"""
        login_frame = ttk.LabelFrame(self.root, text="Spotify Login", padding="5")
        login_frame.grid(row=0, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        
        ttk.Label(login_frame, text="Client ID:").grid(row=0, column=0, padx=5, pady=2)
        self.client_id_entry = ttk.Entry(login_frame, width=40)
        self.client_id_entry.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(login_frame, text="Client Secret:").grid(row=1, column=0, padx=5, pady=2)
        self.client_secret_entry = ttk.Entry(login_frame, width=40, show="*")
        self.client_secret_entry.grid(row=1, column=1, padx=5, pady=2)
        
        ttk.Button(login_frame, text="Connect", command=self.connect_spotify).grid(row=2, column=0, columnspan=2, pady=5)

    def create_interval_frame(self):
        """Creates the section for interval settings"""
        interval_frame = ttk.LabelFrame(self.root, text="New Interval", padding="5")
        interval_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        
        ttk.Label(interval_frame, text="Track Group:").grid(row=0, column=0, padx=5, pady=2)
        self.track_group = ttk.Combobox(interval_frame, values=list(self.tracks.keys()))
        self.track_group.grid(row=0, column=1, padx=5, pady=2)
        
        ttk.Label(interval_frame, text="Duration (seconds):").grid(row=1, column=0, padx=5, pady=2)
        self.duration = ttk.Spinbox(interval_frame, from_=30, to=600, increment=30)
        self.duration.grid(row=1, column=1, padx=5, pady=2)
        self.duration.set(120)
        
        ttk.Button(interval_frame, text="Add Interval", 
                  command=self.add_interval).grid(row=2, column=0, columnspan=2, pady=5)

    def create_playlist_frame(self):
        """Creates the section for the workout playlist"""
        playlist_frame = ttk.LabelFrame(self.root, text="Workout Playlist", padding="5")
        playlist_frame.grid(row=1, column=1, rowspan=2, padx=5, pady=5, sticky="nsew")
        
        self.interval_list = tk.Listbox(playlist_frame, width=40, height=10)
        self.interval_list.grid(row=0, column=0, columnspan=2, padx=5, pady=5)
        
        ttk.Button(playlist_frame, text="Remove", 
                  command=self.remove_interval).grid(row=1, column=0, pady=5)
        ttk.Button(playlist_frame, text="Start Workout", 
                  command=self.start_workout).grid(row=1, column=1, pady=5)

    def create_status_frame(self):
        """Creates the status message section"""
        status_frame = ttk.LabelFrame(self.root, text="Status", padding="5")
        status_frame.grid(row=3, column=0, columnspan=3, padx=5, pady=5, sticky="ew")
        
        self.status_label = ttk.Label(status_frame, text="Ready")
        self.status_label.grid(row=0, column=0, padx=5, pady=2)

    def create_track_display_frame(self):
        """Creates the section for displaying available songs"""
        self.track_display_frame = ttk.LabelFrame(self.root, text="Available Songs", padding="5")
        self.track_display_frame.grid(row=0, column=2, rowspan=3, padx=5, pady=5, sticky="nsew")
        
        group_frame = ttk.Frame(self.track_display_frame)
        group_frame.pack(fill="x", pady=5)
        
        ttk.Label(group_frame, text="Group:").pack(side="left", padx=5)
        self.group_selector = ttk.Combobox(group_frame, values=list(self.tracks.keys()))
        self.group_selector.pack(side="left", padx=5, fill="x", expand=True)
        
        self.track_listbox = tk.Listbox(self.track_display_frame, width=50, height=20)
        scrollbar = ttk.Scrollbar(self.track_display_frame, orient="vertical", 
                                command=self.track_listbox.yview)
        
        self.track_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.track_listbox.config(yscrollcommand=scrollbar.set)
        self.group_selector.bind('<<ComboboxSelected>>', self.update_song_list)

    def connect_spotify(self):
        """Connects to Spotify and initializes the cache"""
        try:
            cache_path = os.path.join(os.getcwd(), "spotify_cache.txt")
            
            # Create a single auth manager for the session
            self.auth_manager = SpotifyOAuth(
                client_id=self.client_id_entry.get(),
                client_secret=self.client_secret_entry.get(),
                redirect_uri="http://localhost:8888/callback",
                scope="user-modify-playback-state user-read-playback-state user-library-read",
                open_browser=True,
                cache_path=cache_path,
                show_dialog=True
            )
            
            self.spotify = spotipy.Spotify(auth_manager=self.auth_manager)
            self.update_status("Successfully connected to Spotify!")
            
            # Preload all track information
            self.preload_track_info()
            
            if list(self.tracks.keys()):
                self.group_selector.set(list(self.tracks.keys())[0])
                self.update_song_list()
                
        except Exception as e:
            self.update_status(f"Connection error: {str(e)}")

    def preload_track_info(self):
        """Loads all track information into the cache"""
        self.update_status("Loading track information...")
        total_tracks = sum(len(tracks) for tracks in self.tracks.values())
        loaded_tracks = 0

        for group in self.tracks:
            for track_uri in self.tracks[group]:
                if track_uri not in self.track_cache:
                    try:
                        track_info = self.spotify.track(track_uri)
                        self.track_cache[track_uri] = {
                            'name': track_info['name'],
                            'artist': track_info['artists'][0]['name'],
                            'duration': track_info['duration_ms'] / 1000
                        }
                        loaded_tracks += 1
                        self.update_status(f"Loading tracks... ({loaded_tracks}/{total_tracks})")
                    except Exception as e:
                        self.update_status(f"Error loading {track_uri}: {str(e)}")
        
        self.update_status("All tracks loaded!")

    def update_song_list(self, event=None):
        """Updates the song list for the selected group"""
        if not self.spotify:
            self.update_status("Please connect to Spotify first!")
            return
            
        selected_group = self.group_selector.get()
        self.track_listbox.delete(0, tk.END)
        
        if selected_group in self.tracks:
            for track_uri in self.tracks[selected_group]:
                try:
                    if track_uri in self.track_cache:
                        track_info = self.track_cache[track_uri]
                        title = track_info['name']
                        artist = track_info['artist']
                        duration = track_info['duration']
                        minutes = int(duration) // 60
                        seconds = int(duration) % 60
                        self.track_listbox.insert(tk.END, 
                            f"{title} - {artist} ({minutes}:{seconds:02d})")
                    else:
                        self.track_listbox.insert(tk.END, 
                            f"Track not loaded ({track_uri})")
                except Exception as e:
                    self.track_listbox.insert(tk.END, 
                        f"Error loading track ({track_uri}): {str(e)}")
        
        self.update_status("Ready")

    def update_status(self, message):
        """Updates the status display"""
        self.status_label.config(text=message)
        self.root.update()

    def add_interval(self):
        """Adds a new interval to the playlist"""
        group = self.track_group.get()
        duration = self.duration.get()
        
        if group and duration:
            interval = f"{group} - {duration}s"
            self.interval_list.insert(tk.END, interval)
        else:
            self.update_status("Please fill in all fields!")

    def remove_interval(self):
        """Removes the selected interval"""
        try:
            selection = self.interval_list.curselection()
            self.interval_list.delete(selection)
        except:
            self.update_status("Please select an interval first!")

    def start_workout(self):
        """Starts the workout"""
        if not self.spotify:
            self.update_status("Please connect to Spotify first!")
            return
        
        intervals = []
        for i in range(self.interval_list.size()):
            interval_text = self.interval_list.get(i)
            group, duration = interval_text.split(" - ")
            duration = int(duration.replace("s", ""))
            intervals.append((group, duration))
        
        if not intervals:
            self.update_status("Playlist is empty!")
            return
            
        thread = threading.Thread(target=self.play_workout, args=(intervals,))
        thread.daemon = True
        thread.start()

    def play_workout(self, intervals):
        """Plays the workout"""
        try:
            devices = self.spotify.devices()
            
            if not devices['devices']:
                self.update_status("No active Spotify device found!")
                return
                
            device_id = devices['devices'][0]['id']
            
            for group, target_duration in intervals:
                if group in self.tracks and self.tracks[group]:
                    available_tracks = self.tracks[group].copy()
                    elapsed_time = 0
                    
                    while elapsed_time < target_duration and available_tracks:
                        track = random.choice(available_tracks)
                        available_tracks.remove(track)
                        
                        if not self.spotify:
                            self.update_status("Lost connection to Spotify!")
                            return
                            
                        try:
                            track_info = self.track_cache[track]
                            track_name = f"{track_info['name']} - {track_info['artist']}"
                            track_duration = track_info['duration']
                            
                            remaining_time = target_duration - elapsed_time
                            
                            self.spotify.start_playback(device_id=device_id, uris=[track])
                            
                            self.update_status(
                                f"Playing {track_name} from {group}\n"
                                f"{int(remaining_time)}s left in current interval"
                            )
                            
                            wait_time = min(track_duration, remaining_time)
                            time.sleep(wait_time)
                            elapsed_time += wait_time
                            
                        except Exception as e:
                            self.update_status(f"Error playing {track}: {str(e)}")
                            continue
                    
                    if elapsed_time < target_duration:
                        remaining_time = target_duration - elapsed_time
                        self.update_status(
                            f"No more tracks in {group}.\n"
                            f"Waiting {int(remaining_time)}s until next interval"
                        )
                        time.sleep(remaining_time)
                        
                else:
                    self.update_status(f"Warning: No tracks in group {group}")
                    time.sleep(1)
                    
        except Exception as e:
            self.update_status(f"Error during playback: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = SpotifyIntervalGUI(root)
    root.mainloop()
