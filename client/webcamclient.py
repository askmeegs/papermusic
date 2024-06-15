import socket
import cv2
import struct
import sys
import time

# configure recipient host/port (server websocket)
host = sys.argv[1]
port = 5000


def send_webcam_stream():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((host, port))
        print("📡 Connected to server: {}:{}".format(host, port))
        cap = cv2.VideoCapture(0)
        print("➡️ Streaming webcam to: {}:{}...".format(host, port))
        ret, frame = cap.read()
    except Exception as e:
        print("❌ Error connecting to server: {}".format(e))
        return
    print("Sending stream...")
    while ret:
        try:
            # compress frame
            retval, buffer = cv2.imencode(".jpg", frame)

            if retval:
                # convert to byte array
                buffer = buffer.tobytes()
                # get size of the frame
                buffer_size = len(buffer)

                # send size of the frame
                sock.sendall(struct.pack("!I", buffer_size))

                # send the frame
                sock.sendall(buffer)
                # print("🟪 Sent frame of buffer_size: {}".format(buffer_size))

            ret, frame = cap.read()
            time.sleep(0.4)
        except Exception as e:
            print("❌ Error sending frame... {}".format(e))
            continue

    print("☎️ Quitting client...")
    sock.close()


if __name__ == "__main__":
    send_webcam_stream()
