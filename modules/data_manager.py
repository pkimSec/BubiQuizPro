def refresh_all_data(self):
        """
        Refresh all cached data and database info.
        Call this after questions are added or removed.
        """
        # Clear caches
        self._questions_cache = {}
        self._topics_cache = set()
        self._sources_cache = set()
        
        # Reload questions from files
        self.load_all_questions()
        
        # Update the database topic entries
        with self.conn_lock:
            cursor = self.conn.cursor()
            
            # Get current topics from question files
            current_topics = self._topics_cache
            
            # Get topics from database
            cursor.execute("SELECT topic_name FROM topic_progress")
            db_topics = {row[0] for row in cursor.fetchall()}
            
            # Remove topics that no longer exist
            for topic in db_topics - current_topics:
                cursor.execute("DELETE FROM topic_progress WHERE topic_name = ?", (topic,))
            
            # Add new topics
            for topic in current_topics:
                # Count questions for this topic
                count = sum(1 for q in self._questions_cache.values() 
                           if topic in q.get('topics', []))
                
                # Insert or update topic
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO topic_progress 
                    (topic_name, total_questions, correct_answers, mastery_percentage)
                    VALUES (?, ?, 0, 0)
                    """,
                    (topic, count)
                )
            
            # Clean up subjects_scripts table
            cursor.execute("DELETE FROM subjects_scripts")
            
            # Re-populate subjects_scripts if needed
            for q in self._questions_cache.values():
                if 'source_reference' in q:
                    parts = q['source_reference'].split(',')[0].split()
                    if len(parts) >= 2:
                        subject = parts[0]
                        script = ' '.join(parts[1:])
                        cursor.execute(
                            "INSERT OR IGNORE INTO subjects_scripts (subject_name, script_name) VALUES (?, ?)",
                            (subject, script)
                        )
            
            self.conn.commit()
            
        logger.info("All data refreshed")#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BubiQuizPro - Data Management Module

This module handles all data operations for the BubiQuizPro application:
- JSON questions import/export
- SQLite database operations for user progress
- Data validation and transformation
"""

import os
import json
import sqlite3
import logging
import shutil
import threading
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

