#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BubiQuizPro - Quiz Engine Module

This module handles the core quiz functionality including:
- Question selection based on various modes
- Answer evaluation
- Spaced repetition scheduling
- Quiz session management
"""

import logging
import random
import time
from datetime import datetime, timedelta
import difflib

logger = logging.getLogger(__name__)

class QuizEngine:
    """
    Manages quiz functionality including question selection,
    answer evaluation, and session management.
    """
    
    def __init__(self, data_manager):
        """
        Initialize the quiz engine.
        
        Args:
            data_manager: DataManager instance for accessing question data
        """
        self.data_manager = data_manager
        self.current_session = None
        self.current_question = None
        self.session_questions = []
        self.session_results = []
        
        logger.info("QuizEngine initialized")
    
    def start_session(self, mode="normal", topics=None, difficulty=None, 
                    source=None, subject=None, script=None, 
                    question_count=10, time_limit=None):
        """
        Start a new quiz session.
        
        Args:
            mode (str): Session mode ("normal", "weak_spots", "spaced_repetition", "exam")
            topics (list): Topics to include
            difficulty (str): Difficulty level
            source (str): Source filter
            subject (str): Subject filter
            script (str): Script filter
            question_count (int): Number of questions
            time_limit (int): Time limit in minutes (None for no limit)
            
        Returns:
            dict: Session information
        """
        # End any existing session
        if self.current_session:
            self.end_session()
        
        # Create new session
        self.current_session = {
            "mode": mode,
            "topics": topics if topics else [],
            "difficulty": difficulty,
            "source": source,
            "subject": subject,
            "script": script,
            "question_count": question_count,
            "time_limit": time_limit,
            "start_time": time.time(),
            "end_time": None,
            "questions_answered": 0,
            "correct_answers": 0
        }
        
        # Select questions based on mode
        if mode == "normal":
            self.session_questions = self._select_normal_questions(
                topics, difficulty, source, subject, script, question_count
            )
        elif mode == "weak_spots":
            self.session_questions = self._select_weak_spot_questions(
                topics, difficulty, source, subject, script, question_count
            )
        elif mode == "spaced_repetition":
            self.session_questions = self._select_spaced_repetition_questions(
                topics, difficulty, source, subject, script, question_count
            )
        elif mode == "exam":
            self.session_questions = self._select_exam_questions(
                topics, difficulty, source, subject, script, question_count
            )
        else:
            logger.warning(f"Unknown session mode: {mode}, falling back to normal mode")
            self.session_questions = self._select_normal_questions(
                topics, difficulty, source, subject, script, question_count
            )
        
        # Reset session results
        self.session_results = []
        self.current_question = None
        
        logger.info(f"Started quiz session: {mode} mode with {len(self.session_questions)} questions")
        
        session_info = {
            "mode": mode,
            "question_count": len(self.session_questions),
            "time_limit": time_limit
        }
        
        return session_info
    
    def _select_normal_questions(self, topics, difficulty, source, subject, script, count):
        """
        Select questions for normal mode.
        
        Args:
            topics, difficulty, source, subject, script: Filters
            count (int): Number of questions to select
            
        Returns:
            list: Selected question IDs
        """
        # Get filtered questions
        filtered = self.data_manager.get_filtered_questions(
            topics, difficulty, source, subject, script
        )
        
        # Randomize and limit to count
        question_ids = list(filtered.keys())
        random.shuffle(question_ids)
        
        return question_ids[:min(count, len(question_ids))]
    
    def _select_weak_spot_questions(self, topics, difficulty, source, subject, script, count):
        """
        Select questions focusing on weak spots (frequently missed questions).
        
        Args:
            topics, difficulty, source, subject, script: Filters
            count (int): Number of questions to select
            
        Returns:
            list: Selected question IDs
        """
        # Get filtered questions
        filtered = self.data_manager.get_filtered_questions(
            topics, difficulty, source, subject, script
        )
        
        # Get progress data
        question_scores = []
        for q_id in filtered:
            progress = self.data_manager.get_question_progress(q_id)
            
            if not progress:
                # Unseen questions get medium priority
                question_scores.append((q_id, 50))
                continue
                
            correct = progress.get('correct_attempts', 0)
            wrong = progress.get('wrong_attempts', 0)
            
            if correct + wrong == 0:
                score = 50  # Unseen questions get medium priority
            else:
                # Calculate score where lower is worse (more focus needed)
                success_rate = correct / (correct + wrong) * 100
                score = success_rate
                
            question_scores.append((q_id, score))
        
        # Sort by score (ascending - lower scores first)
        question_scores.sort(key=lambda x: x[1])
        
        # Select the lowest scoring questions
        return [q[0] for q in question_scores[:min(count, len(question_scores))]]
    
    def _select_spaced_repetition_questions(self, topics, difficulty, source, subject, script, count):
        """
        Select questions due for review based on spaced repetition algorithm.
        
        Args:
            topics, difficulty, source, subject, script: Filters
            count (int): Number of questions to select
            
        Returns:
            list: Selected question IDs
        """
        # Get questions due for review
        due_questions = self.data_manager.get_questions_for_review(count * 2)  # Get more than needed
        
        # Filter by criteria
        filtered = self.data_manager.get_filtered_questions(
            topics, difficulty, source, subject, script
        )
        
        # Intersect the sets
        eligible_questions = [q_id for q_id in due_questions if q_id in filtered]
        
        # If we don't have enough, add some random ones from the filtered set
        if len(eligible_questions) < count:
            remaining = set(filtered.keys()) - set(eligible_questions)
            eligible_questions.extend(random.sample(list(remaining), 
                                                 min(count - len(eligible_questions), len(remaining))))
        
        random.shuffle(eligible_questions)
        return eligible_questions[:min(count, len(eligible_questions))]
    
    def _select_exam_questions(self, topics, difficulty, source, subject, script, count):
        """
        Select questions for exam mode - comprehensive coverage of topics.
        
        Args:
            topics, difficulty, source, subject, script: Filters
            count (int): Number of questions to select
            
        Returns:
            list: Selected question IDs
        """
        # Get filtered questions
        filtered = self.data_manager.get_filtered_questions(
            topics, difficulty, source, subject, script
        )
        
        # Group by topics to ensure coverage
        topic_groups = {}
        
        for q_id, question in filtered.items():
            q_topics = question.get('topics', [])
            for topic in q_topics:
                if topic not in topic_groups:
                    topic_groups[topic] = []
                topic_groups[topic].append(q_id)
        
        # Distribute questions across topics
        selected = []
        topics_list = list(topic_groups.keys())
        
        # Keep selecting questions until we have enough or run out
        while len(selected) < count and topics_list:
            # Cycle through topics
            for topic in list(topics_list):  # Use a copy to safely modify during iteration
                if not topic_groups[topic]:
                    topics_list.remove(topic)
                    continue
                    
                # Get a random question from this topic
                q_id = random.choice(topic_groups[topic])
                topic_groups[topic].remove(q_id)
                
                # Only add if not already selected
                if q_id not in selected:
                    selected.append(q_id)
                    
                if len(selected) >= count:
                    break
            
            # If we've gone through all topics but still need more questions,
            # just add random ones from what's left
            if len(selected) < count and not any(topic_groups.values()):
                remaining = set(filtered.keys()) - set(selected)
                selected.extend(random.sample(list(remaining), 
                                           min(count - len(selected), len(remaining))))
                break
        
        return selected
    
    def get_next_question(self):
        """
        Get the next question in the current session.
        
        Returns:
            dict: Question data or None if no more questions
        """
        if not self.current_session or not self.session_questions:
            logger.warning("Cannot get next question: No active session or no questions left")
            return None
        
        # Check for time limit
        if self.current_session.get('time_limit'):
            elapsed = time.time() - self.current_session['start_time']
            if elapsed / 60 > self.current_session['time_limit']:
                logger.info("Session time limit reached")
                return None
        
        # Get next question ID
        q_id = self.session_questions.pop(0) if self.session_questions else None
        
        if not q_id:
            logger.info("No more questions in session")
            return None
        
        # Get question data
        question = self.data_manager.get_question(q_id)
        if not question:
            logger.warning(f"Question ID {q_id} not found")
            return self.get_next_question()  # Skip and try next
        
        # Store current question
        self.current_question = {
            "id": q_id,
            "data": question,
            "start_time": time.time()
        }
        
        return question
    
    def submit_answer(self, answer):
        """
        Submit an answer for the current question.
        
        Args:
            answer: The user's answer (index for multiple choice, text for text questions)
            
        Returns:
            dict: Result information
        """
        if not self.current_session or not self.current_question:
            logger.warning("Cannot submit answer: No active session or question")
            return {"error": "No active question"}
        
        question = self.current_question["data"]
        question_id = self.current_question["id"]
        question_type = question.get("type", "multiple_choice")
        
        # Evaluate answer
        is_correct = False
        correct_answer = None
        explanation = question.get("explanation", "")
        
        if question_type == "multiple_choice":
            correct_index = question.get("correct_answer", 0)
            options = question.get("options", [])
            
            # Convert answer to integer if it's a string
            if isinstance(answer, str) and answer.isdigit():
                answer = int(answer)
                
            is_correct = answer == correct_index
            correct_answer = options[correct_index] if 0 <= correct_index < len(options) else "Unknown"
            
        elif question_type == "text":
            model_answer = question.get("model_answer", "")
            keywords = question.get("keywords", [])
            
            # Option 1: Simple keyword matching
            if keywords:
                found_keywords = [kw.lower() for kw in keywords if kw.lower() in answer.lower()]
                is_correct = len(found_keywords) >= len(keywords) * 0.6  # At least 60% of keywords
            
            # Option 2: Similarity matching with the model answer
            else:
                similarity = difflib.SequenceMatcher(None, answer.lower(), model_answer.lower()).ratio()
                is_correct = similarity >= 0.7  # At least 70% similar
            
            correct_answer = model_answer
        
        # Get source reference if available
        source_reference = question.get("source_reference", "")
        
        # Record result
        result = {
            "question_id": question_id,
            "is_correct": is_correct,
            "user_answer": answer,
            "correct_answer": correct_answer,
            "explanation": explanation,
            "source_reference": source_reference,
            "time_taken": time.time() - self.current_question["start_time"]
        }
        
        self.session_results.append(result)
        
        # Update session stats
        self.current_session["questions_answered"] += 1
        if is_correct:
            self.current_session["correct_answers"] += 1
        
        # Update question progress in the database
        self.data_manager.update_question_progress(question_id, is_correct)
        
        logger.info(f"Answer submitted for question {question_id}: {'Correct' if is_correct else 'Incorrect'}")
        
        return result
    
    def get_session_progress(self):
        """
        Get current session progress information.
        
        Returns:
            dict: Session progress data
        """
        if not self.current_session:
            return None
        
        return {
            "mode": self.current_session["mode"],
            "questions_total": self.current_session["question_count"],
            "questions_answered": self.current_session["questions_answered"],
            "correct_answers": self.current_session["correct_answers"],
            "remaining_questions": len(self.session_questions),
            "elapsed_time": time.time() - self.current_session["start_time"],
            "time_limit": self.current_session["time_limit"]
        }
    
    def end_session(self):
        """
        End the current quiz session and record statistics.
        
        Returns:
            dict: Session summary
        """
        if not self.current_session:
            logger.warning("Cannot end session: No active session")
            return None
        
        # Set end time
        self.current_session["end_time"] = time.time()
        
        # Calculate duration in minutes
        duration = (self.current_session["end_time"] - self.current_session["start_time"]) / 60
        
        # Record session in the database
        self.data_manager.record_learning_session(
            duration_minutes=int(duration),
            questions_answered=self.current_session["questions_answered"],
            correct_answers=self.current_session["correct_answers"],
            topics=self.current_session["topics"]
        )
        
        # Prepare summary
        summary = {
            "mode": self.current_session["mode"],
            "topics": self.current_session["topics"],
            "duration_minutes": int(duration),
            "questions_total": self.current_session["question_count"],
            "questions_answered": self.current_session["questions_answered"],
            "correct_answers": self.current_session["correct_answers"],
            "accuracy": (self.current_session["correct_answers"] / self.current_session["questions_answered"]) * 100 
                if self.current_session["questions_answered"] > 0 else 0,
            "results": self.session_results
        }
        
        logger.info(f"Session ended: {summary['questions_answered']} questions, " 
                  f"{summary['correct_answers']} correct, {summary['accuracy']:.1f}% accuracy")
        
        # Reset session
        temp_summary = summary  # Store for return
        self.current_session = None
        self.current_question = None
        self.session_questions = []
        self.session_results = []
        
        return temp_summary
    
    def get_question_explanation(self, question_id=None):
        """
        Get explanation for a question.
        
        Args:
            question_id (str, optional): Question ID, if None uses current question
            
        Returns:
            str: Explanation text
        """
        if question_id is None:
            if not self.current_question:
                return None
            question_id = self.current_question["id"]
        
        question = self.data_manager.get_question(question_id)
        if not question:
            return None
        
        return question.get("explanation", "No explanation available.")
    
    def is_session_active(self):
        """
        Check if a quiz session is currently active.
        
        Returns:
            bool: True if session is active, False otherwise
        """
        return self.current_session is not None
    
    def get_current_question(self):
        """
        Get the current question data.
        
        Returns:
            dict: Current question data or None
        """
        if not self.current_question:
            return None
        
        return self.current_question["data"]