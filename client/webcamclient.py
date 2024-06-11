import socket
import cv2
import pickle
import sys

# configure recipient host/port (server websocket)
host = sys.argv[1]
port = 5000


def send_webcam_stream():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))

    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()

    print("➡️ Streaming webcam to: {}:{}...".format(host, port))
    while ret:
        # compress frame
        retval, buffer = cv2.imencode(".jpg", frame)

        if retval:
            # convert to byte array
            buffer = buffer.tobytes()
            # get size of the frame
            buffer_size = len(buffer)

            # send size of the frame
            sock.sendall(pickle.dumps(buffer_size))

            # send the frame
            sock.sendall(buffer)

        ret, frame = cap.read()

    print("☎️ Quitting client...")
    sock.close()
