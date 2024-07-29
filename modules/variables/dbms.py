### Host Class ###
class Host:
# Host initialization
    def __init__(self,name:str):
        if name:
            self.name = name
            self.databases = {}
        else:
            raise ValueError("[!] Host Should Not Be Empty!")
# Host Representation
    def __repr__(self):
        return self.name
# Database Class
    class Database:
    # Database Intialization
        def __init__(self,name:str):
            self.name = name
            self.tables = {}
    # Database Representation
        def __repr__(self):
            return self.name
    # Table Class
        class Table:
        # Table Initialization
            def __init__(self,name:str):
                self.name = name
                self.columns = []
                self.records = []
                self.total_rows = "Not Checked"
                self.avg_row_length = "Not Checked"
                self.data_length = "Not Checked"
                self.create_time = "Not Checked"
        # Table Representation
            def __repr__(self):
                return self.name
        # Number of Records in Table
            def __len__(self):
                return len(self.records)
        # Table Handler
            def handler(self,information):
                if len(information)==5:
                    self.columns = information[0].split(":")
                    self.total_rows = information[1]
                    self.avg_row_length = information[2]
                    self.data_length = information[3]
                    self.create_time = information[4]
        # Table Info Method
            def info(self):
                return {"total_rows":self.total_rows,"avg_row_length":self.avg_row_length,"data_length":self.data_length,"create_time":self.create_time,"columns":self.columns}
        # Show Records Method
            def show_records(self,limit:int=20):
                print("\t".join(self.columns))
                for record in self.records[:limit]:
                    print("\t".join(record))
    # Tables Iteration 
        def __iter__(self):
            self.index = 0
            self.keys = list(self.tables.keys())
            return self
        def __next__(self):
            if self.index<len(self.keys):
                result = self.tables[self.keys[self.index]]
                self.index+=1
                return result
            else:
                raise StopIteration
    # Table Access
        def __getitem__(self,key):
            if key:
                return self.tables.get(key,None)
            else:
                raise ValueError("[!] Table Name Must not be empty!")
        def get(self,key):
            if key:
                return self.tables.get(key,None)
            else:
                raise ValueError("[!] Table Name Must not be empty!")
        # def test(self):
        #     for a in self.tables.keys():
        #         print(f"${a}$")
        #         print(f"${self.tables[a]}$")
    # Number of Tables
        def __len__(self):
            return len(self.tables)
    # Table Creation Method
        def addTable(self,name:str):
            if name and not self[name]:
                self.tables[name] = self.Table(name)
    # Table Handler
        def handler(self,information:list):
            if information:
                self.addTable(name=information[0])
                self[information[0]].handler(information[1:])
# Database Iteration 
    def __iter__(self):
        self.index = 0
        self.keys = list(self.databases.keys())
        return self
    def __next__(self):
        if self.index<len(self.keys):
            result = self.databases[self.keys[self.index]]
            self.index+=1
            return result
        else:
            raise StopIteration
# Database Access
    def __getitem__(self,key):
        if key:
            return self.databases.get(key,None)
        else:
            raise ValueError("[!] Database Name Must not be empty!")
    def get(self,key):
        if key:
            return self.databases.get(key,None)
        else:
            raise ValueError("[!] Database Name Must not be empty!")
# Number of Databases
    def __len__(self):
        return len(self.databases)
# Database Creation Method
    def addDatabase(self,name:str):
        if name and not self[name]:
            self.databases[name] = self.Database(name)
# Database Handler
    def handler(self,data:list):
        if data:
            if type(data[0])==str:
                for dbname in data:
                    self.addDatabase(dbname)
            elif type(data[0])==list and len(data[0])==7:
                for information in data:
                    self.addDatabase(information[0])
                    self[information[0]].handler(information[1:])
            else:
                raise ValueError("[!] Host is unable to handle data!")

if __name__=="__main__":
    localhost = Host("localhost")
    data = [['mysql', 'func', 'dl:name:type:ret', '0', '0', '8192', '2024-05-26 23:20:54'],
            ['mysql', 'global_priv', 'Priv:Host:User', '6', '2730', '16384', '2024-05-26 23:20:57']]
    localhost.handler(data)
    for db in localhost:
        print("Database: -",db)
        for tb in db:
            print("[*] Table -",tb,tb.info())