class DataManager:
    """
    Manages all data operations for BubiQuizPro including:
    - Question import/export
    - User progress tracking
    - Database operations
    """
    
    def __init__(self, db_path=None):
        """
        Initialize the data manager.
        
        Args:
            db_path (str, optional): Path to the SQLite database. 
                                    If None, uses the default path.
        """
        # Set up paths
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.base_dir, 'data')
        self.questions_dir = os.path.join(self.data_dir, 'questions')
        self.exports_dir = os.path.join(self.data_dir, 'exports')
        
        # Ensure directories exist
        os.makedirs(self.questions_dir, exist_ok=True)
        os.makedirs(self.exports_dir, exist_ok=True)
        
        # Set up database
        if db_path is None:
            self.db_path = os.path.join(self.data_dir, 'user_progress.db')
        else:
            self.db_path = db_path
            
        self.conn = None
        self._init_database()
        
        # Cache for questions
        self._questions_cache = {}
        self._topics_cache = set()
        self._sources_cache = set()
        
        # Load questions into cache
        self.load_all_questions()
        
        logger.info("DataManager initialized successfully")
    
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        try:
            # Use check_same_thread=False to allow access from multiple threads
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn_lock = threading.Lock()  # Add a lock for thread safety
            cursor = self.conn.cursor()
            
            # Create tables if they don't exist
            cursor.executescript('''
                -- Tabelle für Fragen-Tracking
                CREATE TABLE IF NOT EXISTS question_progress (
                    question_id TEXT PRIMARY KEY,
                    correct_attempts INT DEFAULT 0,
                    wrong_attempts INT DEFAULT 0,
                    last_attempt TEXT,  -- ISO-Datum
                    next_review TEXT,   -- ISO-Datum für Spaced Repetition
                    mastery_level INT DEFAULT 0  -- 0-5 Beherrschungsgrad
                );
                
                -- Tabelle für Themen-Tracking
                CREATE TABLE IF NOT EXISTS topic_progress (
                    topic_name TEXT PRIMARY KEY,
                    total_questions INT DEFAULT 0,
                    correct_answers INT DEFAULT 0,
                    mastery_percentage REAL DEFAULT 0
                );
                
                -- Tabelle für Session-Tracking
                CREATE TABLE IF NOT EXISTS learning_sessions (
                    session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT,
                    duration_minutes INT,
                    questions_answered INT,
                    correct_answers INT,
                    topics TEXT  -- Komma-getrennte Liste
                );
                
                -- Tabelle für Skripte und Fächer
                CREATE TABLE IF NOT EXISTS subjects_scripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    subject_name TEXT,
                    script_name TEXT,
                    UNIQUE(subject_name, script_name)
                );
            ''')
            
            self.conn.commit()
            logger.debug("Database initialized successfully")
        except sqlite3.Error as e:
            logger.error(f"Database initialization error: {e}", exc_info=True)
            raise
    
    def close(self):
        """Close database connection."""
        if self.conn:
            with self.conn_lock:  # Use lock for thread safety
                self.conn.close()
            logger.debug("Database connection closed")
    
    def import_questions(self, file_path):
        """
        Import questions from a JSON file.
        
        Args:
            file_path (str): Path to the JSON file
            
        Returns:
            tuple: (success, message, count) where:
                success (bool): True if import was successful
                message (str): Status message
                count (int): Number of questions imported
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate the JSON structure
            if not self._validate_question_format(data):
                return False, "Invalid question file format", 0
            
            # Extract metadata
            metadata = data.get('metadata', {})
            source = metadata.get('source', os.path.basename(file_path))
            
            # Process subject and script
            if 'source' in metadata:
                parts = metadata['source'].split()
                if len(parts) >= 2:
                    subject = parts[0]
                    script = ' '.join(parts[1:])
                    self._add_subject_script(subject, script)
            
            # Add to cache
            questions = data.get('questions', [])
            count = 0
            
            for question in questions:
                q_id = question.get('id')
                if not q_id:
                    # Generate ID if not present
                    q_id = f"q{uuid.uuid4().hex[:8]}"
                    question['id'] = q_id
                
                # Add to cache
                self._questions_cache[q_id] = question
                count += 1
                
                # Update topics cache
                for topic in question.get('topics', []):
                    self._topics_cache.add(topic)
                    
                    # Update topic progress table
                    cursor = self.conn.cursor()
                    cursor.execute(
                        "INSERT OR IGNORE INTO topic_progress (topic_name, total_questions) VALUES (?, 0)",
                        (topic,)
                    )
                    cursor.execute(
                        "UPDATE topic_progress SET total_questions = total_questions + 1 WHERE topic_name = ?",
                        (topic,)
                    )
            
            # Save questions to a file in the questions directory
            dest_file = os.path.join(self.questions_dir, os.path.basename(file_path))
            shutil.copy2(file_path, dest_file)
            
            self.conn.commit()
            logger.info(f"Imported {count} questions from {file_path}")
            return True, f"Successfully imported {count} questions", count
            
        except json.JSONDecodeError:
            logger.error(f"JSON decode error in file: {file_path}", exc_info=True)
            return False, "Invalid JSON format", 0
        except Exception as e:
            logger.error(f"Error importing questions: {e}", exc_info=True)
            return False, f"Error: {str(e)}", 0
    
    def _validate_question_format(self, data):
        """
        Validate the JSON question format.
        
        Args:
            data (dict): The loaded JSON data
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not isinstance(data, dict):
            return False
            
        if 'questions' not in data or not isinstance(data['questions'], list):
            return False
            
        for question in data['questions']:
            if not isinstance(question, dict):
                return False
                
            # Check required fields
            if 'question' not in question:
                return False
                
            # Check multiple choice format
            if question.get('type') == 'multiple_choice':
                if 'options' not in question or not isinstance(question['options'], list):
                    return False
                if 'correct_answer' not in question:
                    return False
            
            # Check text question format
            if question.get('type') == 'text':
                if 'model_answer' not in question:
                    return False
        
        return True
    
    def _add_subject_script(self, subject, script):
        """
        Add or update a subject-script combination.
        
        Args:
            subject (str): Subject name
            script (str): Script name
        """
        with self.conn_lock:  # Use lock for thread safety
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT OR IGNORE INTO subjects_scripts (subject_name, script_name) VALUES (?, ?)",
                (subject, script)
            )
            self.conn.commit()
    
    def load_all_questions(self):
        """
        Load all questions from JSON files in the questions directory.
        
        Returns:
            int: Number of questions loaded
        """
        try:
            # Clear caches
            self._questions_cache = {}
            self._topics_cache = set()
            self._sources_cache = set()
            
            count = 0
            
            # Load all JSON files in the questions directory
            for filename in os.listdir(self.questions_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.questions_dir, filename)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if self._validate_question_format(data):
                        metadata = data.get('metadata', {})
                        source = metadata.get('source', filename)
                        self._sources_cache.add(source)
                        
                        # Process questions
                        questions = data.get('questions', [])
                        for question in questions:
                            q_id = question.get('id')
                            if q_id:
                                self._questions_cache[q_id] = question
                                count += 1
                                
                                # Update topics cache
                                for topic in question.get('topics', []):
                                    self._topics_cache.add(topic)
            
            logger.info(f"Loaded {count} questions from {len(os.listdir(self.questions_dir))} files")
            return count
        except Exception as e:
            logger.error(f"Error loading questions: {e}", exc_info=True)
            return 0
    
    def get_all_questions(self):
        """
        Get all questions.
        
        Returns:
            dict: Dictionary of all questions indexed by ID
        """
        return self._questions_cache
    
    def get_question(self, question_id):
        """
        Get a specific question by ID.
        
        Args:
            question_id (str): Question ID
            
        Returns:
            dict: Question data or None if not found
        """
        return self._questions_cache.get(question_id)
    
    def get_all_topics(self):
        """
        Get all topics.
        
        Returns:
            set: Set of all topics
        """
        return self._topics_cache
    
    def get_all_sources(self):
        """
        Get all sources.
        
        Returns:
            set: Set of all sources
        """
        return self._sources_cache
    
    def get_filtered_questions(self, topics=None, difficulty=None, source=None, subject=None, script=None, question_type=None):
        """
        Get questions filtered by various criteria.
        
        Args:
            topics (list, optional): List of topics to filter by
            difficulty (str, optional): Difficulty level to filter by
            source (str, optional): Source to filter by
            subject (str, optional): Subject to filter by
            script (str, optional): Script to filter by
            question_type (str, optional): Type of question to filter by ('multiple_choice' or 'text')
            
        Returns:
            dict: Dictionary of filtered questions indexed by ID
        """
        filtered = {}
        
        # Map common German difficulty terms to standardize
        difficulty_mapping = {
            "leicht": ["leicht", "einfach", "easy"],
            "mittel": ["mittel", "medium", "average"],
            "schwer": ["schwer", "hard", "difficult"]
        }
        
        for q_id, question in self._questions_cache.items():
            # Apply topic filter
            if topics and not any(topic in question.get('topics', []) for topic in topics):
                continue
                
            # Apply difficulty filter
            if difficulty:
                question_difficulty = question.get('difficulty', '').lower()
                
                # Check if there's a match in any of the mapped terms
                match_found = False
                for standard_diff, variations in difficulty_mapping.items():
                    if (difficulty.lower() == standard_diff and 
                        question_difficulty in variations):
                        match_found = True
                        break
                
                if not match_found and question_difficulty != difficulty.lower():
                    continue
            
            # Apply question type filter
            if question_type and question.get('type') != question_type:
                continue
                
            # Apply source filter
            source_ref = question.get('source_reference', '')
            metadata_source = ''
            
            # Check metadata for source if available
            if 'metadata' in question:
                metadata_source = question['metadata'].get('source', '')
            
            if source and not (source in source_ref or source in metadata_source):
                continue
                
            # Apply subject and script filters
            if subject or script:
                source_parts = source_ref.split()
                q_subject = source_parts[0] if len(source_parts) >= 1 else ''
                q_script = ' '.join(source_parts[1:]) if len(source_parts) >= 2 else ''
                
                if subject and q_subject != subject:
                    continue
                    
                if script and q_script != script:
                    continue
            
            # Add to filtered results
            filtered[q_id] = question
        
        return filtered
    
    def get_question_progress(self, question_id):
        """
        Get progress data for a specific question.
        
        Args:
            question_id (str): Question ID
            
        Returns:
            dict: Progress data or empty dict if not found
        """
        try:
            with self.conn_lock:  # Use lock for thread safety
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT * FROM question_progress WHERE question_id = ?",
                    (question_id,)
                )
                row = cursor.fetchone()
                
                if row:
                    return {
                        'question_id': row[0],
                        'correct_attempts': row[1],
                        'wrong_attempts': row[2],
                        'last_attempt': row[3],
                        'next_review': row[4],
                        'mastery_level': row[5]
                    }
                else:
                    return {}
                    
        except sqlite3.Error as e:
            logger.error(f"Error getting question progress: {e}", exc_info=True)
            return {}
    
    def get_all_subjects_scripts(self):
        """
        Get all subject-script combinations.
        
        Returns:
            list: List of dictionaries with subject and script names
        """
        try:
            with self.conn_lock:  # Use lock for thread safety
                cursor = self.conn.cursor()
                cursor.execute("SELECT subject_name, script_name FROM subjects_scripts")
                rows = cursor.fetchall()
                
                result = []
                for row in rows:
                    result.append({
                        'subject': row[0],
                        'script': row[1]
                    })
                
                return result
        except sqlite3.Error as e:
            logger.error(f"Error getting subjects and scripts: {e}", exc_info=True)
            return []
    
    def get_subjects(self):
        """
        Get all unique subjects.
        
        Returns:
            list: List of subject names
        """
        try:
            with self.conn_lock:  # Use lock for thread safety
                cursor = self.conn.cursor()
                cursor.execute("SELECT DISTINCT subject_name FROM subjects_scripts")
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting subjects: {e}", exc_info=True)
            return []
    
    def get_scripts_for_subject(self, subject):
        """
        Get all scripts for a specific subject.
        
        Args:
            subject (str): Subject name
            
        Returns:
            list: List of script names
        """
        try:
            with self.conn_lock:  # Use lock for thread safety
                cursor = self.conn.cursor()
                cursor.execute(
                    "SELECT script_name FROM subjects_scripts WHERE subject_name = ?",
                    (subject,)
                )
                return [row[0] for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Error getting scripts for subject: {e}", exc_info=True)
            return []
    
    def update_question_progress(self, question_id, is_correct):
        """
        Update progress for a specific question after answering.
        
        Args:
            question_id (str): Question ID
            is_correct (bool): Whether the answer was correct
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.conn_lock:  # Use lock for thread safety
                cursor = self.conn.cursor()
                
                # Get current progress
                cursor.execute(
                    "SELECT correct_attempts, wrong_attempts, mastery_level FROM question_progress WHERE question_id = ?",
                    (question_id,)
                )
                row = cursor.fetchone()
                
                now = datetime.now().isoformat()
                
                if row:
                    correct_attempts, wrong_attempts, mastery_level = row
                    
                    if is_correct:
                        correct_attempts += 1
                        # Increase mastery level with a maximum of 5
                        mastery_level = min(mastery_level + 1, 5)
                    else:
                        wrong_attempts += 1
                        # Decrease mastery level with a minimum of 0
                        mastery_level = max(mastery_level - 1, 0)
                    
                    # Calculate next review date based on spaced repetition algorithm
                    next_review = self._calculate_next_review(mastery_level, now)
                    
                    cursor.execute(
                        """
                        UPDATE question_progress 
                        SET correct_attempts = ?, wrong_attempts = ?, 
                            last_attempt = ?, next_review = ?, mastery_level = ?
                        WHERE question_id = ?
                        """,
                        (correct_attempts, wrong_attempts, now, next_review, mastery_level, question_id)
                    )
                else:
                    # First attempt for this question
                    correct_attempts = 1 if is_correct else 0
                    wrong_attempts = 0 if is_correct else 1
                    mastery_level = 1 if is_correct else 0
                    
                    # Calculate next review date
                    next_review = self._calculate_next_review(mastery_level, now)
                    
                    cursor.execute(
                        """
                        INSERT INTO question_progress 
                        (question_id, correct_attempts, wrong_attempts, 
                         last_attempt, next_review, mastery_level)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (question_id, correct_attempts, wrong_attempts, now, next_review, mastery_level)
                    )
                
                # Update topic progress
                question = self.get_question(question_id)
                if question and is_correct:
                    for topic in question.get('topics', []):
                        cursor.execute(
                            """
                            UPDATE topic_progress 
                            SET correct_answers = correct_answers + 1,
                                mastery_percentage = (correct_answers * 100.0 / total_questions)
                            WHERE topic_name = ?
                            """,
                            (topic,)
                        )
                
                self.conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error updating question progress: {e}", exc_info=True)
            with self.conn_lock:
                self.conn.rollback()
            return False
    
    def _calculate_next_review(self, mastery_level, last_review_iso):
        """
        Calculate the next review date based on the spaced repetition algorithm.
        
        Args:
            mastery_level (int): Current mastery level (0-5)
            last_review_iso (str): ISO format date string of last review
            
        Returns:
            str: ISO format date string for next review
        """
        try:
            last_review = datetime.fromisoformat(last_review_iso)
        except (ValueError, TypeError):
            last_review = datetime.now()
        
        # Spaced repetition intervals (in days) for each mastery level
        intervals = [1, 2, 4, 7, 14, 30]
        
        # Get the appropriate interval based on mastery level
        interval = intervals[min(mastery_level, 5)]
        
        # Calculate next review date
        next_review = last_review + timedelta(days=interval)
        
        return next_review.isoformat()
    
    def record_learning_session(self, duration_minutes, questions_answered, correct_answers, topics):
        """
        Record data for a completed learning session.
        
        Args:
            duration_minutes (int): Duration of session in minutes
            questions_answered (int): Number of questions answered
            correct_answers (int): Number of correct answers
            topics (list): List of topics covered
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            with self.conn_lock:  # Use lock for thread safety
                cursor = self.conn.cursor()
                
                topics_str = ','.join(topics) if topics else ''
                
                cursor.execute(
                    """
                    INSERT INTO learning_sessions 
                    (date, duration_minutes, questions_answered, correct_answers, topics)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (datetime.now().isoformat(), duration_minutes, questions_answered, correct_answers, topics_str)
                )
                
                self.conn.commit()
                return True
                
        except sqlite3.Error as e:
            logger.error(f"Error recording learning session: {e}", exc_info=True)
            with self.conn_lock:
                self.conn.rollback()
            return False
    
    def get_learning_sessions(self, limit=None):
        """
        Get learning session data.
        
        Args:
            limit (int, optional): Limit number of sessions returned
            
        Returns:
            list: List of session dictionaries
        """
        try:
            with self.conn_lock:  # Use lock for thread safety
                cursor = self.conn.cursor()
                
                if limit:
                    cursor.execute(
                        "SELECT * FROM learning_sessions ORDER BY date DESC LIMIT ?",
                        (limit,)
                    )
                else:
                    cursor.execute("SELECT * FROM learning_sessions ORDER BY date DESC")
                    
                rows = cursor.fetchall()
                
                sessions = []
                for row in rows:
                    topics = row[5].split(',') if row[5] else []
                    sessions.append({
                        'session_id': row[0],
                        'date': row[1],
                        'duration_minutes': row[2],
                        'questions_answered': row[3],
                        'correct_answers': row[4],
                        'topics': topics
                    })
                
                return sessions
                
        except sqlite3.Error as e:
            logger.error(f"Error getting learning sessions: {e}", exc_info=True)
            return []
    
    def get_topic_progress(self):
        """
        Get progress data for all topics.
        
        Returns:
            list: List of topic progress dictionaries
        """
        try:
            with self.conn_lock:  # Use lock for thread safety
                cursor = self.conn.cursor()
                cursor.execute("SELECT * FROM topic_progress")
                rows = cursor.fetchall()
                
                progress = []
                for row in rows:
                    progress.append({
                        'topic_name': row[0],
                        'total_questions': row[1],
                        'correct_answers': row[2],
                        'mastery_percentage': row[3]
                    })
                
                return progress
                
        except sqlite3.Error as e:
            logger.error(f"Error getting topic progress: {e}", exc_info=True)
            return []
    
    def get_questions_for_review(self, limit=20):
        """
        Get questions due for review based on the spaced repetition algorithm.
        
        Args:
            limit (int, optional): Maximum number of questions to return
            
        Returns:
            list: List of question IDs due for review
        """
        try:
            cursor = self.conn.cursor()
            now = datetime.now().isoformat()
            
            # Get questions due for review
            cursor.execute(
                """
                SELECT question_id FROM question_progress
                WHERE next_review <= ? OR next_review IS NULL
                ORDER BY mastery_level ASC, last_attempt ASC
                LIMIT ?
                """,
                (now, limit)
            )
            
            question_ids = [row[0] for row in cursor.fetchall()]
            
            # If we have fewer than the limit, add some unseen questions
            if len(question_ids) < limit:
                all_ids = set(self._questions_cache.keys())
                seen_ids = set(question_ids)
                
                # Get IDs of questions already in progress
                cursor.execute("SELECT question_id FROM question_progress")
                seen_ids.update(row[0] for row in cursor.fetchall())
                
                # Find unseen questions
                unseen_ids = all_ids - seen_ids
                
                # Add some unseen questions up to the limit
                question_ids.extend(list(unseen_ids)[:limit - len(question_ids)])
            
            return question_ids
            
        except sqlite3.Error as e:
            logger.error(f"Error getting questions for review: {e}", exc_info=True)
            return []
    
    def export_questions_to_anki(self, question_ids, output_file=None):
        """
        Export selected questions to Anki-compatible format.
        
        Args:
            question_ids (list): List of question IDs to export
            output_file (str, optional): Output file path, if None generates a default path
            
        Returns:
            tuple: (success, message, file_path)
        """
        try:
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = os.path.join(self.exports_dir, f"anki_export_{timestamp}.txt")
            
            with open(output_file, 'w', encoding='utf-8') as f:
                for q_id in question_ids:
                    question = self.get_question(q_id)
                    if not question:
                        continue
                    
                    # Create the front side (question)
                    front = question.get('question', '')
                    
                    # Create the back side (answer)
                    if question.get('type') == 'multiple_choice':
                        options = question.get('options', [])
                        correct_idx = question.get('correct_answer', 0)
                        if 0 <= correct_idx < len(options):
                            back = options[correct_idx]
                            # Add explanation if available
                            if 'explanation' in question:
                                back += f"\n\n{question['explanation']}"
                        else:
                            back = "Error: Invalid correct answer index"
                    else:  # text question
                        back = question.get('model_answer', '')
                    
                    # Write to file in Anki format (front; back)
                    f.write(f"{front}; {back}\n")
            
            logger.info(f"Exported {len(question_ids)} questions to {output_file}")
            return True, f"Successfully exported {len(question_ids)} questions", output_file
            
        except Exception as e:
            logger.error(f"Error exporting to Anki: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None
    
    def backup_database(self, backup_path=None):
        """
        Create a backup of the database.
        
        Args:
            backup_path (str, optional): Path for the backup file
            
        Returns:
            tuple: (success, message, file_path)
        """
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(self.data_dir, f"user_progress_backup_{timestamp}.db")
            
            # Close connection temporarily
            if self.conn:
                self.conn.close()
            
            # Copy the database file
            shutil.copy2(self.db_path, backup_path)
            
            # Reopen connection
            self.conn = sqlite3.connect(self.db_path)
            
            logger.info(f"Created database backup at {backup_path}")
            return True, "Database backup created successfully", backup_path
            
        except Exception as e:
            logger.error(f"Error creating database backup: {e}", exc_info=True)
            
            # Ensure connection is reopened
            try:
                if not self.conn:
                    self.conn = sqlite3.connect(self.db_path)
            except Exception:
                pass
                
            return False, f"Error: {str(e)}", None