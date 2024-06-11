# This is server code to send video frames over UDP
import cv2, imutils, socket
import numpy as np
import time
import base64


# source:
# https://pyshine.com/Send-video-over-UDP-socket-in-Python/
def send_webcam_stream():
    try:
        BUFF_SIZE = 65536
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, BUFF_SIZE)

        host_ip = "192.168.1.152"
        port = 5000
        socket_address = (host_ip, port)
        server_socket.bind(socket_address)
        print("🔌 Websocket listening at:", socket_address)

        vid = cv2.VideoCapture(0)
        fps, st, frames_to_count, cnt = (0, 0, 20, 0)

        while True:
            msg, client_addr = server_socket.recvfrom(BUFF_SIZE)
            print("☎️ GOT connection from ", client_addr)
            WIDTH = 400
            while vid.isOpened():
                _, frame = vid.read()
                frame = imutils.resize(frame, width=WIDTH)
                encoded, buffer = cv2.imencode(
                    ".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80]
                )
                message = base64.b64encode(buffer)
                server_socket.sendto(message, client_addr)
                frame = cv2.putText(
                    frame,
                    "FPS: " + str(fps),
                    (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 0, 255),
                    2,
                )
                cv2.imshow("➡️ TRANSMITTING VIDEO", frame)
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    server_socket.close()
                    break
                if cnt == frames_to_count:
                    try:
                        fps = round(frames_to_count / (time.time() - st))
                        st = time.time()
                        cnt = 0
                    except:
                        pass
                cnt += 1
    except Exception as e:
        if e == KeyboardInterrupt:
            print("☎️ Quitting client...")
            vid.release()
            cv2.destroyAllWindows()
            server_socket.close()
        else:
            print("⚠️ Error: ", e)


if __name__ == "__main__":
    send_webcam_stream()


# import socket
# import cv2
# import pickle
# import sys

# # configure recipient host/port (server websocket)
# host = sys.argv[1]
# port = 5000


# def send_webcam_stream():
#     sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     sock.connect((host, port))

#     cap = cv2.VideoCapture(0)
#     ret, frame = cap.read()

#     print("➡️ Streaming webcam to: {}:{}...".format(host, port))
#     while ret:
#         # compress frame
#         retval, buffer = cv2.imencode(".jpg", frame)

#         if retval:
#             # convert to byte array
#             buffer = buffer.tobytes()
#             # get size of the frame
#             buffer_size = len(buffer)

#             # send size of the frame
#             sock.sendall(pickle.dumps(buffer_size))

#             # send the frame
#             sock.sendall(buffer)

#         ret, frame = cap.read()

#     print("☎️ Quitting client...")
#     sock.close()
