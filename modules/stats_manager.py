#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BubiQuizPro - Statistics Manager Module

This module handles the statistics and visualization functionality including:
- Progress tracking
- Performance analysis
- Data visualization
- Reports generation
"""

import logging
import os
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg
import numpy as np
import io
import base64
from PIL import Image, ImageTk

logger = logging.getLogger(__name__)

# Configure matplotlib for non-interactive use
matplotlib.use('Agg')

class StatsManager:
    """
    Manages statistics and visualization for BubiQuizPro.
    """
    
    def __init__(self, data_manager):
        """
        Initialize the statistics manager.
        
        Args:
            data_manager: DataManager instance for accessing data
        """
        self.data_manager = data_manager
        self.exports_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'data', 
            'exports'
        )
        os.makedirs(self.exports_dir, exist_ok=True)
        
        logger.info("StatsManager initialized")
    
    def get_overall_stats(self):
        """
        Get overall statistics summary.
        
        Returns:
            dict: Overall statistics
        """
        try:
            # Get all sessions
            sessions = self.data_manager.get_learning_sessions()
            
            # Get topic progress
            topic_progress = self.data_manager.get_topic_progress()
            
            # Calculate overall stats
            total_questions_answered = sum(s.get('questions_answered', 0) for s in sessions)
            total_correct_answers = sum(s.get('correct_answers', 0) for s in sessions)
            total_time_spent = sum(s.get('duration_minutes', 0) for s in sessions)
            
            overall_accuracy = (total_correct_answers / total_questions_answered * 100) if total_questions_answered > 0 else 0
            
            # Get counts of questions by difficulty
            questions = self.data_manager.get_all_questions()
            difficulty_counts = {}
            for q in questions.values():
                diff = q.get('difficulty', 'unspecified')
                difficulty_counts[diff] = difficulty_counts.get(diff, 0) + 1
            
            # Get active topics
            active_topics = [tp.get('topic_name') for tp in topic_progress]
            mastery_by_topic = {tp.get('topic_name'): tp.get('mastery_percentage', 0) for tp in topic_progress}
            
            # Prepare the result
            stats = {
                'total_sessions': len(sessions),
                'total_questions_answered': total_questions_answered,
                'total_correct_answers': total_correct_answers,
                'overall_accuracy': overall_accuracy,
                'total_time_spent_minutes': total_time_spent,
                'difficulty_distribution': difficulty_counts,
                'topics_count': len(active_topics),
                'mastery_by_topic': mastery_by_topic,
                'topics_mastered': sum(1 for p in mastery_by_topic.values() if p >= 80),
                'last_session_date': sessions[0].get('date') if sessions else None
            }
            
            logger.debug("Generated overall statistics")
            return stats
            
        except Exception as e:
            logger.error(f"Error generating overall stats: {e}", exc_info=True)
            return {}
    
    def get_topic_mastery(self):
        """
        Get mastery percentage for all topics.
        
        Returns:
            dict: Topic mastery percentages
        """
        try:
            topic_progress = self.data_manager.get_topic_progress()
            
            # Structure as a dictionary mapping topic to mastery percentage
            return {tp.get('topic_name'): tp.get('mastery_percentage', 0) for tp in topic_progress}
            
        except Exception as e:
            logger.error(f"Error getting topic mastery: {e}", exc_info=True)
            return {}
    
    def get_recent_performance(self, days=30):
        """
        Get performance data for recent days.
        
        Args:
            days (int): Number of days to include
            
        Returns:
            dict: Recent performance data
        """
        try:
            # Get all sessions
            all_sessions = self.data_manager.get_learning_sessions()
            
            # Calculate date cutoff
            cutoff = (datetime.now() - timedelta(days=days)).isoformat()
            
            # Filter recent sessions
            recent_sessions = [s for s in all_sessions if s.get('date', '') >= cutoff]
            
            # Group by date
            daily_data = {}
            for session in recent_sessions:
                date_only = session.get('date', '').split('T')[0]  # Extract date part only
                
                if date_only not in daily_data:
                    daily_data[date_only] = {
                        'questions': 0,
                        'correct': 0,
                        'minutes': 0
                    }
                
                daily_data[date_only]['questions'] += session.get('questions_answered', 0)
                daily_data[date_only]['correct'] += session.get('correct_answers', 0)
                daily_data[date_only]['minutes'] += session.get('duration_minutes', 0)
            
            # Calculate daily accuracy
            for date, data in daily_data.items():
                if data['questions'] > 0:
                    data['accuracy'] = (data['correct'] / data['questions']) * 100
                else:
                    data['accuracy'] = 0
            
            # Format for result
            dates = sorted(daily_data.keys())
            result = {
                'dates': dates,
                'questions': [daily_data[d]['questions'] for d in dates],
                'correct': [daily_data[d]['correct'] for d in dates],
                'accuracy': [daily_data[d]['accuracy'] for d in dates],
                'minutes': [daily_data[d]['minutes'] for d in dates]
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting recent performance: {e}", exc_info=True)
            return {}
    
    def plot_topic_mastery(self, max_topics=10):
        """
        Generate a bar chart of topic mastery.
        
        Args:
            max_topics (int): Maximum number of topics to include
            
        Returns:
            bytes: PNG image data
        """
        try:
            # Get topic mastery data
            topic_mastery = self.get_topic_mastery()
            
            # Sort topics by mastery percentage (descending)
            sorted_topics = sorted(topic_mastery.items(), key=lambda x: x[1], reverse=True)
            
            # Limit to max_topics
            if len(sorted_topics) > max_topics:
                sorted_topics = sorted_topics[:max_topics]
            
            # Extract data for plotting
            topics = [t[0] for t in sorted_topics]
            mastery = [t[1] for t in sorted_topics]
            
            # Create the figure
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Create the bar chart
            bars = ax.barh(topics, mastery, color='skyblue')
            
            # Add value labels
            for i, bar in enumerate(bars):
                ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                       f'{mastery[i]:.1f}%', va='center')
            
            # Customize the chart
            ax.set_xlim(0, 100)
            ax.set_xlabel('Mastery Percentage')
            ax.set_title('Topic Mastery')
            ax.grid(axis='x', linestyle='--', alpha=0.7)
            
            # Adjust layout
            fig.tight_layout()
            
            # Convert to PNG image data
            buf = io.BytesIO()
            FigureCanvasAgg(fig).print_png(buf)
            
            # Create a PIL image
            img_data = buf.getvalue()
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_path = os.path.join(self.exports_dir, f"topic_mastery_{timestamp}.png")
            with open(img_path, 'wb') as f:
                f.write(img_data)
            
            logger.debug(f"Generated topic mastery chart: {img_path}")
            return img_data
            
        except Exception as e:
            logger.error(f"Error generating topic mastery chart: {e}", exc_info=True)
            return None
    
    def plot_learning_curve(self, days=30):
        """
        Generate a line chart of learning progress over time.
        
        Args:
            days (int): Number of days to include
            
        Returns:
            bytes: PNG image data
        """
        try:
            # Get recent performance data
            data = self.get_recent_performance(days)
            
            if not data or not data.get('dates'):
                logger.warning("No data available for learning curve chart")
                return None
            
            # Create the figure
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Convert dates to better format
            dates = [d.split('-')[1:] for d in data.get('dates', [])]  # Remove year
            dates = [f"{m}/{d}" for m, d in dates]  # Format as month/day
            
            # Plot accuracy line
            ax.plot(dates, data.get('accuracy', []), marker='o', linestyle='-', 
                   color='blue', label='Accuracy (%)')
            
            # Add a second y-axis for question count
            ax2 = ax.twinx()
            ax2.plot(dates, data.get('questions', []), marker='s', linestyle='--', 
                    color='green', label='Questions')
            
            # Customize the chart
            ax.set_ylim(0, 100)
            ax.set_ylabel('Accuracy (%)', color='blue')
            ax2.set_ylabel('Questions', color='green')
            
            # Add title and legend
            ax.set_title(f'Learning Progress (Last {days} Days)')
            ax.grid(True, alpha=0.3)
            
            # Handle x-axis
            if len(dates) > 10:
                # Show only some date labels to avoid crowding
                step = len(dates) // 10 + 1
                for i, label in enumerate(ax.get_xticklabels()):
                    if i % step != 0:
                        label.set_visible(False)
            
            # Rotate date labels
            plt.setp(ax.get_xticklabels(), rotation=45)
            
            # Combine legends
            lines1, labels1 = ax.get_legend_handles_labels()
            lines2, labels2 = ax2.get_legend_handles_labels()
            ax.legend(lines1 + lines2, labels1 + labels2, loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=2)
            
            # Adjust layout
            fig.tight_layout()
            
            # Convert to PNG image data
            buf = io.BytesIO()
            FigureCanvasAgg(fig).print_png(buf)
            
            # Create a PIL image
            img_data = buf.getvalue()
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_path = os.path.join(self.exports_dir, f"learning_curve_{timestamp}.png")
            with open(img_path, 'wb') as f:
                f.write(img_data)
            
            logger.debug(f"Generated learning curve chart: {img_path}")
            return img_data
            
        except Exception as e:
            logger.error(f"Error generating learning curve chart: {e}", exc_info=True)
            return None
    
    def plot_topic_heatmap(self):
        """
        Generate a heatmap showing topic strengths and weaknesses.
        
        Returns:
            bytes: PNG image data
        """
        try:
            # Get topic progress data
            topic_progress = self.data_manager.get_topic_progress()
            
            if not topic_progress:
                logger.warning("No data available for topic heatmap")
                return None
            
            # Sort topics by mastery percentage
            topic_progress.sort(key=lambda x: x.get('mastery_percentage', 0), reverse=True)
            
            # Limit to top 15 topics
            if len(topic_progress) > 15:
                topic_progress = topic_progress[:15]
            
            # Extract data for plotting
            topics = [tp.get('topic_name', '') for tp in topic_progress]
            mastery = [tp.get('mastery_percentage', 0) for tp in topic_progress]
            
            # Create the figure
            fig = Figure(figsize=(10, 6), dpi=100)
            ax = fig.add_subplot(111)
            
            # Create a heatmap-like visualization
            # Normalize mastery values to 0-1 range for color mapping
            norm_mastery = np.array(mastery) / 100.0
            
            # Create a color map from red (0%) to green (100%)
            cmap = plt.cm.RdYlGn
            
            # Plot bars with color based on mastery
            bars = ax.barh(topics, mastery)
            
            # Set colors for each bar
            for i, bar in enumerate(bars):
                bar.set_color(cmap(norm_mastery[i]))
            
            # Add value labels
            for i, bar in enumerate(bars):
                ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, 
                       f'{mastery[i]:.1f}%', va='center')
            
            # Customize the chart
            ax.set_xlim(0, 100)
            ax.set_xlabel('Mastery Percentage')
            ax.set_title('Topic Strengths and Weaknesses')
            ax.grid(axis='x', linestyle='--', alpha=0.3)
            
            # Add color bar
            sm = plt.cm.ScalarMappable(cmap=cmap, norm=plt.Normalize(0, 100))
            sm.set_array([])
            cb = fig.colorbar(sm, ax=ax)
            cb.set_label('Mastery Level')
            
            # Adjust layout
            fig.tight_layout()
            
            # Convert to PNG image data
            buf = io.BytesIO()
            FigureCanvasAgg(fig).print_png(buf)
            
            # Create a PIL image
            img_data = buf.getvalue()
            
            # Save to file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            img_path = os.path.join(self.exports_dir, f"topic_heatmap_{timestamp}.png")
            with open(img_path, 'wb') as f:
                f.write(img_data)
            
            logger.debug(f"Generated topic heatmap chart: {img_path}")
            return img_data
            
        except Exception as e:
            logger.error(f"Error generating topic heatmap: {e}", exc_info=True)
            return None
    
    def generate_progress_report(self):
        """
        Generate a comprehensive progress report.
        
        Returns:
            dict: Report data
        """
        try:
            # Get overall stats
            overall = self.get_overall_stats()
            
            # Get topic mastery
            topic_mastery = self.get_topic_mastery()
            
            # Get recent performance
            recent = self.get_recent_performance(30)
            
            # Get session history
            sessions = self.data_manager.get_learning_sessions(10)  # Last 10 sessions
            
            # Calculate weekly progress
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).isoformat()
            
            weekly_sessions = [s for s in sessions if s.get('date', '') >= week_start]
            weekly_questions = sum(s.get('questions_answered', 0) for s in weekly_sessions)
            weekly_correct = sum(s.get('correct_answers', 0) for s in weekly_sessions)
            weekly_accuracy = (weekly_correct / weekly_questions * 100) if weekly_questions > 0 else 0
            
            # Generate charts
            topic_chart = self.plot_topic_mastery()
            learning_curve = self.plot_learning_curve()
            heatmap = self.plot_topic_heatmap()
            
            # Convert chart data to base64 for embedding
            topic_chart_b64 = base64.b64encode(topic_chart).decode('utf-8') if topic_chart else None
            learning_curve_b64 = base64.b64encode(learning_curve).decode('utf-8') if learning_curve else None
            heatmap_b64 = base64.b64encode(heatmap).decode('utf-8') if heatmap else None
            
            # Compile report
            report = {
                'overall': overall,
                'topic_mastery': topic_mastery,
                'recent': recent,
                'weekly': {
                    'questions': weekly_questions,
                    'correct': weekly_correct,
                    'accuracy': weekly_accuracy
                },
                'session_history': sessions,
                'charts': {
                    'topic_chart': topic_chart_b64,
                    'learning_curve': learning_curve_b64,
                    'heatmap': heatmap_b64
                }
            }
            
            logger.info("Generated progress report")
            return report
            
        except Exception as e:
            logger.error(f"Error generating progress report: {e}", exc_info=True)
            return {}
    
    def export_report_pdf(self, output_path=None):
        """
        Export progress report as PDF.
        
        Args:
            output_path (str, optional): Output file path
            
        Returns:
            tuple: (success, message, file_path)
        """
        try:
            # Generate the report data
            report = self.generate_progress_report()
            
            # Set default output path if not provided
            if output_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_path = os.path.join(self.exports_dir, f"progress_report_{timestamp}.pdf")
            
            # Note: This is a placeholder for PDF generation.
            # In a full implementation, you would use a library like reportlab or weasyprint.
            # For now, we'll just use matplotlib to create a simple PDF.
            
            # Create a multi-page figure
            fig = plt.figure(figsize=(8.5, 11), dpi=100)
            
            # Add title
            plt.suptitle('BubiQuizPro: Progress Report', fontsize=16)
            plt.figtext(0.5, 0.95, datetime.now().strftime("%Y-%m-%d"), 
                      ha='center', fontsize=10)
            
            # Add summary statistics
            plt.figtext(0.1, 0.85, 'Summary Statistics', fontsize=14)
            
            stats_text = [
                f"Total Sessions: {report['overall'].get('total_sessions', 0)}",
                f"Total Questions Answered: {report['overall'].get('total_questions_answered', 0)}",
                f"Overall Accuracy: {report['overall'].get('overall_accuracy', 0):.1f}%",
                f"Time Spent: {report['overall'].get('total_time_spent_minutes', 0)} minutes",
                f"Topics Mastered: {report['overall'].get('topics_mastered', 0)} of {report['overall'].get('topics_count', 0)}"
            ]
            
            for i, line in enumerate(stats_text):
                plt.figtext(0.1, 0.8 - i * 0.03, line, fontsize=10)
            
            # Save the PDF
            plt.savefig(output_path)
            plt.close(fig)
            
            logger.info(f"Exported progress report PDF: {output_path}")
            return True, "Progress report exported successfully", output_path
            
        except Exception as e:
            logger.error(f"Error exporting progress report PDF: {e}", exc_info=True)
            return False, f"Error: {str(e)}", None
    
    def create_tk_image(self, img_data, size=None):
        """
        Create a Tkinter-compatible image from PNG image data.
        
        Args:
            img_data (bytes): PNG image data
            size (tuple, optional): Resize dimensions (width, height)
            
        Returns:
            ImageTk.PhotoImage: Tkinter-compatible image
        """
        try:
            # Create PIL Image from bytes
            image = Image.open(io.BytesIO(img_data))
            
            # Resize if needed
            if size:
                image = image.resize(size, Image.LANCZOS)
            
            # Convert to Tkinter-compatible image
            return ImageTk.PhotoImage(image)
            
        except Exception as e:
            logger.error(f"Error creating Tkinter image: {e}", exc_info=True)
            return None