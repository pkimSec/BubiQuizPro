#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BubiQuizPro - Main Window UI Component

This module implements the main application window and UI components.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging
import os
import sys
import time
from datetime import datetime
import threading

logger = logging.getLogger(__name__)

# Import UI components
from ui.question_frame import QuestionFrame
from ui.stats_frame import StatsFrame
from ui.settings_frame import SettingsFrame

class MainWindow:
    """
    Main application window class for BubiQuizPro.
    """
    
    def __init__(self, root, data_manager, quiz_engine, stats_manager):
        """
        Initialize the main window.
        
        Args:
            root: Tkinter root window
            data_manager: DataManager instance
            quiz_engine: QuizEngine instance
            stats_manager: StatsManager instance
        """
        self.root = root
        self.data_manager = data_manager
        self.quiz_engine = quiz_engine
        self.stats_manager = stats_manager
        
        # Set application theme
        self._set_theme()
        
        # Create main frame structure
        self._create_ui()
        
        # Initialize the UI with data
        self._init_ui_data()
        
        # Add window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        logger.info("MainWindow initialized")
    
    def _set_theme(self):
        """Set the application theme and style."""
        style = ttk.Style()
        
        # Try to use a modern theme if available
        try:
            style.theme_use('clam')  # Alternatives: 'alt', 'default', 'classic'
        except tk.TclError:
            pass  # Fall back to default theme
        
        # Configure common styles
        style.configure('TFrame', background='#f0f0f0')
        style.configure('TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('TButton', font=('Arial', 10))
        style.configure('Heading.TLabel', font=('Arial', 12, 'bold'))
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'))
        
        # Sidebar style
        style.configure('Sidebar.TFrame', background='#3a4750')
        style.configure('Sidebar.TLabel', background='#3a4750', foreground='white', font=('Arial', 10))
        style.configure('Sidebar.TButton', font=('Arial', 10), background='#4a5a68')
        
        # Content area style
        style.configure('Content.TFrame', background='#f8f9fa')
        
        # Status bar style
        style.configure('StatusBar.TFrame', background='#e8e8e8')
        style.configure('StatusBar.TLabel', background='#e8e8e8', font=('Arial', 9))
        
        # Button styles
        style.configure('Primary.TButton', font=('Arial', 10, 'bold'), background='#3498db')
        style.configure('Success.TButton', font=('Arial', 10), background='#2ecc71')
        style.configure('Warning.TButton', font=('Arial', 10), background='#f39c12')
        style.configure('Danger.TButton', font=('Arial', 10), background='#e74c3c')
    
    def _create_ui(self):
        """Create the main UI structure."""
        # Configure grid layout for the root window
        self.root.grid_columnconfigure(0, weight=0)  # Sidebar
        self.root.grid_columnconfigure(1, weight=1)  # Content area
        self.root.grid_rowconfigure(0, weight=1)     # Main content
        self.root.grid_rowconfigure(1, weight=0)     # Status bar
        
        # Create sidebar
        self.sidebar = ttk.Frame(self.root, style='Sidebar.TFrame', width=200)
        self.sidebar.grid(row=0, column=0, sticky='nsew')
        self.sidebar.grid_propagate(False)  # Prevent resizing
        
        # Create content area
        self.content_frame = ttk.Frame(self.root, style='Content.TFrame')
        self.content_frame.grid(row=0, column=1, sticky='nsew')
        
        # Create status bar
        self.status_bar = ttk.Frame(self.root, style='StatusBar.TFrame', height=25)
        self.status_bar.grid(row=1, column=0, columnspan=2, sticky='ew')
        
        # Build sidebar content
        self._build_sidebar()
        
        # Build status bar content
        self._build_status_bar()
        
        # Create content frames
        self._create_content_frames()
        
        # Show home frame by default
        self._show_frame('home')
    
    def _build_sidebar(self):
        """Build the sidebar with navigation buttons."""
        # Add logo/title
        logo_frame = ttk.Frame(self.sidebar, style='Sidebar.TFrame')
        logo_frame.pack(fill='x', padx=10, pady=10)
        
        title_label = ttk.Label(logo_frame, text="BubiQuizPro", 
                             style='Sidebar.TLabel', font=('Arial', 14, 'bold'))
        title_label.pack(pady=5)
        
        version_label = ttk.Label(logo_frame, text="v1.0", 
                               style='Sidebar.TLabel', font=('Arial', 8))
        version_label.pack()
        
        # Add separator
        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', padx=10, pady=10)
        
        # Navigation buttons
        nav_frame = ttk.Frame(self.sidebar, style='Sidebar.TFrame')
        nav_frame.pack(fill='x', padx=5, pady=5)
        
        # Define navigation buttons
        nav_buttons = [
            ("Home", lambda: self._show_frame('home')),
            ("Start Quiz", lambda: self._show_frame('quiz_setup')),
            ("Statistics", lambda: self._show_frame('stats')),
            ("Settings", lambda: self._show_frame('settings')),
            ("Import/Export", lambda: self._show_frame('import_export'))
        ]
        
        # Create buttons
        self.nav_buttons = {}
        for text, command in nav_buttons:
            btn = ttk.Button(nav_frame, text=text, command=command, width=20)
            btn.pack(pady=3)
            self.nav_buttons[text.lower()] = btn
        
        # Add separators and additional info at the bottom
        ttk.Separator(self.sidebar, orient='horizontal').pack(fill='x', padx=10, pady=10)
        
        # Add spacer
        spacer = ttk.Frame(self.sidebar, style='Sidebar.TFrame')
        spacer.pack(fill='both', expand=True)
        
        # Add help button at bottom
        help_btn = ttk.Button(self.sidebar, text="Help", 
                           command=self._show_help, width=20)
        help_btn.pack(pady=10, padx=5)
    
    def _build_status_bar(self):
        """Build the status bar with information."""
        # Status message
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(self.status_bar, textvariable=self.status_var, 
                              style='StatusBar.TLabel')
        status_label.pack(side='left', padx=10)
        
        # Add current time to status bar
        self.time_var = tk.StringVar()
        time_label = ttk.Label(self.status_bar, textvariable=self.time_var, 
                            style='StatusBar.TLabel')
        time_label.pack(side='right', padx=10)
        
        # Update time periodically
        self._update_time()
    
    def _update_time(self):
        """Update the time displayed in the status bar."""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_var.set(current_time)
        # Schedule to update every second
        self.root.after(1000, self._update_time)
    
    def _create_content_frames(self):
        """Create all content frames."""
        self.frames = {}
        
        # Home frame
        self.frames['home'] = self._create_home_frame()
        
        # Quiz setup frame
        self.frames['quiz_setup'] = self._create_quiz_setup_frame()
        
        # Active quiz frame
        self.frames['quiz_active'] = QuestionFrame(
            self.content_frame, 
            self.quiz_engine,
            self._on_quiz_end
        )
        
        # Statistics frame
        self.frames['stats'] = StatsFrame(
            self.content_frame, 
            self.stats_manager,
            self.data_manager
        )
        
        # Settings frame
        self.frames['settings'] = SettingsFrame(
            self.content_frame,
            self.data_manager
        )
        
        # Import/Export frame
        self.frames['import_export'] = self._create_import_export_frame()
    
    def _create_home_frame(self):
        """Create the home screen frame."""
        frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        
        # Welcome message
        welcome_label = ttk.Label(frame, text="Welcome to BubiQuizPro", 
                               style='Title.TLabel', font=('Arial', 24, 'bold'))
        welcome_label.pack(pady=20)
        
        # Dashboard area
        dashboard = ttk.Frame(frame, style='Content.TFrame')
        dashboard.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Configure grid
        dashboard.columnconfigure((0, 1, 2), weight=1, uniform='column')
        dashboard.rowconfigure((0, 1), weight=1, uniform='row')
        
        # Statistics summary
        stats_frame = ttk.LabelFrame(dashboard, text="Learning Statistics", padding=10)
        stats_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        
        self.home_stats_labels = {}
        stats_data = [
            ("Total Questions:", "questions", "0"),
            ("Questions Answered:", "answered", "0"),
            ("Overall Accuracy:", "accuracy", "0%"),
            ("Topics Mastered:", "mastered", "0/0")
        ]
        
        for i, (label_text, key, default) in enumerate(stats_data):
            label = ttk.Label(stats_frame, text=label_text)
            label.grid(row=i, column=0, sticky='w', pady=3)
            
            value = ttk.Label(stats_frame, text=default)
            value.grid(row=i, column=1, sticky='e', pady=3)
            
            self.home_stats_labels[key] = value
        
        # Recent sessions
        sessions_frame = ttk.LabelFrame(dashboard, text="Recent Sessions", padding=10)
        sessions_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        
        self.recent_sessions_list = tk.Listbox(sessions_frame, height=6)
        self.recent_sessions_list.pack(fill='both', expand=True)
        
        # Quick actions
        actions_frame = ttk.LabelFrame(dashboard, text="Quick Actions", padding=10)
        actions_frame.grid(row=0, column=2, padx=10, pady=10, sticky='nsew')
        
        # Quick action buttons
        quick_buttons = [
            ("Start New Quiz", lambda: self._show_frame('quiz_setup')),
            ("Review Weak Spots", lambda: self._start_quick_quiz('weak_spots')),
            ("Resume Learning", lambda: self._start_quick_quiz('spaced_repetition')),
            ("View Statistics", lambda: self._show_frame('stats'))
        ]
        
        for i, (text, command) in enumerate(quick_buttons):
            btn = ttk.Button(actions_frame, text=text, command=command)
            btn.pack(fill='x', pady=5)
        
        # Topic overview
        topics_frame = ttk.LabelFrame(dashboard, text="Topic Mastery Overview", padding=10)
        topics_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky='nsew')
        
        # Topic progress will be populated in _init_ui_data
        self.topics_frame = topics_frame
        
        return frame
    
    def _create_quiz_setup_frame(self):
        """Create the quiz setup frame."""
        frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        
        # Title
        title_label = ttk.Label(frame, text="Quiz Setup", 
                             style='Title.TLabel', font=('Arial', 18, 'bold'))
        title_label.pack(pady=(20, 10))
        
        # Setup form
        form_frame = ttk.Frame(frame, style='Content.TFrame', padding=20)
        form_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Quiz mode
        mode_frame = ttk.LabelFrame(form_frame, text="Quiz Mode", padding=10)
        mode_frame.pack(fill='x', pady=10)
        
        self.quiz_mode = tk.StringVar(value="normal")
        
        modes = [
            ("Normal Quiz", "normal", "Answer questions based on your selection"),
            ("Weak Spots", "weak_spots", "Focus on questions you've had trouble with"),
            ("Spaced Repetition", "spaced_repetition", "Optimized for long-term learning"),
            ("Exam Mode", "exam", "Simulate an exam with time limit")
        ]
        
        for text, value, description in modes:
            mode_option = ttk.Frame(mode_frame)
            mode_option.pack(fill='x', pady=3)
            
            radio = ttk.Radiobutton(mode_option, text=text, value=value, 
                                  variable=self.quiz_mode)
            radio.pack(side='left')
            
            desc_label = ttk.Label(mode_option, text=description, font=('Arial', 9, 'italic'))
            desc_label.pack(side='right')
        
        # Filters section
        filters_frame = ttk.LabelFrame(form_frame, text="Filters", padding=10)
        filters_frame.pack(fill='x', pady=10)
        
        # Configure grid for filters
        filters_frame.columnconfigure(0, weight=0)
        filters_frame.columnconfigure(1, weight=1)
        
        # Subject filter
        ttk.Label(filters_frame, text="Subject:").grid(row=0, column=0, sticky='w', pady=5)
        self.subject_var = tk.StringVar()
        self.subject_combo = ttk.Combobox(filters_frame, textvariable=self.subject_var)
        self.subject_combo.grid(row=0, column=1, sticky='ew', pady=5, padx=5)
        self.subject_combo.bind('<<ComboboxSelected>>', self._update_scripts_list)
        
        # Script filter
        ttk.Label(filters_frame, text="Script:").grid(row=1, column=0, sticky='w', pady=5)
        self.script_var = tk.StringVar()
        self.script_combo = ttk.Combobox(filters_frame, textvariable=self.script_var)
        self.script_combo.grid(row=1, column=1, sticky='ew', pady=5, padx=5)
        
        # Topic filter
        ttk.Label(filters_frame, text="Topics:").grid(row=2, column=0, sticky='w', pady=5)
        
        topics_select_frame = ttk.Frame(filters_frame)
        topics_select_frame.grid(row=2, column=1, sticky='ew', pady=5, padx=5)
        
        self.topics_listbox = tk.Listbox(topics_select_frame, height=5, selectmode='multiple')
        self.topics_listbox.pack(side='left', fill='both', expand=True)
        
        topics_scroll = ttk.Scrollbar(topics_select_frame, orient='vertical', 
                                    command=self.topics_listbox.yview)
        topics_scroll.pack(side='right', fill='y')
        self.topics_listbox.config(yscrollcommand=topics_scroll.set)
        
        # Difficulty filter
        ttk.Label(filters_frame, text="Difficulty:").grid(row=3, column=0, sticky='w', pady=5)
        self.difficulty_var = tk.StringVar()
        difficulty_options = ['Any', 'leicht', 'mittel', 'schwer']
        difficulty_combo = ttk.Combobox(filters_frame, textvariable=self.difficulty_var, 
                                      values=difficulty_options, state='readonly')
        difficulty_combo.grid(row=3, column=1, sticky='ew', pady=5, padx=5)
        difficulty_combo.current(0)
        
        # Quiz options section
        options_frame = ttk.LabelFrame(form_frame, text="Quiz Options", padding=10)
        options_frame.pack(fill='x', pady=10)
        
        # Configure grid for options
        options_frame.columnconfigure(0, weight=0)
        options_frame.columnconfigure(1, weight=1)
        
        # Number of questions
        ttk.Label(options_frame, text="Number of Questions:").grid(row=0, column=0, sticky='w', pady=5)
        self.question_count_var = tk.IntVar(value=10)
        question_count_spin = ttk.Spinbox(options_frame, from_=1, to=100, 
                                        textvariable=self.question_count_var, width=5)
        question_count_spin.grid(row=0, column=1, sticky='w', pady=5, padx=5)
        
        # Time limit
        ttk.Label(options_frame, text="Time Limit (minutes):").grid(row=1, column=0, sticky='w', pady=5)
        self.time_limit_var = tk.IntVar(value=0)
        time_limit_spin = ttk.Spinbox(options_frame, from_=0, to=180, 
                                    textvariable=self.time_limit_var, width=5)
        time_limit_spin.grid(row=1, column=1, sticky='w', pady=5, padx=5)
        ttk.Label(options_frame, text="(0 = no time limit)").grid(row=1, column=1, sticky='e', pady=5)
        
        # Buttons
        buttons_frame = ttk.Frame(form_frame, style='Content.TFrame')
        buttons_frame.pack(fill='x', pady=20)
        
        ttk.Button(buttons_frame, text="Cancel", 
                command=lambda: self._show_frame('home')).pack(side='left', padx=5)
        
        ttk.Button(buttons_frame, text="Start Quiz", style='Primary.TButton',
                command=self._start_quiz).pack(side='right', padx=5)
        
        return frame
    
    def _create_import_export_frame(self):
        """Create the import/export frame."""
        frame = ttk.Frame(self.content_frame, style='Content.TFrame')
        
        # Title
        title_label = ttk.Label(frame, text="Import & Export", 
                             style='Title.TLabel', font=('Arial', 18, 'bold'))
        title_label.pack(pady=(20, 10))
        
        # Main content
        content_frame = ttk.Frame(frame, style='Content.TFrame', padding=20)
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Import section
        import_frame = ttk.LabelFrame(content_frame, text="Import Questions", padding=10)
        import_frame.pack(fill='x', pady=10)
        
        import_desc = ttk.Label(import_frame, 
                             text="Import question files in JSON format.")
        import_desc.pack(anchor='w', pady=5)
        
        import_btn = ttk.Button(import_frame, text="Import JSON File", 
                             command=self._import_questions)
        import_btn.pack(anchor='w', pady=5)
        
        # Export section
        export_frame = ttk.LabelFrame(content_frame, text="Export", padding=10)
        export_frame.pack(fill='x', pady=10)
        
        # Anki export
        anki_frame = ttk.Frame(export_frame)
        anki_frame.pack(fill='x', pady=5)
        
        anki_label = ttk.Label(anki_frame, text="Export to Anki format:")
        anki_label.pack(side='left', padx=5)
        
        anki_btn = ttk.Button(anki_frame, text="Export Selected Topics", 
                           command=self._export_anki)
        anki_btn.pack(side='right', padx=5)
        
        # Add topic selection for export
        topics_frame = ttk.Frame(export_frame)
        topics_frame.pack(fill='x', pady=5)
        
        ttk.Label(topics_frame, text="Select topics to export:").pack(anchor='w', pady=2)
        
        topics_select_frame = ttk.Frame(topics_frame)
        topics_select_frame.pack(fill='x', pady=2)
        
        self.export_topics_listbox = tk.Listbox(topics_select_frame, height=5, selectmode='multiple')
        self.export_topics_listbox.pack(side='left', fill='both', expand=True)
        
        topics_scroll = ttk.Scrollbar(topics_select_frame, orient='vertical', 
                                    command=self.export_topics_listbox.yview)
        topics_scroll.pack(side='right', fill='y')
        self.export_topics_listbox.config(yscrollcommand=topics_scroll.set)
        
        # Statistics export
        stats_frame = ttk.Frame(export_frame)
        stats_frame.pack(fill='x', pady=5)
        
        stats_label = ttk.Label(stats_frame, text="Export statistics report:")
        stats_label.pack(side='left', padx=5)
        
        stats_btn = ttk.Button(stats_frame, text="Export PDF Report", 
                            command=self._export_stats)
        stats_btn.pack(side='right', padx=5)
        
        # Database backup
        backup_frame = ttk.Frame(export_frame)
        backup_frame.pack(fill='x', pady=5)
        
        backup_label = ttk.Label(backup_frame, text="Create database backup:")
        backup_label.pack(side='left', padx=5)
        
        backup_btn = ttk.Button(backup_frame, text="Backup Database", 
                             command=self._backup_database)
        backup_btn.pack(side='right', padx=5)
        
        return frame
    
    def _init_ui_data(self):
        """Initialize UI with data from database."""
        # Load subjects
        self._load_subjects_and_scripts()
        
        # Load topics for both quiz setup and export
        self._load_topics()
        
        # Update home screen data
        self._update_home_screen()
    
    def _load_subjects_and_scripts(self):
        """Load subjects and scripts from database."""
        # Get subjects
        subjects = self.data_manager.get_subjects()
        
        # Add 'All' option
        subjects = ['All'] + subjects
        
        # Update combobox
        self.subject_combo['values'] = subjects
        if subjects:
            self.subject_combo.current(0)
    
    def _update_scripts_list(self, event=None):
        """Update the scripts list based on selected subject."""
        selected_subject = self.subject_var.get()
        
        if selected_subject == 'All':
            # Get all scripts
            scripts = []
            for subject in self.data_manager.get_subjects():
                scripts.extend(self.data_manager.get_scripts_for_subject(subject))
        else:
            # Get scripts for selected subject
            scripts = self.data_manager.get_scripts_for_subject(selected_subject)
        
        # Add 'All' option
        scripts = ['All'] + scripts
        
        # Update combobox
        self.script_combo['values'] = scripts
        if scripts:
            self.script_combo.current(0)
    
    def _load_topics(self):
        """Load topics from database."""
        # Get all topics
        topics = sorted(self.data_manager.get_all_topics())
        
        # Clear existing items
        self.topics_listbox.delete(0, tk.END)
        self.export_topics_listbox.delete(0, tk.END)
        
        # Add topics to listboxes
        for topic in topics:
            self.topics_listbox.insert(tk.END, topic)
            self.export_topics_listbox.insert(tk.END, topic)
    
    def _update_home_screen(self):
        """Update home screen with latest data."""
        # Update statistics labels
        overall_stats = self.stats_manager.get_overall_stats()
        
        if overall_stats:
            total_q = len(self.data_manager.get_all_questions())
            self.home_stats_labels['questions'].config(text=str(total_q))
            
            total_answered = overall_stats.get('total_questions_answered', 0)
            self.home_stats_labels['answered'].config(text=str(total_answered))
            
            accuracy = overall_stats.get('overall_accuracy', 0)
            self.home_stats_labels['accuracy'].config(text=f"{accuracy:.1f}%")
            
            topics_mastered = overall_stats.get('topics_mastered', 0)
            topics_count = overall_stats.get('topics_count', 0)
            self.home_stats_labels['mastered'].config(text=f"{topics_mastered}/{topics_count}")
        
        # Update recent sessions list
        self.recent_sessions_list.delete(0, tk.END)
        sessions = self.data_manager.get_learning_sessions(limit=5)
        
        for session in sessions:
            date = session.get('date', '').split('T')[0]  # Extract date part
            questions = session.get('questions_answered', 0)
            correct = session.get('correct_answers', 0)
            accuracy = (correct / questions * 100) if questions > 0 else 0
            
            self.recent_sessions_list.insert(
                tk.END, 
                f"{date}: {questions} questions, {accuracy:.1f}% accuracy"
            )
        
        # Update topic mastery overview
        # First, clear the frame
        for widget in self.topics_frame.winfo_children():
            widget.destroy()
        
        # Get topic mastery data
        topic_mastery = self.stats_manager.get_topic_mastery()
        
        # Sort topics by mastery
        sorted_topics = sorted(topic_mastery.items(), key=lambda x: x[1], reverse=True)
        
        # Display top 5 topics with progress bars
        display_topics = sorted_topics[:5]
        
        for i, (topic, mastery) in enumerate(display_topics):
            topic_frame = ttk.Frame(self.topics_frame)
            topic_frame.pack(fill='x', pady=2)
            
            topic_label = ttk.Label(topic_frame, text=topic, width=20, anchor='w')
            topic_label.pack(side='left', padx=5)
            
            # Create a progress bar
            progress_var = tk.DoubleVar(value=mastery)
            progress_bar = ttk.Progressbar(topic_frame, variable=progress_var, 
                                        maximum=100, length=200)
            progress_bar.pack(side='left', padx=5, fill='x', expand=True)
            
            mastery_label = ttk.Label(topic_frame, text=f"{mastery:.1f}%", width=6)
            mastery_label.pack(side='right', padx=5)
    
    def _show_frame(self, frame_name):
        """Show a specific content frame."""
        # Hide all frames
        for frame in self.frames.values():
            frame.pack_forget()
        
        # Show the requested frame
        if frame_name in self.frames:
            self.frames[frame_name].pack(fill='both', expand=True)
            
            # Update status
            self.status_var.set(f"Viewing: {frame_name.replace('_', ' ').title()}")
            
            # If showing home, update the data
            if frame_name == 'home':
                self._update_home_screen()
            
            # Special handling for certain frames
            if frame_name == 'stats':
                # Refresh stats data
                self.frames['stats'].refresh_data()
            
            logger.debug(f"Showing frame: {frame_name}")
        else:
            logger.error(f"Unknown frame name: {frame_name}")
    
    def _start_quiz(self):
        """Start a quiz based on user selections."""
        # Get selected mode
        mode = self.quiz_mode.get()
        
        # Get filters
        selected_subject = self.subject_var.get()
        subject = None if selected_subject == 'All' else selected_subject
        
        selected_script = self.script_var.get()
        script = None if selected_script == 'All' else selected_script
        
        # Get selected topics
        selected_indices = self.topics_listbox.curselection()
        topics = None
        if selected_indices:
            topics = [self.topics_listbox.get(i) for i in selected_indices]
        
        # Get difficulty
        difficulty = self.difficulty_var.get()
        difficulty = None if difficulty == 'Any' else difficulty
        
        # Get question type (if defined in UI)
        question_type = None
        if hasattr(self, 'question_type_var'):
            question_type = self.question_type_var.get()
            if question_type == 'Any':
                question_type = None
        
        # Get question count and time limit
        question_count = self.question_count_var.get()
        time_limit = self.time_limit_var.get() or None  # 0 becomes None (no limit)
        
        # Start the quiz session
        self.quiz_engine.start_session(
            mode=mode,
            topics=topics,
            difficulty=difficulty,
            subject=subject,
            script=script,
            question_type=question_type,
            question_count=question_count,
            time_limit=time_limit
        )
        
        # Load first question into the question frame
        self.frames['quiz_active'].load_first_question()
        
        # Show the quiz frame
        self._show_frame('quiz_active')
        
        # Update status
        self.status_var.set(f"Quiz started: {mode} mode")
        
        logger.info(f"Started quiz: mode={mode}, topics={topics}, difficulty={difficulty}, question_type={question_type}")
    
    def _start_quick_quiz(self, mode):
        """Start a quick quiz with default settings."""
        # Set defaults based on mode
        question_count = 10
        time_limit = None
        
        # Start the quiz session
        self.quiz_engine.start_session(
            mode=mode,
            question_count=question_count,
            time_limit=time_limit,
            question_type=None  # Allow both question types
        )
        
        # Load first question into the question frame
        self.frames['quiz_active'].load_first_question()
        
        # Show the quiz frame
        self._show_frame('quiz_active')
        
        # Update status
        self.status_var.set(f"Quick quiz started: {mode} mode")
        
        logger.info(f"Started quick quiz: mode={mode}")
    
    def _on_quiz_end(self, results):
        """Handle quiz end event."""
        # Switch back to home screen
        self._show_frame('home')
        
        # Update status
        self.status_var.set("Quiz completed")
        
        # Show results summary
        if results:
            accuracy = results.get('accuracy', 0)
            questions = results.get('questions_answered', 0)
            correct = results.get('correct_answers', 0)
            
            messagebox.showinfo(
                "Quiz Results",
                f"Quiz completed!\n\n"
                f"Questions answered: {questions}\n"
                f"Correct answers: {correct}\n"
                f"Accuracy: {accuracy:.1f}%"
            )
        
        logger.info("Quiz ended")
    
    def _import_questions(self):
        """Import questions from a JSON file."""
        # Open file dialog
        file_path = filedialog.askopenfilename(
            title="Import Questions",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Show progress
        self.status_var.set("Importing questions...")
        self.root.update_idletasks()
        
        # Import in a separate thread to avoid freezing UI
        def import_thread():
            success, message, count = self.data_manager.import_questions(file_path)
            
            # Update UI in the main thread
            self.root.after(0, lambda: self._on_import_complete(success, message, count))
        
        threading.Thread(target=import_thread).start()
    
    def _on_import_complete(self, success, message, count):
        """Handle import completion."""
        if success:
            messagebox.showinfo("Import Successful", message)
            
            # Reload topics
            self._load_topics()
            
            # Reload subjects and scripts
            self._load_subjects_and_scripts()
            
            # Update home screen
            self._update_home_screen()
        else:
            messagebox.showerror("Import Failed", message)
        
        # Update status
        self.status_var.set("Ready")
    
    def _export_anki(self):
        """Export selected topics to Anki format."""
        # Get selected topics
        selected_indices = self.export_topics_listbox.curselection()
        
        if not selected_indices:
            messagebox.showwarning("No Topics Selected", 
                                "Please select at least one topic to export.")
            return
        
        topics = [self.export_topics_listbox.get(i) for i in selected_indices]
        
        # Open save dialog
        file_path = filedialog.asksaveasfilename(
            title="Export to Anki",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Show progress
        self.status_var.set("Exporting to Anki format...")
        self.root.update_idletasks()
        
        # Get all questions with the selected topics
        questions = self.data_manager.get_filtered_questions(topics=topics)
        
        # Export to Anki
        success, message, export_path = self.data_manager.export_questions_to_anki(
            question_ids=list(questions.keys()),
            output_file=file_path
        )
        
        if success:
            messagebox.showinfo("Export Successful", message)
        else:
            messagebox.showerror("Export Failed", message)
        
        # Update status
        self.status_var.set("Ready")
    
    def _export_stats(self):
        """Export statistics to PDF."""
        # Open save dialog
        file_path = filedialog.asksaveasfilename(
            title="Export Statistics",
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Show progress
        self.status_var.set("Generating statistics report...")
        self.root.update_idletasks()
        
        # Export in a separate thread to avoid freezing UI
        def export_thread():
            success, message, export_path = self.stats_manager.export_report_pdf(file_path)
            
            # Update UI in the main thread
            self.root.after(0, lambda: self._on_export_complete(success, message))
        
        threading.Thread(target=export_thread).start()
    
    def _on_export_complete(self, success, message):
        """Handle export completion."""
        if success:
            messagebox.showinfo("Export Successful", message)
        else:
            messagebox.showerror("Export Failed", message)
        
        # Update status
        self.status_var.set("Ready")
    
    def _backup_database(self):
        """Backup the database."""
        # Open save dialog
        file_path = filedialog.asksaveasfilename(
            title="Backup Database",
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        # Show progress
        self.status_var.set("Creating database backup...")
        self.root.update_idletasks()
        
        # Create backup
        success, message, backup_path = self.data_manager.backup_database(file_path)
        
        if success:
            messagebox.showinfo("Backup Successful", message)
        else:
            messagebox.showerror("Backup Failed", message)
        
        # Update status
        self.status_var.set("Ready")
    
    def _show_help(self):
        """Show help information."""
        help_text = """
        BubiQuizPro Help
        
        - Home: View summary statistics and quick actions
        - Start Quiz: Configure and start a new quiz session
        - Statistics: View detailed learning statistics
        - Settings: Configure application settings
        - Import/Export: Import questions and export data
        
        For more detailed help, please refer to the documentation.
        """
        
        messagebox.showinfo("Help", help_text)
    
    def _on_closing(self):
        """Handle window closing event."""
        try:
            # End quiz session if active
            if self.quiz_engine.is_session_active():
                self.quiz_engine.end_session()
            
            # Close data manager
            self.data_manager.close()
            
            logger.info("Application closed properly")
            
        except Exception as e:
            logger.error(f"Error during application closing: {e}", exc_info=True)
        
        # Destroy the window
        self.root.destroy()