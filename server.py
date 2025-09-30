import os
import socket
from datetime import datetime
import cgi  
import io

class SocketServer:
    def __init__(self):
        self.bufsize = 1024  # 버퍼 크기 설정  
        with open('./response.bin', 'rb') as file:
            self.RESPONSE = file.read()  # 응답 파일 읽기

        self.DIR_PATH = './request'
        self.IMG_DIR_PATH = './images'
        self.createDir(self.DIR_PATH)
        self.createDir(self.IMG_DIR_PATH)

    def createDir(self, path):
        """디렉토리 생성"""
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError:
            print(f"Error: Failed to create the directory.")

    def run(self, ip, port):
        """서버 실행"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((ip, port))
        self.sock.listen(10)
        print("Start the socket server...")
        print("\"Ctrl+C\" for stopping the server!\r\n")

        try:
            while True:
                clnt_sock, req_addr = self.sock.accept()
                clnt_sock.settimeout(5.0)
                print(f"Request from {req_addr}...")

                try:
                    raw_request = b''
                    headers_part = b''

                    while b'\r\n\r\n' not in headers_part:
                        part = clnt_sock.recv(self.bufsize)
                        if not part: break
                        headers_part += part
                    
                    header_end_idx = headers_part.find(b'\r\n\r\n')
                    body_part = headers_part[header_end_idx+4:]
                    headers_part = headers_part[:header_end_idx]

                    headers_str = headers_part.decode('utf-8', errors='ignore')
                    content_length = 0
                    content_type = ''
                    for line in headers_str.split('\r\n'):
                        if line.lower().startswith('content-length:'):
                            content_length = int(line.split(':')[1].strip())
                        if line.lower().startswith('content-type:'):
                            content_type = line.split(':')[1].strip()

                    while len(body_part) < content_length:
                        part = clnt_sock.recv(self.bufsize)
                        if not part: break
                        body_part += part

                    raw_request = headers_part + b'\r\n\r\n' + body_part

                    timestamp = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
                    req_filename = f"{timestamp}.bin"
                    req_filepath = os.path.join(self.DIR_PATH, req_filename)
                    with open(req_filepath, 'wb') as f:
                        f.write(raw_request)
                    print(f"  - Request saved to {req_filepath}")

                    if 'multipart/form-data' in content_type:
                        fp = io.BytesIO(body_part)
                        fs = cgi.FieldStorage(
                            fp=fp,
                            headers={'content-type': content_type},
                            environ={'REQUEST_METHOD': 'POST'}
                        )

                        for field in fs.keys():
                            item = fs[field]
                            if item.filename:
                                img_filename = item.filename
                                img_filepath = os.path.join(self.IMG_DIR_PATH, img_filename)
                                with open(img_filepath, 'wb') as f:
                                    f.write(item.file.read())
                                print(f"  - Image saved to {img_filepath}")

                except Exception as e:
                    print(f"Error processing request: {e}")

                # 응답 전송
                clnt_sock.sendall(self.RESPONSE)

                # 클라이언트 소켓 닫기
                clnt_sock.close()
                print("Response sent and connection closed.\r\n")

        except KeyboardInterrupt:
            print("\r\nStop the server...")
            
        finally:
            # 서버 소켓 닫기
            self.sock.close()

if __name__ == "__main__":
    server = SocketServer()
    server.run("127.0.0.1", 8000)