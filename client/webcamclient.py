# MODIFIED FROM:
# https://github.com/mandrelbrotset/udp-video-streaming/blob/master/udp_client.py
import cv2
import socket
import math
import pickle
import sys

# configure recipient host/port (server websocket)
max_length = 65540
host = sys.argv[1]
port = 5000


def send_webcam_stream():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

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

            num_of_packs = 1
            if buffer_size > max_length:
                num_of_packs = math.ceil(buffer_size / max_length)

            frame_info = {"packs": num_of_packs}
            sock.sendto(pickle.dumps(frame_info), (host, port))

            left = 0
            right = max_length

            for i in range(num_of_packs):
                data = buffer[left:right]
                left = right
                right += max_length

                # send the frames accordingly
                sock.sendto(data, (host, port))

        ret, frame = cap.read()

    print("☎️ Quitting client...")


if __name__ == "__main__":
    send_webcam_stream()
