# Web Crawler Project

## Description
This project contains a web crawler that collects datasets from specified websites based on keywords and stores the data in a CSV file and a PostgreSQL database. The crawler can be scheduled to run at regular intervals.

## Directory Structure
- `config/`: Contains the configuration file.
- `logs/`: Stores log files.
- `scripts/`: Contains the main and utility scripts.
- `datasets/`: Stores the output CSV files.
- `requirements.txt`: Lists the project dependencies.
- `run_crawler.sh`: Shell script to run the crawler.

## Setup

1. **Clone the repository**:
    ```sh
    git clone https://github.com/your-repo/web_crawler_project.git
    cd web_crawler_project
    ```

2. **Set up a virtual environment** (optional but recommended):
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install dependencies**:
    ```sh
    pip install -r requirements.txt
    ```

4. **Configure the crawler**:
    - Edit the `config/config.json` file with your websites, keywords, database configuration, and other settings.

5. **Run the crawler**:
    ```sh
    ./run_crawler.sh
    ```

## Usage

You can run the web crawler from the command line with different options:

```sh
python scripts/web_crawler.py --query "<your-query>" --mode "<images|datasets>" --limit <number> --schedule "<daily|weekly>"
