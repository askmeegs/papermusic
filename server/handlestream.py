from PIL import Image
import asyncio
import cv2
import numpy as np
import socket
import struct


# prepare to receive mac webcam stream
host = "0.0.0.0"
port = 5000
max_length = 10000


async def listen():
    print("enter Listen")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(1)

    print("🤔 Listening for stream {}:{}...".format(host, port))

    conn, addr = sock.accept()
    print("✅ Connection from: ", addr)

    j = 0
    while True:
        try:
            # receive size of the frame
            buffer_size = conn.recv(4)
            buffer_size = struct.unpack("!I", buffer_size)[0]

            # receive the frame
            buffer = b""
            while len(buffer) < buffer_size:
                packet = conn.recv(buffer_size - len(buffer))
                if not packet:
                    break
                buffer += packet

            frame = np.frombuffer(buffer, dtype=np.uint8)
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            frame = cv2.flip(frame, 1)

            if frame is not None and type(frame) == np.ndarray:
                if cv2.waitKey(1) == 27:
                    break
                # if j is a multiple of 2, save frame
                if j % 2 == 0:
                    cv2.imwrite(f"framecapture/frame_{j}.jpg", frame)
                    print("📸 Saved frame: framecapture/frame_{}.jpg".format(j))
                j += 1

        except Exception as e:
            continue


if __name__ == "__main__":
    asyncio.run(listen())
