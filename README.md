# Muruthi - Personal Life Intelligence System

Muruthi is a personal life intelligence system that observes behavior, understands patterns, and guides better decisions.

In simple words: Muruthi helps a person see how they live and choose a better path.

## North Star

Muruthi must help the user answer one question every day:

"What should I do next to improve my life outcomes?"

Everything in the system exists to answer this question.

## Core Objectives

1. Observe Life (Data Capture)
- Automatically track how time is spent: apps, windows, work vs distraction, routines.
- Goal: understand what the user actually does, not what they think they do.

2. Remember Life (Central Memory)
- Store daily activity history, trends, cycles, and behavior changes.
- Goal: build a long-term memory over weeks and months.

3. Understand Patterns (Analysis)
- Detect focus windows, distraction triggers, momentum shifts, and habit loops.
- Goal: transform raw events into meaningful understanding.

4. Guide Decisions (Recommendations)
- Provide practical daily guidance based on observed behavior.
- Goal: help users choose better next actions.

## MVP Goal

The MVP succeeds when Muruthi reliably does this:
- Track laptop activity
- Store the data locally
- Categorize activity
- Show daily summary
- Give one actionable recommendation

Example output:

Muruthi Daily Insight

Coding: 2h 40m  
Research: 1h 20m  
Social Media: 1h 50m

Muruthi guidance: Social media exceeded productive work today. Reduce it tomorrow morning to improve focus.

## What Muruthi Is Not

- Not a to-do list app
- Not a calendar replacement
- Not a task manager
- Not a generic productivity tracker

Muruthi is a life intelligence system focused on guidance, not task administration.

## Design Principle

Less tracking, more understanding.

The goal is guidance, not just data.

## Data Capture Mission

The Muruthi data capture layer passively collects high-signal behavioral data from user devices, normalizes it into a unified timeline, and provides the foundation for life pattern analysis and decision guidance.

Data capture in Muruthi should be:
- Automatic
- Lightweight
- Accurate enough for behavioral analysis
- Privacy-conscious
- Cheap to run
- Easy to extend later

Muruthi captures signals, not noise.

## Features

- Activity Tracking - Windows desktop activity capture using local monitor
- Local Storage - SQLite database, no cloud dependency
- Smart Categorization - 11 activity categories (coding, research, social_media, entertainment, communication, study, writing, business, finance, idle, other)
- Daily Insights - one recommendation generated from daily behavior patterns
- Desktop UI - Tkinter-based dashboard with daily summaries and guidance
- Modular Architecture - collector, memory, analysis, and guide layers

## Architecture

Muruthi is built in 4 layers:

```
Collector Layer  → Local activity monitor
    ↓
Memory Layer     → SQLite Database + Normalization
    ↓
Mind Layer       → Categorization + Analysis
    ↓
Guide Layer      → Recommendations + Dashboard
```

## Data Capture Layers

1. Activity Events
- app name, window title, start time, end time, duration, source

2. Idle and Active State
- active, idle, locked or inactive state estimation

3. Categorized Behavior
- raw events mapped to coding, research, social_media, entertainment, communication, study, writing, business, finance, idle, other

4. Context Signals
- time of day, weekday or weekend, online or offline state, battery and AC power

5. Outcome Markers
- behavior-to-outcome links such as commits, completed goals, measurable progress

6. Manual Major Events
- optional major life events that cannot be inferred from screen activity alone

## MVP Data Capture Scope

Must capture:
- active app and window
- timestamped duration
- idle or inactive periods
- source and device-local event timeline
- device id and context signals

Must produce:
- daily totals by app
- daily totals by category
- focus vs distraction estimate
- top 5 activities

## Project Structure

