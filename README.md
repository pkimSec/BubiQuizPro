# BubiQuizPro

A comprehensive self-study quiz application designed for efficient learning and exam preparation.

## Features

- **Multiple Question Types**: Supports multiple-choice and text questions
- **Intelligent Learning**: Implements spaced repetition algorithm for optimized learning
- **Flexible Filtering**: Filter questions by subject, script, topic, and difficulty level
- **Progress Tracking**: Detailed statistics and visualizations of your learning progress
- **Customizable**: Adjustable settings to match your learning preferences

## Installation

### Requirements

- Python 3.12 or higher
- Required libraries: Tkinter, Matplotlib, Pillow

### Setup

1. Clone or download this repository
2. Install required dependencies:
   ```
   pip install matplotlib pillow
   ```
3. Run the application:
   ```
   python main.py
   ```

## Usage

### Importing Questions

BubiQuizPro uses a standardized JSON format for questions. You can import questions using the Import/Export tab.

Example JSON format:

```json
{
  "metadata": {
    "version": "1.0",
    "source": "Vorlesungsskript Analysis",
    "created_by": "Author Name",
    "creation_date": "2025-03-15",
    "topics": ["Analysis", "Differentialrechnung"]
  },
  "questions": [
    {
      "id": "q001",
      "type": "multiple_choice",
      "difficulty": "mittel",
      "topics": ["Differentialrechnung", "Ableitungsregeln"],
      "question": "Welche Regel beschreibt die Ableitung eines Produkts zweier Funktionen?",
      "options": [
        "Summenregel: (f + g)' = f' + g'",
        "Produktregel: (f·g)' = f'·g + f·g'",
        "Kettenregel: (f∘g)' = (f'∘g)·g'",
        "Quotientenregel: (f/g)' = (f'·g - f·g')/g²"
      ],
      "correct_answer": 1,
      "explanation": "Die Produktregel besagt, dass die Ableitung eines Produkts zweier Funktionen gleich der Summe aus dem Produkt der Ableitung der ersten Funktion mit der zweiten Funktion und dem Produkt der ersten Funktion mit der Ableitung der zweiten Funktion ist.",
      "source_reference": "Skript 2, Seite 45"
    },
    {
      "id": "q002",
      "type": "text",
      "difficulty": "schwer",
      "topics": ["Grenzwerte", "Stetigkeit"],
      "question": "Erklären Sie den Zusammenhang zwischen Stetigkeit und Differenzierbarkeit einer Funktion.",
      "model_answer": "Eine differenzierbare Funktion ist immer stetig, aber eine stetige Funktion muss nicht differenzierbar sein. Differenzierbarkeit in einem Punkt bedeutet, dass die Funktion dort eine eindeutige Tangente besitzt, was automatisch Stetigkeit impliziert. Ein Gegenbeispiel ist die Betragsfunktion f(x)=|x| bei x=0, die stetig, aber nicht differenzierbar ist, da sie dort einen Knick aufweist.",
      "keywords": ["Stetigkeit", "Differenzierbarkeit", "Tangente", "Knick", "Betragsfunktion"],
      "source_reference": "Skript 1, Seite 28-30"
    }
  ]
}
```

### Quiz Modes

- **Normal Quiz**: Answer questions based on your selection criteria
- **Weak Spots**: Focus on questions you've had trouble with
- **Spaced Repetition**: Optimally scheduled review for long-term memory
- **Exam Mode**: Simulate an exam with time limit

### Statistics

The Statistics tab provides detailed insights into your learning progress:
- Overall performance metrics
- Topic mastery visualization
- Learning progress over time
- Session history

### Settings

Customize the application to your preference through the Settings tab:
- General application behavior
- Quiz settings and answer evaluation
- Display preferences and theme

## Project Structure

```
bubiquizpro/
├── main.py                # Main application entry point
├── data/                  # Data directory
│   ├── questions/         # Imported question files
│   ├── user_progress.db   # SQLite database for progress
│   └── exports/           # Exported files
├── modules/               # Core functionality modules
│   ├── __init__.py        # Package initialization
│   ├── data_manager.py    # Data management operations
│   ├── quiz_engine.py     # Quiz logic and algorithms
│   └── stats_manager.py   # Statistics and visualization
├── ui/                    # User interface components
│   ├── __init__.py        # Package initialization
│   ├── main_window.py     # Main application window
│   ├── question_frame.py  # Question display UI
│   ├── stats_frame.py     # Statistics UI
│   └── settings_frame.py  # Settings UI
└── logs/                  # Application logs
```

## License

This project is open-source software.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.