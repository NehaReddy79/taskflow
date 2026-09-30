import time
import random
def handle_send_email(payload):
    print(f"Sending email to {payload.get('to')}")
    time.sleep(1)

def handle_resize_image(payload):
    print(f"Resizing image {payload.get('filename')}")
    time.sleep(1)
    if random.random() < 0.5:
        raise Exception("Image resize failed")

HANDLERS = {
    "send_email" : handle_send_email,
    "resize_image" : handle_resize_image,
}