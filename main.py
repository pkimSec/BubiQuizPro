#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BubiQuizPro - Main Application Entry Point

This is the main entry point for the BubiQuizPro application.
It initializes the application, loads configurations, and launches the main window.
"""

import os
import sys
import tkinter as tk
from tkinter import messagebox
import logging
from datetime import datetime
import json

# Add module paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'modules'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'ui'))

# Import application modules
from modules.data_manager import DataManager
from modules.quiz_engine import QuizEngine
from modules.stats_manager import StatsManager
from ui.main_window import MainWindow
from ui.login_dialog import LoginDialog

# Configure logging
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f'bubiquizpro_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class BubiQuizPro:
    """Main application class for BubiQuizPro."""
    
    def __init__(self):
        """Initialize the application."""
        self.root = tk.Tk()
        self.root.title("BubiQuizPro")
        self.root.geometry("1024x768")
        self.root.minsize(800, 600)
        
        # Set up data directory structure
        self._setup_directories()
        
        try:
            # Initialize application components
            self.data_manager = DataManager()
            self.quiz_engine = QuizEngine(self.data_manager)
            self.stats_manager = StatsManager(self.data_manager)
            
            # Show login dialog
            self._show_login_dialog()
            
            # Create main window
            self.main_window = MainWindow(
                self.root, 
                self.data_manager, 
                self.quiz_engine, 
                self.stats_manager
            )
            
            # Apply username from login
            if hasattr(self, 'username') and self.username:
                self._update_username(self.username)
            
            logger.info("Application initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing application: {e}", exc_info=True)
            messagebox.showerror("Initialization Error", 
                               f"An error occurred while starting the application: {str(e)}")
            sys.exit(1)
    
    def _show_login_dialog(self):
        """Show the login dialog."""
        # Path to settings file
        settings_file = os.path.join(self.data_manager.data_dir, 'settings.json')
        
        # Show login dialog
        login_dialog = LoginDialog(self.root, settings_file)
        
        # Get username
        self.username = login_dialog.username
        
        # If cancelled, use default
        if login_dialog.cancelled:
            self.username = ""
    
    def _update_username(self, username):
        """
        Update the username in settings.
        
        Args:
            username (str): Username to set
        """
        # Path to settings file
        settings_file = os.path.join(self.data_manager.data_dir, 'settings.json')
        
        # Load or create settings
        settings = {}
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
            except Exception:
                settings = {}
        
        # Ensure general section exists
        if 'general' not in settings:
            settings['general'] = {}
        
        # Update username
        settings['general']['username'] = username
        
        # Add to recent users list
        if 'recent_users' not in settings:
            settings['recent_users'] = []
        
        # Add username to recent users if not already there
        if username and username not in settings['recent_users']:
            settings['recent_users'].insert(0, username)
            # Keep only the last 5 users
            settings['recent_users'] = settings['recent_users'][:5]
        
        # Save settings
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)
        
    def _setup_directories(self):
        """Set up the necessary directory structure."""
        base_dir = os.path.dirname(__file__)
        
        # Create required directories if they don't exist
        directories = [
            os.path.join(base_dir, 'data'),
            os.path.join(base_dir, 'data', 'questions'),
            os.path.join(base_dir, 'data', 'exports')
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            logger.debug(f"Directory ensured: {directory}")
    
    def run(self):
        """Run the application main loop."""
        try:
            # Set app icon if available
            try:
                icon_path = os.path.join(os.path.dirname(__file__), 'resources', 'icon.ico')
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
            except Exception as e:
                logger.warning(f"Could not set application icon: {e}")
            
            # Run the application
            self.root.mainloop()
        except Exception as e:
            logger.error(f"Error in main loop: {e}", exc_info=True)
            messagebox.showerror("Runtime Error", 
                               f"An unexpected error occurred: {str(e)}")
        finally:
            # Perform cleanup
            try:
                if hasattr(self, 'data_manager'):
                    self.data_manager.close()
                logger.info("Application shutdown complete")
            except Exception as e:
                logger.error(f"Error during shutdown: {e}", exc_info=True)

if __name__ == "__main__":
    app = BubiQuizPro()
    app.run()   