#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BubiQuizPro - Settings Frame UI Component

This module implements the UI component for application settings.
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser, filedialog
import logging
import os
import json
import shutil
import subprocess
import platform
import threading

logger = logging.getLogger(__name__)

class SettingsFrame(ttk.Frame):
    """
    Frame for application settings.
    """
    
    def __init__(self, parent, data_manager):
        """
        Initialize the settings frame.
        
        Args:
            parent: Parent widget
            data_manager: DataManager instance
        """
        super().__init__(parent, style='Content.TFrame')
        
        self.data_manager = data_manager
        self.settings = {}
        
        # Create UI components
        self._create_ui()
        
        # Load settings
        self._load_settings()
        
        logger.info("SettingsFrame initialized")
    
    def _create_ui(self):
        """Create the UI components."""
        # Configure grid
        self.columnconfigure(0, weight=1)
        
        # Header
        header_frame = ttk.Frame(self, style='Content.TFrame')
        header_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=(20, 10))
        
        title_label = ttk.Label(header_frame, text="Settings", 
                             font=('Arial', 18, 'bold'))
        title_label.pack(side='left')
        
        # Settings content
        content_frame = ttk.Frame(self, style='Content.TFrame')
        content_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        
        # Create a notebook with tabs for different settings categories
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # General settings tab
        self.general_frame = self._create_general_tab()
        self.notebook.add(self.general_frame, text="General")
        
        # Quiz settings tab
        self.quiz_frame = self._create_quiz_tab()
        self.notebook.add(self.quiz_frame, text="Quiz")
        
        # Display settings tab
        self.display_frame = self._create_display_tab()
        self.notebook.add(self.display_frame, text="Display")
        
        # Data settings tab
        self.data_frame = self._create_data_tab()
        self.notebook.add(self.data_frame, text="Data")
        
        # Buttons section
        buttons_frame = ttk.Frame(self, style='Content.TFrame')
        buttons_frame.grid(row=2, column=0, sticky='ew', padx=20, pady=20)
        
        reset_btn = ttk.Button(buttons_frame, text="Reset to Defaults", 
                            command=self._reset_settings)
        reset_btn.pack(side='left', padx=5)
        
        apply_btn = ttk.Button(buttons_frame, text="Apply", 
                            command=self._apply_settings)
        apply_btn.pack(side='right', padx=5)
        
        save_btn = ttk.Button(buttons_frame, text="Save", 
                           command=self._save_settings,
                           style='Primary.TButton')
        save_btn.pack(side='right', padx=5)
    
    def _create_general_tab(self):
        """Create the general settings tab."""
        frame = ttk.Frame(self.notebook, style='Content.TFrame', padding=10)
        
        # Application settings
        app_frame = ttk.LabelFrame(frame, text="Application Settings", padding=10)
        app_frame.pack(fill='x', pady=10)
        
        # Configure grid
        app_frame.columnconfigure(0, weight=0)
        app_frame.columnconfigure(1, weight=1)
        
        # Username setting
        ttk.Label(app_frame, text="Username:").grid(row=0, column=0, sticky='w', pady=5)
        self.username_var = tk.StringVar()
        username_entry = ttk.Entry(app_frame, textvariable=self.username_var, width=30)
        username_entry.grid(row=0, column=1, sticky='w', pady=5, padx=5)
        
        # Startup behavior
        ttk.Label(app_frame, text="On Startup:").grid(row=1, column=0, sticky='w', pady=5)
        self.startup_var = tk.StringVar()
        startup_options = ["Show Home Screen", "Show Statistics", "Continue Last Session"]
        startup_combo = ttk.Combobox(app_frame, textvariable=self.startup_var, 
                                   values=startup_options, state='readonly')
        startup_combo.grid(row=1, column=1, sticky='w', pady=5, padx=5)
        
        # Autosave setting
        ttk.Label(app_frame, text="Auto-save:").grid(row=2, column=0, sticky='w', pady=5)
        self.autosave_var = tk.BooleanVar()
        autosave_check = ttk.Checkbutton(app_frame, text="Auto-save progress", 
                                       variable=self.autosave_var)
        autosave_check.grid(row=2, column=1, sticky='w', pady=5, padx=5)
        
        # Data management
        data_frame = ttk.LabelFrame(frame, text="Data Management", padding=10)
        data_frame.pack(fill='x', pady=10)
        
        # Configure grid
        data_frame.columnconfigure(0, weight=1)
        
        # Backup options
        ttk.Label(data_frame, text="Automatic Backups:").grid(row=0, column=0, sticky='w', pady=5)
        
        backup_options_frame = ttk.Frame(data_frame)
        backup_options_frame.grid(row=1, column=0, sticky='w', pady=5)
        
        self.backup_var = tk.StringVar()
        backup_options = [
            ("Never", "never"),
            ("Daily", "daily"),
            ("Weekly", "weekly"),
            ("Monthly", "monthly")
        ]
        
        for text, value in backup_options:
            ttk.Radiobutton(backup_options_frame, text=text, value=value, 
                          variable=self.backup_var).pack(side='left', padx=10)
        
        # Backup button
        backup_btn = ttk.Button(data_frame, text="Create Backup Now", 
                             command=self._backup_database)
        backup_btn.grid(row=2, column=0, sticky='w', pady=10, padx=5)
        
        return frame
    
    def _create_data_tab(self):
        """Create the data management tab."""
        frame = ttk.Frame(self.notebook, style='Content.TFrame', padding=10)
        
        # Progress Reset Section
        progress_frame = ttk.LabelFrame(frame, text="Progress Management", padding=10)
        progress_frame.pack(fill='x', pady=10)
        
        # Warning label
        warning_label = ttk.Label(progress_frame, 
                               text="Warning: These actions cannot be undone!",
                               font=('Arial', 10, 'bold'),
                               foreground='red')
        warning_label.pack(anchor='w', pady=(0, 10))
        
        # Reset progress for current user
        reset_current_btn = ttk.Button(progress_frame, 
                                     text="Reset Progress for Current User",
                                     command=self._reset_current_user_progress)
        reset_current_btn.pack(fill='x', pady=5)
        
        # Reset progress for all users
        reset_all_btn = ttk.Button(progress_frame, 
                                 text="Reset Progress for All Users",
                                 command=self._reset_all_users_progress)
        reset_all_btn.pack(fill='x', pady=5)
        
        # Questions Management Section
        questions_frame = ttk.LabelFrame(frame, text="Questions Management", padding=10)
        questions_frame.pack(fill='x', pady=10)
        
        # Folder location
        folder_path = os.path.join(self.data_manager.base_dir, 'data', 'questions')
        location_label = ttk.Label(questions_frame, 
                                text=f"Questions folder: {folder_path}")
        location_label.pack(anchor='w', pady=5)
        
        # Button frame for questions management
        questions_btn_frame = ttk.Frame(questions_frame)
        questions_btn_frame.pack(fill='x', pady=5)
        
        # Open questions folder
        open_folder_btn = ttk.Button(questions_btn_frame, 
                                   text="Open Questions Folder",
                                   command=self._open_questions_folder)
        open_folder_btn.pack(side='left', padx=5)
        
        # Delete all questions
        delete_all_btn = ttk.Button(questions_btn_frame, 
                                  text="Delete All Questions",
                                  command=self._delete_all_questions)
        delete_all_btn.pack(side='right', padx=5)
        
        # Database Management Section
        db_frame = ttk.LabelFrame(frame, text="Database Management", padding=10)
        db_frame.pack(fill='x', pady=10)
        
        # Database location
        db_path = self.data_manager.db_path
        db_label = ttk.Label(db_frame, 
                          text=f"Database file: {db_path}")
        db_label.pack(anchor='w', pady=5)
        
        # Database buttons
        db_btn_frame = ttk.Frame(db_frame)
        db_btn_frame.pack(fill='x', pady=5)
        
        # Backup database
        backup_db_btn = ttk.Button(db_btn_frame, 
                                 text="Backup Database",
                                 command=self._backup_database)
        backup_db_btn.pack(side='left', padx=5)

        return frame

    def _create_quiz_tab(self):
        """Create the quiz settings tab."""
        frame = ttk.Frame(self.notebook, style='Content.TFrame', padding=10)
        
        # Default quiz settings
        defaults_frame = ttk.LabelFrame(frame, text="Default Quiz Settings", padding=10)
        defaults_frame.pack(fill='x', pady=10)
        
        # Configure grid
        defaults_frame.columnconfigure(0, weight=0)
        defaults_frame.columnconfigure(1, weight=1)
        
        # Default question count
        ttk.Label(defaults_frame, text="Default Question Count:").grid(row=0, column=0, sticky='w', pady=5)
        self.default_count_var = tk.IntVar(value=10)
        default_count_spin = ttk.Spinbox(defaults_frame, from_=1, to=100, 
                                       textvariable=self.default_count_var, width=5)
        default_count_spin.grid(row=0, column=1, sticky='w', pady=5, padx=5)
        
        # Default quiz mode
        ttk.Label(defaults_frame, text="Default Quiz Mode:").grid(row=1, column=0, sticky='w', pady=5)
        self.default_mode_var = tk.StringVar()
        mode_options = ["Normal", "Weak Spots", "Spaced Repetition", "Exam"]
        mode_combo = ttk.Combobox(defaults_frame, textvariable=self.default_mode_var, 
                                values=mode_options, state='readonly')
        mode_combo.grid(row=1, column=1, sticky='w', pady=5, padx=5)
        
        # Default difficulty
        ttk.Label(defaults_frame, text="Default Difficulty:").grid(row=2, column=0, sticky='w', pady=5)
        self.default_difficulty_var = tk.StringVar()
        difficulty_options = ["Any", "leicht", "mittel", "schwer"]
        difficulty_combo = ttk.Combobox(defaults_frame, textvariable=self.default_difficulty_var, 
                                      values=difficulty_options, state='readonly')
        difficulty_combo.grid(row=2, column=1, sticky='w', pady=5, padx=5)
        
        # Answer behavior
        behavior_frame = ttk.LabelFrame(frame, text="Answer Behavior", padding=10)
        behavior_frame.pack(fill='x', pady=10)
        
        # Configure grid
        behavior_frame.columnconfigure(0, weight=0)
        behavior_frame.columnconfigure(1, weight=1)
        
        # Show immediate feedback
        ttk.Label(behavior_frame, text="Feedback:").grid(row=0, column=0, sticky='w', pady=5)
        self.immediate_feedback_var = tk.BooleanVar(value=True)
        feedback_check = ttk.Checkbutton(behavior_frame, text="Show immediate feedback", 
                                       variable=self.immediate_feedback_var)
        feedback_check.grid(row=0, column=1, sticky='w', pady=5, padx=5)
        
        # Text answer matching strictness
        ttk.Label(behavior_frame, text="Text Answer Matching:").grid(row=1, column=0, sticky='w', pady=5)
        self.matching_var = tk.StringVar()
        matching_options = ["Strict", "Moderate", "Lenient"]
        matching_combo = ttk.Combobox(behavior_frame, textvariable=self.matching_var, 
                                    values=matching_options, state='readonly')
        matching_combo.grid(row=1, column=1, sticky='w', pady=5, padx=5)
        
        # Spaced repetition settings
        sr_frame = ttk.LabelFrame(frame, text="Spaced Repetition Settings", padding=10)
        sr_frame.pack(fill='x', pady=10)
        
        # Configure grid
        sr_frame.columnconfigure(0, weight=0)
        sr_frame.columnconfigure(1, weight=1)
        
        # Learning algorithm
        ttk.Label(sr_frame, text="Algorithm:").grid(row=0, column=0, sticky='w', pady=5)
        self.algorithm_var = tk.StringVar()
        algorithm_options = ["Standard", "SM-2 (Anki-like)", "Custom"]
        algorithm_combo = ttk.Combobox(sr_frame, textvariable=self.algorithm_var, 
                                     values=algorithm_options, state='readonly')
        algorithm_combo.grid(row=0, column=1, sticky='w', pady=5, padx=5)
        
        # Scheduling factor
        ttk.Label(sr_frame, text="Scheduling Factor:").grid(row=1, column=0, sticky='w', pady=5)
        factor_frame = ttk.Frame(sr_frame)
        factor_frame.grid(row=1, column=1, sticky='w', pady=5, padx=5)
        
        self.factor_var = tk.DoubleVar(value=2.5)
        factor_scale = ttk.Scale(factor_frame, from_=1.0, to=4.0, 
                               variable=self.factor_var, 
                               length=200,
                               orient='horizontal')
        factor_scale.pack(side='left')
        
        factor_label = ttk.Label(factor_frame, textvariable=self.factor_var, width=5)
        factor_label.pack(side='left', padx=5)
        
        return frame
    
    def _create_display_tab(self):
        """Create the display settings tab."""
        frame = ttk.Frame(self.notebook, style='Content.TFrame', padding=10)
        
        # Theme settings
        theme_frame = ttk.LabelFrame(frame, text="Theme Settings", padding=10)
        theme_frame.pack(fill='x', pady=10)
        
        # Configure grid
        theme_frame.columnconfigure(0, weight=0)
        theme_frame.columnconfigure(1, weight=1)
        
        # Theme selection
        ttk.Label(theme_frame, text="Theme:").grid(row=0, column=0, sticky='w', pady=5)
        self.theme_var = tk.StringVar()
        theme_options = ["Light", "Dark", "System", "Custom"]
        theme_combo = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                 values=theme_options, state='readonly')
        theme_combo.grid(row=0, column=1, sticky='w', pady=5, padx=5)
        
        # Custom accent color
        ttk.Label(theme_frame, text="Accent Color:").grid(row=1, column=0, sticky='w', pady=5)
        
        color_frame = ttk.Frame(theme_frame)
        color_frame.grid(row=1, column=1, sticky='w', pady=5, padx=5)
        
        self.accent_color_var = tk.StringVar(value="#3498db")
        color_preview = tk.Label(color_frame, width=3, height=1, 
                              background=self.accent_color_var.get())
        color_preview.pack(side='left', padx=5)
        
        color_btn = ttk.Button(color_frame, text="Choose Color", 
                            command=lambda: self._choose_color(color_preview))
        color_btn.pack(side='left', padx=5)
        
        # Font settings
        font_frame = ttk.LabelFrame(frame, text="Font Settings", padding=10)
        font_frame.pack(fill='x', pady=10)
        
        # Configure grid
        font_frame.columnconfigure(0, weight=0)
        font_frame.columnconfigure(1, weight=1)
        
        # Font family
        ttk.Label(font_frame, text="Font:").grid(row=0, column=0, sticky='w', pady=5)
        self.font_var = tk.StringVar()
        font_options = ["Arial", "Helvetica", "Times New Roman", "Courier New", "System"]
        font_combo = ttk.Combobox(font_frame, textvariable=self.font_var, 
                                values=font_options, state='readonly')
        font_combo.grid(row=0, column=1, sticky='w', pady=5, padx=5)
        
        # Font size
        ttk.Label(font_frame, text="Font Size:").grid(row=1, column=0, sticky='w', pady=5)
        self.font_size_var = tk.IntVar(value=10)
        font_size_spin = ttk.Spinbox(font_frame, from_=8, to=18, 
                                   textvariable=self.font_size_var, width=5)
        font_size_spin.grid(row=1, column=1, sticky='w', pady=5, padx=5)
        
        # Preview
        preview_frame = ttk.LabelFrame(frame, text="Preview", padding=10)
        preview_frame.pack(fill='x', pady=10)
        
        self.preview_label = ttk.Label(preview_frame, 
                                    text="This is how your text will appear in the application.",
                                    font=('Arial', 10))
        self.preview_label.pack(pady=10)
        
        # Update preview button
        update_btn = ttk.Button(preview_frame, text="Update Preview", 
                             command=self._update_preview)
        update_btn.pack(pady=5)
        
        return frame
    
    def _load_settings(self):
        """Load settings from file."""
        # Check if settings file exists
        settings_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        settings_file = os.path.join(settings_dir, 'settings.json')
        
        # Default settings
        default_settings = {
            'general': {
                'username': '',
                'startup': 'Show Home Screen',
                'autosave': True,
                'backup': 'weekly'
            },
            'quiz': {
                'default_count': 10,
                'default_mode': 'Normal',
                'default_difficulty': 'Any',
                'immediate_feedback': True,
                'matching': 'Moderate',
                'algorithm': 'Standard',
                'factor': 2.5
            },
            'display': {
                'theme': 'Light',
                'accent_color': '#3498db',
                'font': 'Arial',
                'font_size': 10
            }
        }
        
        # Load settings if file exists, otherwise use defaults
        if os.path.exists(settings_file):
            try:
                with open(settings_file, 'r') as f:
                    loaded_settings = json.load(f)
                
                # Merge with defaults to ensure all keys exist
                self.settings = default_settings
                
                # Update with loaded values
                for category in loaded_settings:
                    if category in self.settings:
                        self.settings[category].update(loaded_settings[category])
                
                logger.info("Settings loaded from file")
                
            except Exception as e:
                logger.error(f"Error loading settings: {e}", exc_info=True)
                self.settings = default_settings
        else:
            self.settings = default_settings
            logger.info("Using default settings")
        
        # Apply to UI
        self._apply_settings_to_ui()
    
    def _apply_settings_to_ui(self):
        """Apply loaded settings to UI components."""
        # General settings
        general = self.settings.get('general', {})
        self.username_var.set(general.get('username', ''))
        self.startup_var.set(general.get('startup', 'Show Home Screen'))
        self.autosave_var.set(general.get('autosave', True))
        self.backup_var.set(general.get('backup', 'weekly'))
        
        # Quiz settings
        quiz = self.settings.get('quiz', {})
        self.default_count_var.set(quiz.get('default_count', 10))
        self.default_mode_var.set(quiz.get('default_mode', 'Normal'))
        self.default_difficulty_var.set(quiz.get('default_difficulty', 'Any'))
        self.immediate_feedback_var.set(quiz.get('immediate_feedback', True))
        self.matching_var.set(quiz.get('matching', 'Moderate'))
        self.algorithm_var.set(quiz.get('algorithm', 'Standard'))
        self.factor_var.set(quiz.get('factor', 2.5))
        
        # Display settings
        display = self.settings.get('display', {})
        self.theme_var.set(display.get('theme', 'Light'))
        self.accent_color_var.set(display.get('accent_color', '#3498db'))
        self.font_var.set(display.get('font', 'Arial'))
        self.font_size_var.set(display.get('font_size', 10))
        
        # Update UI elements that depend on settings
        self._update_preview()
    
    def _apply_settings(self):
        """Apply current UI values to the settings."""
        # Update settings dict from UI values
        
        # Get the old username for comparison
        old_username = self.settings.get('general', {}).get('username', '')
        new_username = self.username_var.get()
        
        # General settings
        self.settings['general'] = {
            'username': new_username,
            'startup': self.startup_var.get(),
            'autosave': self.autosave_var.get(),
            'backup': self.backup_var.get()
        }
        
        # Quiz settings
        self.settings['quiz'] = {
            'default_count': self.default_count_var.get(),
            'default_mode': self.default_mode_var.get(),
            'default_difficulty': self.default_difficulty_var.get(),
            'immediate_feedback': self.immediate_feedback_var.get(),
            'matching': self.matching_var.get(),
            'algorithm': self.algorithm_var.get(),
            'factor': self.factor_var.get()
        }
        
        # Display settings
        self.settings['display'] = {
            'theme': self.theme_var.get(),
            'accent_color': self.accent_color_var.get(),
            'font': self.font_var.get(),
            'font_size': self.font_size_var.get()
        }
        
        # Apply display settings immediately
        self._update_preview()
        
        # Update recent users if username changed
        if new_username and new_username != old_username:
            if 'recent_users' not in self.settings:
                self.settings['recent_users'] = []
                
            # Add username to recent users if not already there
            if new_username not in self.settings['recent_users']:
                self.settings['recent_users'].insert(0, new_username)
                # Keep only the last 5 users
                self.settings['recent_users'] = self.settings['recent_users'][:5]
        
        messagebox.showinfo("Settings Applied", 
                          "Settings have been applied. Some changes may require restarting the application.")
        
        logger.info("Settings applied")
    
    def _save_settings(self):
        """Save settings to file."""
        # First apply current UI values
        self._apply_settings()
        
        # Save to file
        settings_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
        settings_file = os.path.join(settings_dir, 'settings.json')
        
        try:
            with open(settings_file, 'w') as f:
                json.dump(self.settings, f, indent=4)
            
            messagebox.showinfo("Settings Saved", 
                              "Settings have been saved successfully.")
            
            logger.info("Settings saved to file")
            
        except Exception as e:
            logger.error(f"Error saving settings: {e}", exc_info=True)
            messagebox.showerror("Save Error", 
                               f"An error occurred while saving settings: {str(e)}")
    
    def _reset_settings(self):
        """Reset settings to defaults."""
        if messagebox.askyesno("Reset Settings", 
                             "Are you sure you want to reset all settings to defaults?"):
            # Default settings
            default_settings = {
                'general': {
                    'username': '',
                    'startup': 'Show Home Screen',
                    'autosave': True,
                    'backup': 'weekly'
                },
                'quiz': {
                    'default_count': 10,
                    'default_mode': 'Normal',
                    'default_difficulty': 'Any',
                    'immediate_feedback': True,
                    'matching': 'Moderate',
                    'algorithm': 'Standard',
                    'factor': 2.5
                },
                'display': {
                    'theme': 'Light',
                    'accent_color': '#3498db',
                    'font': 'Arial',
                    'font_size': 10
                }
            }
            
            self.settings = default_settings
            self._apply_settings_to_ui()
            
            messagebox.showinfo("Settings Reset", 
                              "All settings have been reset to defaults.")
            
            logger.info("Settings reset to defaults")
    
    def _update_preview(self):
        """Update the preview based on current font settings."""
        # Get current font settings
        font_family = self.font_var.get()
        font_size = self.font_size_var.get()
        
        # Update preview label
        self.preview_label.configure(font=(font_family, font_size))
    
    def _choose_color(self, preview_label):
        """
        Open color chooser dialog and update the color.
        
        Args:
            preview_label: Label to update with the selected color
        """
        color = colorchooser.askcolor(initialcolor=self.accent_color_var.get())[1]
        if color:
            self.accent_color_var.set(color)
            preview_label.config(background=color)
    
    def _reset_current_user_progress(self):
        """Reset progress for the current user."""
        if messagebox.askyesno("Reset Current User Progress",
                             "Are you sure you want to reset all progress for the current user?\n\n"
                             "This will remove all question progress and session history "
                             "for the current user. This action cannot be undone.",
                             icon='warning'):
            try:
                # Get current username from settings
                username = self.username_var.get()
                
                # Run in a separate thread to avoid UI freeze
                def reset_thread():
                    with self.data_manager.conn_lock:  # Use lock for thread safety
                        cursor = self.data_manager.conn.cursor()
                        
                        # If username is set, only reset that user's progress
                        if username:
                            # Placeholder for username-specific reset
                            # In the current implementation, we don't have user-specific tables
                            # This would need to be expanded if user-specific progress is implemented
                            messagebox.showinfo("Information", 
                                             "Multiple user support not fully implemented. "
                                             "Resetting all progress.")
                            self._reset_all_tables()
                        else:
                            # If no username set, reset all progress
                            self._reset_all_tables()
                            
                        self.data_manager.conn.commit()
                        
                        # Update UI in main thread
                        self.after(0, lambda: messagebox.showinfo("Reset Complete", 
                                                             "User progress has been reset successfully."))
                
                threading.Thread(target=reset_thread).start()
                
            except Exception as e:
                logger.error(f"Error resetting user progress: {e}", exc_info=True)
                messagebox.showerror("Reset Error", 
                                  f"An error occurred while resetting progress: {str(e)}")
    
    def _reset_all_users_progress(self):
        """Reset progress for all users."""
        if messagebox.askyesno("Reset All Progress",
                             "Are you sure you want to reset ALL progress for ALL users?\n\n"
                             "This will remove ALL question progress and session history. "
                             "This action cannot be undone.",
                             icon='warning'):
            try:
                # Run in a separate thread to avoid UI freeze
                def reset_thread():
                    # Reset all tables
                    self._reset_all_tables()
                    
                    # Update UI in main thread
                    self.after(0, lambda: messagebox.showinfo("Reset Complete", 
                                                         "All progress has been reset successfully."))
                
                threading.Thread(target=reset_thread).start()
                
            except Exception as e:
                logger.error(f"Error resetting all progress: {e}", exc_info=True)
                messagebox.showerror("Reset Error", 
                                  f"An error occurred while resetting progress: {str(e)}")
    
    def _reset_all_tables(self):
        """Reset all database tables."""
        with self.data_manager.conn_lock:  # Use lock for thread safety
            cursor = self.data_manager.conn.cursor()
            
            # Clear question progress
            cursor.execute("DELETE FROM question_progress")
            
            # Clear topic progress
            cursor.execute("DELETE FROM topic_progress")
            
            # Clear learning sessions
            cursor.execute("DELETE FROM learning_sessions")
            
            # Don't clear subjects_scripts table as that's structural metadata
            
            # Update topic progress with zeros
            # Refresh topic progress table with current topics but zero progress
            topics = self.data_manager.get_all_topics()
            for topic in topics:
                # Count questions for this topic
                count = 0
                for q in self.data_manager.get_all_questions().values():
                    if topic in q.get('topics', []):
                        count += 1
                
                # Insert or update topic in topic_progress
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO topic_progress 
                    (topic_name, total_questions, correct_answers, mastery_percentage)
                    VALUES (?, ?, 0, 0)
                    """,
                    (topic, count)
                )
            
            self.data_manager.conn.commit()
    
    def _open_questions_folder(self):
        """Open the questions folder in file explorer."""
        folder_path = os.path.join(self.data_manager.base_dir, 'data', 'questions')
        
        # Ensure the folder exists
        os.makedirs(folder_path, exist_ok=True)
        
        # Open folder based on operating system
        try:
            if platform.system() == 'Windows':
                os.startfile(folder_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', folder_path])
            else:  # Linux and other Unix-like
                subprocess.Popen(['xdg-open', folder_path])
                
            logger.info(f"Opened questions folder: {folder_path}")
            
        except Exception as e:
            logger.error(f"Error opening questions folder: {e}", exc_info=True)
            messagebox.showerror("Error", 
                              f"Could not open folder: {str(e)}\n\nPath: {folder_path}")
    
    def _delete_all_questions(self):
        """Delete all questions from the questions folder."""
        if messagebox.askyesno("Delete All Questions",
                             "Are you sure you want to delete ALL question files?\n\n"
                             "This will remove all question files from the questions folder. "
                             "This action cannot be undone.",
                             icon='warning'):
            try:
                folder_path = os.path.join(self.data_manager.base_dir, 'data', 'questions')
                
                # Get list of question files
                files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
                
                if not files:
                    messagebox.showinfo("No Questions", 
                                      "No question files found in the questions folder.")
                    return
                
                # Delete each file
                for file in files:
                    file_path = os.path.join(folder_path, file)
                    os.remove(file_path)
                
                # Clear the questions cache and reload data
                self.data_manager.refresh_all_data()
                
                # Notify main window to refresh UI components
                self._notify_main_window_refresh()
                
                messagebox.showinfo("Questions Deleted", 
                                 f"Successfully deleted {len(files)} question files.")
                
                logger.info(f"Deleted {len(files)} question files from {folder_path}")
                
            except Exception as e:
                logger.error(f"Error deleting questions: {e}", exc_info=True)
                messagebox.showerror("Delete Error", 
                                  f"An error occurred while deleting questions: {str(e)}")
                
    def _notify_main_window_refresh(self):
        """Notify the main window to refresh UI components."""
        # Find the main window instance
        parent = self
        while parent.master:
            parent = parent.master
            if hasattr(parent, '_update_home_screen'):
                # If this is the main window, refresh its UI
                parent._update_home_screen()
                parent._load_topics()
                parent._load_subjects_and_scripts()
                break
    
    def _backup_database(self):
        """Create a backup of the database."""
        try:
            # Use the DataManager's backup function
            file_path = filedialog.asksaveasfilename(
                title="Backup Database",
                defaultextension=".db",
                filetypes=[("Database files", "*.db"), ("All files", "*.*")]
            )
            
            if not file_path:
                return
                
            success, message, backup_path = self.data_manager.backup_database(file_path)
            
            if success:
                messagebox.showinfo("Backup Successful", message)
            else:
                messagebox.showerror("Backup Failed", message)
                
        except Exception as e:
            logger.error(f"Error backing up database: {e}", exc_info=True)
            messagebox.showerror("Backup Error", 
                              f"An error occurred while backing up the database: {str(e)}")