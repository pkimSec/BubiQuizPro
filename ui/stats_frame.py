#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BubiQuizPro - Statistics Frame UI Component

This module implements the UI component for displaying learning statistics.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import threading
from PIL import Image, ImageTk
import io

logger = logging.getLogger(__name__)

class StatsFrame(ttk.Frame):
    """
    Frame for displaying learning statistics and progress.
    """
    
    def __init__(self, parent, stats_manager, data_manager):
        """
        Initialize the statistics frame.
        
        Args:
            parent: Parent widget
            stats_manager: StatsManager instance
            data_manager: DataManager instance
        """
        super().__init__(parent, style='Content.TFrame')
        
        self.stats_manager = stats_manager
        self.data_manager = data_manager
        
        self.chart_images = {}  # Store for chart images
        
        # Create UI components
        self._create_ui()
        
        logger.info("StatsFrame initialized")
    
    def _create_ui(self):
        """Create the UI components."""
        # Configure grid
        self.columnconfigure(0, weight=1)
        
        # Header
        header_frame = ttk.Frame(self, style='Content.TFrame')
        header_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=(20, 10))
        
        title_label = ttk.Label(header_frame, text="Learning Statistics", 
                             font=('Arial', 18, 'bold'))
        title_label.pack(side='left')
        
        refresh_btn = ttk.Button(header_frame, text="Refresh", 
                              command=self.refresh_data)
        refresh_btn.pack(side='right')
        
        # Create a notebook with tabs for different statistics
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=1, column=0, sticky='nsew', padx=20, pady=10)
        
        # Overview tab
        self.overview_frame = self._create_overview_tab()
        self.notebook.add(self.overview_frame, text="Overview")
        
        # Topics tab
        self.topics_frame = self._create_topics_tab()
        self.notebook.add(self.topics_frame, text="Topics")
        
        # Progress tab
        self.progress_frame = self._create_progress_tab()
        self.notebook.add(self.progress_frame, text="Progress")
        
        # Sessions tab
        self.sessions_frame = self._create_sessions_tab()
        self.notebook.add(self.sessions_frame, text="Sessions")
    
    def _create_overview_tab(self):
        """Create the overview tab."""
        frame = ttk.Frame(self.notebook, style='Content.TFrame', padding=10)
        
        # Summary section
        summary_frame = ttk.LabelFrame(frame, text="Summary Statistics", padding=10)
        summary_frame.pack(fill='x', pady=10)
        
        # Grid for summary statistics
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.columnconfigure(1, weight=1)
        summary_frame.columnconfigure(2, weight=1)
        
        # Create summary statistic labels
        self.summary_labels = {}
        
        # Add statistic items
        stats_items = [
            ("Total Questions", "total_questions", "0"),
            ("Questions Answered", "questions_answered", "0"),
            ("Overall Accuracy", "accuracy", "0%"),
            ("Total Learning Time", "time_spent", "0 min"),
            ("Topics Mastered", "topics_mastered", "0/0"),
            ("Active Streak", "streak", "0 days")
        ]
        
        # Create two columns of statistics
        col1_items = stats_items[:3]
        col2_items = stats_items[3:]
        
        # First column
        for i, (label, key, default) in enumerate(col1_items):
            ttk.Label(summary_frame, text=label + ":", 
                   font=('Arial', 10, 'bold')).grid(row=i, column=0, sticky='w', pady=5, padx=5)
            
            value_label = ttk.Label(summary_frame, text=default)
            value_label.grid(row=i, column=1, sticky='w', pady=5, padx=5)
            self.summary_labels[key] = value_label
        
        # Second column
        for i, (label, key, default) in enumerate(col2_items):
            ttk.Label(summary_frame, text=label + ":", 
                   font=('Arial', 10, 'bold')).grid(row=i, column=2, sticky='w', pady=5, padx=5)
            
            value_label = ttk.Label(summary_frame, text=default)
            value_label.grid(row=i, column=3, sticky='w', pady=5, padx=5)
            self.summary_labels[key] = value_label
        
        # Charts section
        charts_frame = ttk.LabelFrame(frame, text="Performance Overview", padding=10)
        charts_frame.pack(fill='both', expand=True, pady=10)
        
        # Progress chart
        self.progress_chart_label = ttk.Label(charts_frame, text="Loading chart...")
        self.progress_chart_label.pack(pady=10)
        
        return frame
    
    def _create_topics_tab(self):
        """Create the topics tab."""
        frame = ttk.Frame(self.notebook, style='Content.TFrame', padding=10)
        
        # Create a split view
        paned = ttk.PanedWindow(frame, orient='horizontal')
        paned.pack(fill='both', expand=True)
        
        # Left side: Topics list with progress bars
        left_frame = ttk.Frame(paned, style='Content.TFrame', padding=10)
        
        ttk.Label(left_frame, text="Topic Mastery", 
               font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        # Topics list with scrollbar
        topics_frame = ttk.Frame(left_frame, style='Content.TFrame')
        topics_frame.pack(fill='both', expand=True)
        
        # Create a canvas with scrollbar for the topics list
        canvas = tk.Canvas(topics_frame, borderwidth=0, highlightthickness=0)
        scrollbar = ttk.Scrollbar(topics_frame, orient="vertical", command=canvas.yview)
        self.topics_container = ttk.Frame(canvas, style='Content.TFrame')
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        canvas_window = canvas.create_window((0, 0), window=self.topics_container, anchor="nw")
        
        # Configure canvas to resize with container
        def resize_canvas(event):
            canvas.configure(scrollregion=canvas.bbox("all"), width=event.width)
        
        self.topics_container.bind("<Configure>", resize_canvas)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))
        
        # Right side: Heatmap/chart
        right_frame = ttk.Frame(paned, style='Content.TFrame', padding=10)
        
        ttk.Label(right_frame, text="Topic Heatmap", 
               font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        self.topics_chart_label = ttk.Label(right_frame, text="Loading chart...")
        self.topics_chart_label.pack(pady=10, expand=True)
        
        # Add frames to paned window
        paned.add(left_frame, weight=1)
        paned.add(right_frame, weight=2)
        
        return frame
    
    def _create_progress_tab(self):
        """Create the progress over time tab."""
        frame = ttk.Frame(self.notebook, style='Content.TFrame', padding=10)
        
        # Recent performance chart
        ttk.Label(frame, text="Learning Progress", 
               font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        self.learning_curve_label = ttk.Label(frame, text="Loading chart...")
        self.learning_curve_label.pack(pady=10)
        
        # Recent performance metrics
        metrics_frame = ttk.LabelFrame(frame, text="Recent Performance", padding=10)
        metrics_frame.pack(fill='x', pady=10)
        
        # Progress metrics grid
        metrics_frame.columnconfigure((0, 1, 2, 3), weight=1)
        
        # Labels for performance metrics
        metric_items = [
            ("Last 7 Days", "week_questions", "0 questions"),
            ("Weekly Accuracy", "week_accuracy", "0%"),
            ("Last 30 Days", "month_questions", "0 questions"),
            ("Monthly Accuracy", "month_accuracy", "0%")
        ]
        
        self.progress_labels = {}
        
        for i, (label, key, default) in enumerate(metric_items):
            ttk.Label(metrics_frame, text=label + ":", 
                   font=('Arial', 10, 'bold')).grid(row=0, column=i, padx=5, pady=5)
            
            value_label = ttk.Label(metrics_frame, text=default)
            value_label.grid(row=1, column=i, padx=5, pady=5)
            self.progress_labels[key] = value_label
        
        return frame
    
    def _create_sessions_tab(self):
        """Create the sessions history tab."""
        frame = ttk.Frame(self.notebook, style='Content.TFrame', padding=10)
        
        # Sessions list
        ttk.Label(frame, text="Session History", 
               font=('Arial', 12, 'bold')).pack(anchor='w', pady=(0, 10))
        
        # Create treeview with scrollbar
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame)
        scrollbar.pack(side='right', fill='y')
        
        # Treeview
        columns = ('date', 'duration', 'questions', 'correct', 'accuracy', 'topics')
        self.sessions_tree = ttk.Treeview(tree_frame, columns=columns, 
                                        show='headings', 
                                        yscrollcommand=scrollbar.set)
        
        # Configure scrollbar
        scrollbar.config(command=self.sessions_tree.yview)
        
        # Set column headings
        self.sessions_tree.heading('date', text='Date')
        self.sessions_tree.heading('duration', text='Duration')
        self.sessions_tree.heading('questions', text='Questions')
        self.sessions_tree.heading('correct', text='Correct')
        self.sessions_tree.heading('accuracy', text='Accuracy')
        self.sessions_tree.heading('topics', text='Topics')
        
        # Set column widths
        self.sessions_tree.column('date', width=100)
        self.sessions_tree.column('duration', width=80)
        self.sessions_tree.column('questions', width=80)
        self.sessions_tree.column('correct', width=80)
        self.sessions_tree.column('accuracy', width=80)
        self.sessions_tree.column('topics', width=300)
        
        self.sessions_tree.pack(fill='both', expand=True)
        
        return frame
    
    def refresh_data(self):
        """Refresh the displayed statistics."""
        # Show loading message
        self.set_loading_state(True)
        
        # Run data loading in a separate thread to avoid freezing UI
        threading.Thread(target=self._load_data_thread).start()
    
    def _load_data_thread(self):
        """Thread worker for loading data."""
        try:
            # Load and process data
            self._load_overview_data()
            self._load_topics_data()
            self._load_progress_data()
            self._load_sessions_data()
            
            # Update UI in main thread
            self.after(0, lambda: self.set_loading_state(False))
            
            logger.info("Statistics data refreshed")
            
        except Exception as e:
            logger.error(f"Error loading statistics data: {e}", exc_info=True)
            
            # Show error in main thread
            self.after(0, lambda: messagebox.showerror(
                "Data Loading Error",
                f"An error occurred while loading statistics: {str(e)}"
            ))
    
    def set_loading_state(self, is_loading):
        """
        Set the loading state of the UI.
        
        Args:
            is_loading (bool): Whether data is loading
        """
        if is_loading:
            # Set loading message in chart areas
            self.progress_chart_label.config(text="Loading chart...")
            self.topics_chart_label.config(text="Loading chart...")
            self.learning_curve_label.config(text="Loading chart...")
        else:
            # Clear loading messages (if charts weren't loaded)
            if 'progress' not in self.chart_images:
                self.progress_chart_label.config(text="No data available")
            
            if 'topics' not in self.chart_images:
                self.topics_chart_label.config(text="No data available")
                
            if 'learning_curve' not in self.chart_images:
                self.learning_curve_label.config(text="No data available")
    
    def _load_overview_data(self):
        """Load overview tab data."""
        # Get overall stats
        stats = self.stats_manager.get_overall_stats()
        
        if not stats:
            return
        
        # Update summary labels in main thread
        self.after(0, lambda: self._update_summary_labels(stats))
        
        # Get progress chart
        chart_data = self.stats_manager.plot_learning_curve(days=30)
        
        if chart_data:
            # Convert to tkinter image
            img = self.stats_manager.create_tk_image(chart_data, size=(800, 400))
            
            # Store reference to prevent garbage collection
            self.chart_images['progress'] = img
            
            # Update label in main thread
            self.after(0, lambda: self.progress_chart_label.config(image=img, text=""))
    
    def _update_summary_labels(self, stats):
        """
        Update the summary statistics labels.
        
        Args:
            stats (dict): Statistics data
        """
        # Update labels with data
        self.summary_labels['total_questions'].config(
            text=str(len(self.data_manager.get_all_questions()))
        )
        
        self.summary_labels['questions_answered'].config(
            text=str(stats.get('total_questions_answered', 0))
        )
        
        accuracy = stats.get('overall_accuracy', 0)
        self.summary_labels['accuracy'].config(
            text=f"{accuracy:.1f}%"
        )
        
        time_spent = stats.get('total_time_spent_minutes', 0)
        if time_spent > 60:
            time_text = f"{time_spent // 60} hrs {time_spent % 60} min"
        else:
            time_text = f"{time_spent} min"
            
        self.summary_labels['time_spent'].config(
            text=time_text
        )
        
        topics_mastered = stats.get('topics_mastered', 0)
        topics_count = stats.get('topics_count', 0)
        self.summary_labels['topics_mastered'].config(
            text=f"{topics_mastered}/{topics_count}"
        )
        
        # Calculate streak (placeholder - would need actual login tracking)
        self.summary_labels['streak'].config(
            text="0 days"
        )
    
    def _load_topics_data(self):
        """Load topics tab data."""
        # Get topic mastery data
        topic_mastery = self.stats_manager.get_topic_mastery()
        
        if not topic_mastery:
            return
        
        # Update topics list in main thread
        self.after(0, lambda: self._update_topics_list(topic_mastery))
        
        # Get topic heatmap
        chart_data = self.stats_manager.plot_topic_heatmap()
        
        if chart_data:
            # Convert to tkinter image
            img = self.stats_manager.create_tk_image(chart_data, size=(600, 500))
            
            # Store reference to prevent garbage collection
            self.chart_images['topics'] = img
            
            # Update label in main thread
            self.after(0, lambda: self.topics_chart_label.config(image=img, text=""))
    
    def _update_topics_list(self, topic_mastery):
        """
        Update the topics list with progress bars.
        
        Args:
            topic_mastery (dict): Topic mastery percentages
        """
        # Clear existing topic items
        for widget in self.topics_container.winfo_children():
            widget.destroy()
        
        # Sort topics by mastery (highest first)
        sorted_topics = sorted(topic_mastery.items(), key=lambda x: x[1], reverse=True)
        
        # Add topic items with progress bars
        for i, (topic, mastery) in enumerate(sorted_topics):
            topic_frame = ttk.Frame(self.topics_container)
            topic_frame.pack(fill='x', pady=2)
            
            topic_label = ttk.Label(topic_frame, text=topic, width=25, anchor='w')
            topic_label.pack(side='left', padx=5)
            
            # Progress bar
            progress_var = tk.DoubleVar(value=mastery)
            progress_bar = ttk.Progressbar(
                topic_frame, 
                variable=progress_var, 
                length=300,
                maximum=100
            )
            progress_bar.pack(side='left', padx=5, fill='x', expand=True)
            
            # Percentage label
            pct_label = ttk.Label(topic_frame, text=f"{mastery:.1f}%", width=7)
            pct_label.pack(side='right', padx=5)
            
            # Add alternating row colors
            if i % 2 == 0:
                topic_frame.configure(style='Content.TFrame')
            else:
                topic_frame.configure(style='Content.TFrame')
                # Could set a different style for alternating rows if desired
    
    def _load_progress_data(self):
        """Load progress tab data."""
        # Get recent performance data
        recent_data = self.stats_manager.get_recent_performance(days=30)
        
        if not recent_data:
            return
        
        # Update progress metrics in main thread
        self.after(0, lambda: self._update_progress_metrics(recent_data))
        
        # Get learning curve chart
        chart_data = self.stats_manager.plot_learning_curve(days=30)
        
        if chart_data:
            # Convert to tkinter image
            img = self.stats_manager.create_tk_image(chart_data, size=(800, 400))
            
            # Store reference to prevent garbage collection
            self.chart_images['learning_curve'] = img
            
            # Update label in main thread
            self.after(0, lambda: self.learning_curve_label.config(image=img, text=""))
    
    def _update_progress_metrics(self, recent_data):
        """
        Update the progress metrics.
        
        Args:
            recent_data (dict): Recent performance data
        """
        # Calculate metrics for recent periods
        dates = recent_data.get('dates', [])
        questions = recent_data.get('questions', [])
        correct = recent_data.get('correct', [])
        
        # Get last 7 days data (if available)
        week_questions = sum(questions[-7:]) if len(questions) >= 7 else sum(questions)
        week_correct = sum(correct[-7:]) if len(correct) >= 7 else sum(correct)
        week_accuracy = (week_correct / week_questions * 100) if week_questions > 0 else 0
        
        # Get last 30 days data
        month_questions = sum(questions)
        month_correct = sum(correct)
        month_accuracy = (month_correct / month_questions * 100) if month_questions > 0 else 0
        
        # Update labels
        self.progress_labels['week_questions'].config(
            text=f"{week_questions} questions"
        )
        
        self.progress_labels['week_accuracy'].config(
            text=f"{week_accuracy:.1f}%"
        )
        
        self.progress_labels['month_questions'].config(
            text=f"{month_questions} questions"
        )
        
        self.progress_labels['month_accuracy'].config(
            text=f"{month_accuracy:.1f}%"
        )
    
    def _load_sessions_data(self):
        """Load sessions tab data."""
        # Get session history
        sessions = self.data_manager.get_learning_sessions()
        
        if not sessions:
            return
        
        # Update sessions tree in main thread
        self.after(0, lambda: self._update_sessions_tree(sessions))
    
    def _update_sessions_tree(self, sessions):
        """
        Update the sessions treeview.
        
        Args:
            sessions (list): Session data
        """
        # Clear existing items
        for item in self.sessions_tree.get_children():
            self.sessions_tree.delete(item)
        
        # Add sessions to treeview
        for session in sessions:
            # Format date
            date_str = session.get('date', '').split('T')[0]  # Extract date part
            
            # Format duration
            duration = session.get('duration_minutes', 0)
            if duration >= 60:
                duration_str = f"{duration // 60}h {duration % 60}m"
            else:
                duration_str = f"{duration}m"
            
            # Calculate accuracy
            questions = session.get('questions_answered', 0)
            correct = session.get('correct_answers', 0)
            accuracy = (correct / questions * 100) if questions > 0 else 0
            accuracy_str = f"{accuracy:.1f}%"
            
            # Format topics
            topics = session.get('topics', [])
            topics_str = ", ".join(topics) if topics else "—"
            
            # Add to treeview
            self.sessions_tree.insert(
                '', 'end',
                values=(
                    date_str,
                    duration_str,
                    questions,
                    correct,
                    accuracy_str,
                    topics_str
                )
            )