```
muruthi/
├── app/
│   ├── main.py                          # Tkinter desktop app entry point
│   ├── collectors/
│   │   └── local_monitor.py             # Windows foreground app/window tracking
│   ├── database/
│   │   ├── db.py                        # SQLite manager
│   │   └── models.py                    # Activity/Summary models
│   ├── analysis/
│   │   ├── normalizer.py               # Event normalization
│   │   ├── categorizer.py              # 11-category classifier
│   │   └── recommender.py              # Rule-based recommendations
│   └── config/
│       └── settings.py                 # Configuration
├── data/                                # SQLite database location
├── muruthi.py                           # Launcher
├── requirements.txt                     # Python dependencies
└── README.md                            # This file
```

## Getting Started

### Prerequisites

- Python 3.8+ installed

### Installation

1. **Clone or set up the project**
```bash
cd muruthi
```

2. **Create virtual environment (optional but recommended)**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure (optional)**
- Default database path: `data/muruthi.db`

### Running the Application

Launch the desktop app:
```bash
python muruthi.py
```

This opens the Muruthi window with:
- Dashboard tab - current activity and daily stats
- Activities tab - recent activity list with categorization
- Summary tab - daily breakdown by category and app
- Daily Insight tab - one prioritized recommendation
- Life & Outcomes tab - manual life events and outcome markers

## How It Works

### 1. Collection
Muruthi reads active application and window title locally from the desktop session.

The collector tracks:
- Active window title
- Application name
- Timestamps and duration
- System state (active, idle, locked_or_offline)
- Device and context signals (battery, AC power, online state, time segment)

### 2. Normalization
Raw collector events are converted to internal schema:
- Clean app names (e.g., "Google Chrome" → "chrome")
- Standard timestamps
- Duration calculation
- Session-aware aggregation for efficient writes
- Filtering of low-value noise
- Idle and inactive period handling

### 3. Categorization
Activities are classified into 11 categories using keyword matching:

| Category | Examples |
|----------|----------|
| **coding** | vscode, pycharm, terminal, git, docker |
| **research** | stackoverflow, medium, documentation, arxiv |
| **social_media** | facebook, twitter, reddit, instagram, discord |
| **entertainment** | youtube, netflix, spotify, games |
| **communication** | zoom, slack, email, teams |
| **study** | coursera, duolingo, classroom |
| **writing** | word, notion, docs, onenote |
| **business** | jira, salesforce, crm, hubspot |
| **finance** | quickbooks, banking, budget, tax |
| **idle** | screensaver, lock, blank screen |
| **other** | uncategorized |

### 4. Recommendations
Daily rules generate 1 recommendation:
- 🎯 **Momentum** - If coding/study > 4h, preserve focus
- ⚠️ **Distractions** - If social > 2h AND coding < 1h, reduce distractions
- ☕ **Break Reminder** - If focus session > 90min, take a break
- 📚 **Learning** - If study/research < 30m, invest in learning
- 🎮 **Balance** - If entertainment > coding, balance work/life
- 🚀 **Communication** - If meetings dominate, block focus time

## Database Schema

### activities
Core normalized activity events:
- `id` - Primary key
- `source` - Data source (local_monitor, future sources)
- `device_id` - Device identifier
- `app_name` - Application name
- `window_title` - Window title
- `url_domain` - Extracted domain for browser events when available
- `category` - Activity category
- `activity_type` - active or idle
- `system_state` - active, idle, locked_or_offline
- `start_time` - Activity start
- `end_time` - Activity end
- `duration_seconds` - Duration
- `time_of_day` - morning/afternoon/evening/night
- `weekday_name` - day name
- `is_weekend` - weekend flag
- `battery_percent` - battery context signal
- `on_ac_power` - charging context signal
- `is_online` - network context signal
- `raw_data_json` - Original event data
- `created_at` - When stored

### daily_summaries
Aggregated daily data:
- `date` - ISO date
- `total_active_time` - Total tracked seconds
- `activity_count` - Number of activities
- `top_category` - Most common category
- `category_breakdown` - JSON dict of category → seconds
- `top_app` - Most used app

