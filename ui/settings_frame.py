#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BubiQuizPro - Settings Frame UI Component

This module implements the UI component for application settings.
"""

import tkinter as tk
from tkinter import ttk, messagebox, colorchooser
import logging
import os
import json

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
                             command=self._create_backup)
        backup_btn.grid(row=2, column=0, sticky='w', pady=10, padx=5)
        
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
        
        # General settings
        self.settings['general'] = {
            'username': self.username_var.get(),
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
    
    def _create_backup(self):
        """Create a backup of the database."""
        success, message, file_path = self.data_manager.backup_database()
        
        if success:
            messagebox.showinfo("Backup Created", message)
        else:
            messagebox.showerror("Backup Failed", message)