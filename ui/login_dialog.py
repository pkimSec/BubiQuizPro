#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BubiQuizPro - Login Dialog

This module implements a simple login dialog for selecting a username.
"""

import tkinter as tk
from tkinter import ttk
import os
import json
import logging

logger = logging.getLogger(__name__)

class LoginDialog(tk.Toplevel):
    """Dialog for selecting or entering a username."""
    
    def __init__(self, parent, settings_file=None):
        """
        Initialize the login dialog.
        
        Args:
            parent: Parent window
            settings_file: Path to settings file
        """
        super().__init__(parent)
        self.title("BubiQuizPro - Login")
        self.transient(parent)
        self.grab_set()
        
        # Center the dialog
        window_width = 400
        window_height = 300
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        self.username = ""
        self.cancelled = False
        self.settings_file = settings_file
        
        # Create UI
        self._create_widgets()
        
        # Load last username
        self._load_last_username()
        
        # Make dialog modal
        self.wait_window(self)
    
    def _create_widgets(self):
        """Create the dialog widgets."""
        # Main frame
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill='both', expand=True)
        
        # Logo/title
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill='x', pady=10)
        
        title_label = ttk.Label(title_frame, text="BubiQuizPro", 
                             font=('Arial', 18, 'bold'))
        title_label.pack()
        
        subtitle_label = ttk.Label(title_frame, text="Self-Study Quiz Application")
        subtitle_label.pack()
        
        # Username entry
        entry_frame = ttk.LabelFrame(main_frame, text="Enter Username")
        entry_frame.pack(fill='x', pady=20)
        
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(entry_frame, textvariable=self.username_var, width=30)
        username_entry.pack(padx=20, pady=20)
        
        # Recent usernames (if any)
        self.recent_frame = ttk.LabelFrame(main_frame, text="Recent Users")
        self.recent_frame.pack(fill='x', pady=10)
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=20)
        
        cancel_btn = ttk.Button(button_frame, text="Cancel", 
                             command=self._on_cancel)
        cancel_btn.pack(side='left', padx=5)
        
        login_btn = ttk.Button(button_frame, text="Login", 
                            command=self._on_login,
                            style='Primary.TButton')
        login_btn.pack(side='right', padx=5)
        
        # Bind return key to login
        self.bind('<Return>', lambda e: self._on_login())
        
        # Focus username entry
        username_entry.focus_set()
    
    def _load_last_username(self):
        """Load the last used username from settings."""
        if not self.settings_file or not os.path.exists(self.settings_file):
            return
            
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
                
            # Get username from settings
            username = settings.get('general', {}).get('username', '')
            if username:
                self.username_var.set(username)
                
            # Get recent usernames (if implemented)
            recent_users = settings.get('recent_users', [])
            if recent_users:
                for user in recent_users[:5]:  # Show max 5 recent users
                    btn = ttk.Button(self.recent_frame, text=user,
                                  command=lambda u=user: self._select_user(u))
                    btn.pack(fill='x', padx=10, pady=2)
            else:
                # Hide the frame if no recent users
                self.recent_frame.pack_forget()
                
        except Exception as e:
            logger.error(f"Error loading last username: {e}", exc_info=True)
    
    def _select_user(self, username):
        """
        Select a username from the recent list.
        
        Args:
            username (str): Username to select
        """
        self.username_var.set(username)
        self._on_login()
    
    def _on_login(self):
        """Handle login button click."""
        username = self.username_var.get().strip()
        if username:
            self.username = username
            self.destroy()
        else:
            # If no username, just use anonymous
            self.username = "Anonymous"
            self.destroy()
    
    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancelled = True
        self.username = ""
        self.destroy()