### daily_recommendations
Daily insights:
- `date` - ISO date
- `title` - Short title
- `description` - Full recommendation text
- `category` - Relevant category
- `priority` - high/normal/low

### outcome_markers
Outcome signals linked to behavior:
- `date` - ISO date
- `marker_type` - e.g., git_commits, tasks_completed
- `marker_value` - numeric value
- `unit` - count/hours/amount
- `source` - local_git/manual/etc.
- `note` - metadata

### life_events
Optional major manual life context:
- `event_date` - ISO date
- `title` - event title
- `description` - context detail
- `event_type` - work/health/family/travel/etc.
- `impact_level` - low/medium/high

## Configuration

Create `.env` to customize:

```bash
# Database
DB_PATH=data/muruthi.db

# UI
THEME=light
LANGUAGE=en

# Debugging
DEBUG=false
```

## Extending Muruthi

### Add a Category
Edit `app/analysis/categorizer.py` → `_build_rules()` dict:
```python
"mycategory": ["keyword1", "keyword2", "app_name"],
```

### Add a Recommendation Rule
Edit `app/analysis/recommender.py` → `generate_recommendation()`:
```python
if some_metric > threshold:
    recommendation = DailyRecommendation(...)
    candidates.append((recommendation, weight))
```

### Add a Data Source
Create `app/collectors/my_collector.py`:
```python
class MyCollector:
    def fetch_events(self, start, end):
        # Return list of events
        pass
```

## Troubleshooting

**"No activities showing"**
- Keep Muruthi open for 1-2 minutes so activity logging can accumulate entries
- Ensure the current foreground window is not minimized or a system lock screen

**"Database already exists"**
- Delete `data/muruthi.db` to reset or export data first

**Import errors**
- Ensure `requirements.txt` is installed: `pip install -r requirements.txt`
- Verify Python 3.8+ is active: `python --version`

## Road Map

Phase 1 (MVP): reliable local tracking, summaries, and one daily recommendation

Phase 2: deeper pattern modeling, life-state transitions, and better long-horizon insights

Phase 3: outcome simulation and probability-guided recommendations (Markov-chain inspired)

## Development

**Project Values:**
- 🔒 **Local-first** - All data stays on your machine
- 🤏 **Minimal** - Start small, add features carefully
- 📖 **Readable** - Code over cleverness
- 🔧 **Modular** - Easy to replace components
- 🚀 **Practical** - Focus on real problems

## License

Open source. Use, modify, share freely.
- ActivityWatch (running locally on port 5600)
- Windows, macOS, or Linux

## Installation

1. Clone or download this project:
```bash
cd muruthi
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root for custom settings:

```env
# ActivityWatch connection
AW_HOST=localhost
AW_PORT=5600
AW_ENABLED=true

# Database
DB_PATH=data/muruthi.db

# UI
THEME=light
LANGUAGE=en

# Debug mode
DEBUG=false
```

## Running the Application

Start the application:

```bash
python -m app.main
```

Or directly:

```bash
python app/main.py
```

**Important:** Make sure ActivityWatch is running before starting Muruthi. ActivityWatch runs on `http://localhost:5600` by default.

## Quick Start

1. Ensure ActivityWatch is installed and running
2. Create virtual environment and install dependencies
3. Run `python app/main.py`
4. Click "Sync from ActivityWatch" to import your activity data
5. View your activities in the dashboard

## Next Steps

- [ ] Implement data synchronization with ActivityWatch
- [ ] Add time-series visualization charts
- [ ] Build automatic categorization engine
- [ ] Create activity reports and insights
- [ ] Add support for multiple data sources
- [ ] Implement performance analytics
- [ ] Add export functionality (CSV, PDF)

## Development Notes

- All modules are independent and can be extended individually
- Database is fully typed with dataclass models in `models.py`
- Settings use environment variables for flexibility
- UI uses Qt signals/slots pattern for responsiveness

## License

MIT License - Feel free to use and modify!

---

**Made with ❤️ for better life tracking and self-awareness.**
