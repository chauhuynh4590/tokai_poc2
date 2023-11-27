import queue
import threading
import time
import cv2


class CVFreshestFrame:
    """
    always getting the most recent frame of a camera
    """

    def __init__(self, source, fps=30):
        # self.cap = cv2.VideoCapture(source)
        self.cap = source
        self.W = int(source.get(3))
        self.H = int(source.get(4))
        self.running = True
        self.fps = fps
        self.q = queue.Queue()
        self.t = threading.Thread(target=self._reader)
        self.t.daemon = True
        self.t.start()

    def release(self):
        # print("RELEASE")
        self.running = False
        self.cap.release()

    # read frames as soon as they are available, keeping only most recent one
    def _reader(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                self.q.put(None)
                self.release()
            if not self.q.empty():
                try:
                    self.q.get_nowait()  # discard previous (unprocessed) frame
                except queue.Empty:
                    pass
            self.q.put(frame)
            time.sleep(1 / self.fps)

    def read(self):
        img = self.q.get(block=True, timeout=10)
        return self.running, img


if __name__ == "__main__":
    pass
