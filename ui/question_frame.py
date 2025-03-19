#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BubiQuizPro - Question Frame UI Component

This module implements the UI component for displaying questions and recording answers.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging
import time
import threading

logger = logging.getLogger(__name__)

class QuestionFrame(ttk.Frame):
    """
    Frame for displaying quiz questions and handling user answers.
    """
    
    def __init__(self, parent, quiz_engine, on_quiz_end_callback):
        """
        Initialize the question frame.
        
        Args:
            parent: Parent widget
            quiz_engine: QuizEngine instance
            on_quiz_end_callback: Callback function to call when quiz ends
        """
        super().__init__(parent, style='Content.TFrame')
        
        self.quiz_engine = quiz_engine
        self.on_quiz_end_callback = on_quiz_end_callback
        
        self.current_question = None
        self.answer_submitted = False
        self.timer_thread = None
        self.timer_active = False
        
        # Create UI components
        self._create_ui()
        
        logger.info("QuestionFrame initialized")
    
    def _create_ui(self):
        """Create the UI components."""
        # Configure grid
        self.columnconfigure(0, weight=1)
        
        # Header section
        self.header_frame = ttk.Frame(self, style='Content.TFrame')
        self.header_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=(20, 10))
        
        # Quiz info label
        self.quiz_info_var = tk.StringVar(value="Quiz in Progress")
        self.quiz_info_label = ttk.Label(self.header_frame, 
                                    textvariable=self.quiz_info_var,
                                    font=('Arial', 14, 'bold'))
        self.quiz_info_label.pack(side='left')
        
        # Progress indicators
        self.progress_frame = ttk.Frame(self.header_frame, style='Content.TFrame')
        self.progress_frame.pack(side='right')
        
        self.progress_var = tk.StringVar(value="Question 0/0")
        self.progress_label = ttk.Label(self.progress_frame, 
                                    textvariable=self.progress_var)
        self.progress_label.pack(side='left', padx=10)
        
        self.time_var = tk.StringVar(value="Time: 00:00")
        self.time_label = ttk.Label(self.progress_frame, 
                                textvariable=self.time_var)
        self.time_label.pack(side='left', padx=10)
        
        # Progress bar
        self.progress_bar_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_bar_var)
        self.progress_bar.grid(row=1, column=0, sticky='ew', padx=20, pady=5)
        
        # Question section
        self.question_frame = ttk.Frame(self, style='Content.TFrame', padding=20)
        self.question_frame.grid(row=2, column=0, sticky='nsew', padx=20, pady=10)
        self.question_frame.columnconfigure(0, weight=1)
        self.question_frame.rowconfigure(1, weight=1)
        
        # Question text
        self.question_var = tk.StringVar()
        self.question_label = ttk.Label(self.question_frame, 
                                    textvariable=self.question_var,
                                    font=('Arial', 12), 
                                    wraplength=800,
                                    justify='left')
        self.question_label.grid(row=0, column=0, sticky='w', pady=(0, 20))
        
        # Create frames for different question types
        self.mc_frame = self._create_multiple_choice_frame()
        self.text_frame = self._create_text_question_frame()
        
        # Buttons section
        self.buttons_frame = ttk.Frame(self, style='Content.TFrame')
        self.buttons_frame.grid(row=3, column=0, sticky='ew', padx=20, pady=20)
        
        self.submit_btn = ttk.Button(self.buttons_frame, text="Submit", 
                                command=self._submit_answer)
        self.submit_btn.pack(side='right', padx=5)
        
        self.next_btn = ttk.Button(self.buttons_frame, text="Next Question", 
                                command=self._next_question,
                                state='disabled')
        self.next_btn.pack(side='right', padx=5)
        
        self.quit_btn = ttk.Button(self.buttons_frame, text="End Quiz", 
                                command=self._confirm_quit_quiz)
        self.quit_btn.pack(side='left', padx=5)
        
        # Feedback section (initially hidden)
        self.feedback_frame = ttk.LabelFrame(self, text="Feedback", padding=10)
        self.feedback_frame.grid(row=4, column=0, sticky='ew', padx=20, pady=10)
        self.feedback_frame.grid_remove()  # Hide initially
        
        self.result_var = tk.StringVar()
        self.result_label = ttk.Label(self.feedback_frame, 
                                textvariable=self.result_var,
                                font=('Arial', 12, 'bold'))
        self.result_label.pack(anchor='w', pady=5)
        
        self.correct_answer_var = tk.StringVar()
        self.correct_answer_label = ttk.Label(self.feedback_frame, 
                                        textvariable=self.correct_answer_var,
                                        wraplength=800)
        self.correct_answer_label.pack(anchor='w', pady=5)
        
        self.explanation_var = tk.StringVar()
        self.explanation_label = ttk.Label(self.feedback_frame, 
                                        textvariable=self.explanation_var,
                                        wraplength=800,
                                        justify='left')
        self.explanation_label.pack(anchor='w', pady=5)
        
        # Add source reference label (NEW)
        self.source_var = tk.StringVar()
        self.source_label = ttk.Label(self.feedback_frame,
                                    textvariable=self.source_var,
                                    wraplength=800,
                                    font=('Arial', 9, 'italic'))
        self.source_label.pack(anchor='w', pady=5)
        
        # Status frame at the bottom
        self.status_frame = ttk.Frame(self, style='StatusBar.TFrame')
        self.status_frame.grid(row=5, column=0, sticky='ew', padx=0, pady=(10, 0))
        
        self.status_var = tk.StringVar(value="Ready to start quiz")
        self.status_label = ttk.Label(self.status_frame, 
                                textvariable=self.status_var,
                                style='StatusBar.TLabel')
        self.status_label.pack(side='left', padx=10)
    
    def _create_multiple_choice_frame(self):
        """Create the frame for multiple choice questions."""
        frame = ttk.Frame(self.question_frame, style='Content.TFrame')
        frame.grid(row=1, column=0, sticky='nsew')
        frame.grid_remove()  # Hide initially
        
        # Radio button variable
        self.mc_var = tk.IntVar(value=-1)
        
        # Options frame
        self.options_frame = ttk.Frame(frame, style='Content.TFrame')
        self.options_frame.pack(fill='both', expand=True)
        
        # Will be populated dynamically with radio buttons
        self.option_radios = []
        
        return frame
    
    def _create_text_question_frame(self):
        """Create the frame for text questions."""
        frame = ttk.Frame(self.question_frame, style='Content.TFrame')
        frame.grid(row=1, column=0, sticky='nsew')
        frame.grid_remove()  # Hide initially
        
        # Text entry with scrollbar
        entry_frame = ttk.Frame(frame, style='Content.TFrame')
        entry_frame.pack(fill='both', expand=True, pady=10)
        
        self.text_entry = tk.Text(entry_frame, height=10, width=80, wrap='word')
        self.text_entry.pack(side='left', fill='both', expand=True)
        
        text_scroll = ttk.Scrollbar(entry_frame, orient='vertical', 
                                  command=self.text_entry.yview)
        text_scroll.pack(side='right', fill='y')
        self.text_entry.config(yscrollcommand=text_scroll.set)
        
        # Keywords hint section
        self.keywords_frame = ttk.LabelFrame(frame, text="Keywords to Include", padding=5)
        self.keywords_frame.pack(fill='x', pady=10)
        
        self.keywords_var = tk.StringVar()
        self.keywords_label = ttk.Label(self.keywords_frame, 
                                      textvariable=self.keywords_var,
                                      wraplength=800)
        self.keywords_label.pack(anchor='w')
        
        return frame
    
    def load_first_question(self):
        """
        Load the first question to start the quiz.
        
        Returns:
            dict or None: The first question data or None if no questions available
        """
        # Reset state
        self.answer_submitted = False
        self.feedback_frame.grid_remove()
        
        # Reset UI
        self.submit_btn.config(state='normal')
        self.next_btn.config(state='disabled')
        
        # Update progress information
        progress = self.quiz_engine.get_session_progress()
        if progress:
            mode_name = progress.get('mode', '').replace('_', ' ').title()
            self.quiz_info_var.set(f"{mode_name} Quiz")
            
            total = progress.get('questions_total', 0)
            self.progress_var.set(f"Question 1/{total}")
            
            # Set progress bar
            self.progress_bar_var.set(1 / total * 100 if total > 0 else 0)
        
        # Start timer if time limit is set
        if progress and progress.get('time_limit'):
            self._start_timer(progress.get('time_limit') * 60)  # Convert to seconds
        
        # Get first question
        question = self.quiz_engine.get_next_question()
        if question:
            self._display_question(question)
            return question
        else:
            # No questions available - end quiz
            logger.warning("No questions available for the current filter criteria")
            return None
    
    def _display_question(self, question):
        """
        Display a question in the UI.
        
        Args:
            question (dict): Question data
        """
        self.current_question = question
        
        # Set question text
        self.question_var.set(question.get('question', 'No question text available'))
        
        # Show appropriate frame based on question type
        question_type = question.get('type', 'multiple_choice')
        
        if question_type == 'multiple_choice':
            self._display_multiple_choice(question)
        else:  # text question
            self._display_text_question(question)
        
        # Update status
        difficulty = question.get('difficulty', 'unknown')
        topics = ', '.join(question.get('topics', []))
        self.status_var.set(f"Difficulty: {difficulty} | Topics: {topics}")
        
        logger.debug(f"Displayed question ID: {question.get('id')}")
    
    def _display_multiple_choice(self, question):
        """
        Display a multiple choice question.
        
        Args:
            question (dict): Question data
        """
        # Show MC frame, hide text frame
        self.mc_frame.grid()
        self.text_frame.grid_remove()
        
        # Clear previous options
        for widget in self.options_frame.winfo_children():
            widget.destroy()
        self.option_radios = []
        
        # Reset selection
        self.mc_var.set(-1)
        
        # Add options
        options = question.get('options', [])
        
        for i, option_text in enumerate(options):
            option_frame = ttk.Frame(self.options_frame, style='Content.TFrame')
            option_frame.pack(fill='x', pady=5)
            
            # Using standard tk.Radiobutton because ttk.Radiobutton doesn't support wraplength
            radio = tk.Radiobutton(option_frame, 
                                 text=option_text,
                                 variable=self.mc_var,
                                 value=i,
                                 wraplength=700,
                                 justify='left',
                                 font=('Arial', 10),
                                 bg='#f0f0f0',  # Match background color
                                 anchor='w')
            radio.pack(anchor='w', fill='x', expand=True)
            
            self.option_radios.append(radio)
    
    def _display_text_question(self, question):
        """
        Display a text question.
        
        Args:
            question (dict): Question data
        """
        # Show text frame, hide MC frame
        self.text_frame.grid()
        self.mc_frame.grid_remove()
        
        # Clear previous text
        self.text_entry.delete('1.0', tk.END)
        
        # Show keywords if available
        keywords = question.get('keywords', [])
        if keywords:
            self.keywords_var.set("Include these concepts: " + ", ".join(keywords))
            self.keywords_frame.pack(fill='x', pady=10)
        else:
            self.keywords_frame.pack_forget()
    
    def _submit_answer(self):
        """Submit the current answer."""
        if self.answer_submitted or not self.current_question:
            return
        
        # Get answer based on question type
        question_type = self.current_question.get('type', 'multiple_choice')
        
        if question_type == 'multiple_choice':
            answer = self.mc_var.get()
            
            # Validate selection
            if answer == -1:
                messagebox.showwarning("No Selection", "Please select an answer.")
                return
                
        else:  # text question
            answer = self.text_entry.get('1.0', tk.END).strip()
            
            # Validate text
            if not answer:
                messagebox.showwarning("No Answer", "Please enter your answer.")
                return
        
        # Submit to quiz engine
        result = self.quiz_engine.submit_answer(answer)
        
        # Mark as submitted
        self.answer_submitted = True
        
        # Update UI
        self.submit_btn.config(state='disabled')
        self.next_btn.config(state='normal')
        
        # Display feedback
        self._show_answer_feedback(result)
        
        logger.debug(f"Answer submitted: {result.get('is_correct')}")
    
    def _show_answer_feedback(self, result):
        """
        Show feedback for the submitted answer.
        
        Args:
            result (dict): Result data from quiz engine
        """
        # Show the feedback frame
        self.feedback_frame.grid()
        
        # Clear all feedback variables first to ensure no previous content remains
        self.correct_answer_var.set("")
        self.explanation_var.set("")
        self.source_var.set("")
        
        # Set result text and color
        if result.get('is_correct'):
            self.result_var.set("Correct!")
            self.result_label.config(foreground='green')
        else:
            self.result_var.set("Incorrect")
            self.result_label.config(foreground='red')
            
            # Show correct answer only for incorrect responses
            self.correct_answer_var.set(f"Correct answer: {result.get('correct_answer', '')}")
        
        # Show explanation if available
        explanation = result.get('explanation', '')
        if explanation:
            self.explanation_var.set(f"Explanation: {explanation}")
        
        # Get and display source reference
        source_ref = result.get('source_reference', '')
        
        # If not in result, try to get it directly from the question
        if not source_ref and self.current_question:
            source_ref = self.current_question.get('source_reference', '')
        
        if source_ref:
            self.source_var.set(f"Source: {source_ref}")
    
    
    def _next_question(self):
        """Move to the next question."""
        # Hide feedback
        self.feedback_frame.grid_remove()
        
        # Reset state
        self.answer_submitted = False
        self.submit_btn.config(state='normal')
        self.next_btn.config(state='disabled')
        
        # Clear previous answers - ensure text entry is cleared
        self.text_entry.delete('1.0', tk.END)
        self.mc_var.set(-1)
        
        # Clear feedback variables explicitly
        self.result_var.set("")
        self.correct_answer_var.set("")
        self.explanation_var.set("")
        self.source_var.set("")
        
        # Update progress information
        progress = self.quiz_engine.get_session_progress()
        if progress:
            question_num = progress.get('questions_answered', 0) + 1
            total = progress.get('questions_total', 0)
            self.progress_var.set(f"Question {question_num}/{total}")
            
            # Update progress bar
            progress_pct = question_num / total * 100 if total > 0 else 0
            self.progress_bar_var.set(progress_pct)
        
        # Get next question
        question = self.quiz_engine.get_next_question()
        if question:
            self._display_question(question)
        else:
            self._end_quiz()
        
        logger.debug("Moved to next question")

    def _end_quiz(self):
        """End the current quiz and show results."""
        # Stop timer if running
        self.timer_active = False
        
        # Get session results
        results = self.quiz_engine.end_session()
        
        # Notify parent via callback
        if self.on_quiz_end_callback:
            self.on_quiz_end_callback(results)
        
        logger.info("Quiz ended")
    
    def _confirm_quit_quiz(self):
        """Confirm before quitting the quiz."""
        if messagebox.askyesno("End Quiz", 
                             "Are you sure you want to end this quiz? Your progress will be saved."):
            self._end_quiz()
    
    def _start_timer(self, seconds):
        """
        Start a countdown timer for the quiz.
        
        Args:
            seconds (int): Time limit in seconds
        """
        self.timer_active = True
        self.timer_start_time = time.time()
        self.timer_end_time = self.timer_start_time + seconds
        
        # Start timer in a separate thread
        self.timer_thread = threading.Thread(target=self._timer_worker)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        logger.debug(f"Started timer: {seconds} seconds")
    
    def _timer_worker(self):
        """Timer thread worker function."""
        try:
            while self.timer_active:
                # Calculate remaining time
                current_time = time.time()
                remaining = max(0, self.timer_end_time - current_time)
                
                # Format as MM:SS
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                time_str = f"Time: {minutes:02d}:{seconds:02d}"
                
                # Update UI in the main thread
                if hasattr(self, 'time_var'):
                    self.time_var.set(time_str)
                
                # Check if time is up
                if remaining <= 0:
                    self.timer_active = False
                    
                    # End the quiz in the main thread
                    if hasattr(self, 'master'):
                        self.master.after(0, self._time_up)
                    break
                
                # Sleep briefly
                time.sleep(0.1)
                
        except Exception as e:
            logger.error(f"Error in timer thread: {e}", exc_info=True)
    
    def _time_up(self):
        """Handle time-up event."""
        messagebox.showinfo("Time's Up", "The time limit for this quiz has been reached.")
        self._end_quiz()