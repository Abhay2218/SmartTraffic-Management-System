# SmartTraffic-Management-System

SmartTraffic is a traffic management and simulation project that applies Operating Systems scheduling algorithms to vehicle queues at road intersections. It combines a C-based scheduling engine, a Flask backend, a MySQL database, and a web-based dashboard to simulate traffic flow and manage traffic signals.

The system models vehicles as processes with arrival times, burst durations, directions, and priorities. It uses scheduling algorithms to determine how vehicles are handled and provides a foundation for adaptive traffic management across multiple junctions.

## Features

- **FCFS Scheduling:** Processes vehicles in arrival order.
- **Priority Scheduling:** Handles vehicles according to priority.
- **Priority Aging:** Improves the effective priority of waiting vehicles to reduce starvation.
- **Round Robin Scheduling:** Allocates processing time using a configurable time quantum.
- **Traffic Signal Management:** Manages signal states and prevents conflicting green signals through controlled state transitions.
- **REST API:** Provides communication between the frontend, backend, and scheduling engine.
- **Database Management:** Stores traffic-related data using a normalized MySQL schema.
- **Interactive Dashboard:** Provides a web interface with junction information, map visualization, and signal monitoring.
- **Transaction Handling:** Uses database transactions to maintain consistency during updates.
- **Testing:** Includes tests for scheduling algorithms, API integration, database integrity, and synchronization.

## Technology Stack

| Technology | Usage |
|---|---|
| C | Scheduling engine |
| Python | Backend logic |
| Flask | REST API |
| MySQL | Data storage |
| HTML and CSS | Web interface |
| JavaScript | Frontend interactions |
| Leaflet.js | Interactive map |
| OpenStreetMap | Map data |
| Git and GitHub | Version control and collaboration |

## System Architecture

```text
                    Web Dashboard
                 HTML / CSS / JavaScript
                           |
                       HTTP / JSON
                           |
                    Flask REST API
                      /         \
                     /           \
             C Scheduling       MySQL
                 Engine        Database
                     \           /
                      \         /
                    Traffic Data
                   and Signal State
```

### How It Works

1. The user interacts with the web dashboard to view junction information and use available controls.
2. The Flask backend receives requests and coordinates application operations.
3. The backend communicates with the C scheduling engine using a JSON-based protocol.
4. The scheduling engine processes vehicle queues using the selected scheduling algorithm.
5. MySQL stores the relevant application data and signal records.
6. The frontend displays available traffic and junction information.

## Scheduling Algorithms

### First Come, First Served (FCFS)

Vehicles are handled in the order of their arrival times. This provides a straightforward scheduling strategy based on arrival order.

### Priority Scheduling with Aging

Vehicles are scheduled according to priority. An aging mechanism increases the effective priority of waiting vehicles to reduce the possibility of indefinite waiting.

### Round Robin (RR)

Vehicles receive processing time according to a configurable time quantum. Vehicles that have remaining burst time return to the queue for subsequent scheduling cycles.

## Database

The application uses MySQL for persistent data storage.

The database design includes:

- 11 normalized relational tables.
- Third Normal Form (3NF) schema design.
- Relational integrity constraints.
- Junction and traffic-related records.
- Signal-phase transition logging.
- Transactional updates and rollback handling.

## Project Structure

The following is a conceptual overview. Actual filenames and directories depend on the repository's current layout.

```text
SmartTraffic-Management-System/
├── C Scheduling Engine
├── Flask Backend
├── MySQL Schema and Seed Data
├── Web Dashboard
├── Tests
├── Documentation
└── README.md
```

## Getting Started

### Prerequisites

Install the following tools:

- Git
- Python and pip
- A compatible C compiler
- MySQL Server
- A modern web browser

### 1. Clone the Repository

```bash
git clone https://github.com/Abhay2218/SmartTraffic-Management-System.git
cd SmartTraffic-Management-System
```

### 2. Set Up the Database

1. Start MySQL Server.
2. Create the database required by the application.
3. Import the project's SQL schema and seed data.
4. Configure the database connection details in the backend configuration.

Use the actual SQL filenames and database settings present in the repository.

### 3. Set Up the Python Environment

Create a virtual environment:

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/macOS**

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies using the repository's dependency file, if available:

```bash
pip install -r requirements.txt
```

### 4. Build the C Scheduling Engine

Compile the C source files using the project's build configuration or provided scripts. Ensure that the executable is available at the path expected by the Flask backend.

### 5. Run the Application

Start the Flask backend and web dashboard using the commands or startup scripts provided in the repository.

Ensure that MySQL is running and the database connection is configured correctly before starting the application.

*Note: Exact build and startup commands should be added after verifying the current repository files.*

## Testing

The project includes testing for the following areas:

- C scheduling algorithms.
- Concurrency and synchronization.
- Database integrity and transaction handling.
- REST API integration.
- Vehicle CRUD operations and boundary cases.

Advanced stress testing and complex traffic scenarios remain areas for further development.

## Future Improvements

- Adaptive scheduling based on traffic density.
- Coordination between multiple junctions.
- Accident and road-closure simulation.
- Traffic rerouting and queue-impact analysis.
- Comparative scheduling analytics.
- Performance optimization and expanded stress testing.

## Repository

GitHub: https://github.com/Abhay2218/SmartTraffic-Management-System

## Contributors

- **Kshitij Kukreti** — C scheduling engine and OS scheduling implementation.
- **Abhay Pratap Singh Negi** — MySQL database schema and seed data.
- **Abhyudya Bhandari** — Flask REST API and backend endpoints.

Contributions to shared scheduling and
