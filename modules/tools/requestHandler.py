import requests

class BurpRequest:

    def __init__(self, file_path):
        self.ssl = True
        self.file_path = file_path
        self.method = None
        self.url = None
        self.headers = {}
        self.body = ""
        self.hostname = None
        self.load_request()

    def load_request(self):
        with open(self.file_path, 'r') as file:
            lines = file.readlines()
            self.parse_request(lines)

    def parse_request(self, lines):
        request_line = lines[0].strip().split()
        self.method = request_line[0]
        self.url = request_line[1]

        header_section = True
        for line in lines[1:]:
            if header_section:
                if line.strip() == '':
                    header_section = False
                    continue
                header_key, header_value = line.split(':', 1)
                self.headers[header_key] = header_value.strip()
            else:
                if self.body is None:
                    self.body = line
                else:
                    self.body += line
        self.hostname = self.headers.get("Host","")

    def send_request(self,failover:bool=False,parameters:list=[]):
        protocol = "https://" if self.ssl else "http://"
        url = protocol+self.hostname+self.url
        headers = self.headers
        body = self.body
        if parameters:
            for parameter in parameters:
                url = url.replace(parameter[0],parameter[1])
                body = body.replace(parameter[0],parameter[1])
        try:
            if self.method == 'GET':
                response = requests.get(url, headers=headers, data=body, timeout=(5,15))
            elif self.method == 'POST':
                response = requests.post(url, headers=headers, data=body, timeout=(5,15))
            elif self.method == 'PUT':
                response = requests.put(url, headers=headers, data=body, timeout=(5,15))
            elif self.method == 'DELETE':
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f'Unsupported HTTP method: {self.method}')
        except requests.exceptions.SSLError as e:
            self.ssl = False
            if not failover:
                return self.send_request(failover=True,parameters=parameters)
            print(f"[!] Connection Failed with {self.headers.get('Host')}            ")
            return ""
        except requests.exceptions.ConnectionError:
            self.ssl = False if self.ssl else True
            if not failover:
                return self.send_request(failover=True,parameters=parameters)
            print(f"[!] Connection Failed with {self.headers.get('Host')}             ")
            return ""
        return response

