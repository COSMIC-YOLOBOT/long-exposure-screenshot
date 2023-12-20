import tkinter as tk
from tkinter import ttk
import threading
import numpy as np
from PIL import Image, ImageTk
import pyautogui
import time
from datetime import datetime
from tkinter import filedialog


class LongExposureApp(tk.Tk):
    """
    A GUI application for capturing and processing long exposure screenshots.

    Allows users to capture screenshots over a specified duration
    and interval, and then averages these screenshots to create a long exposure effect.
    The user can adjust the gamma value of the resulting image.
    """

    ##########################################################################
    ## Initialization
    ##########################################################################

    def __init__(self):
        super().__init__()
        self.title("Long Exposure Screenshot Tool")

        # Initialize variables
        self.interval = tk.DoubleVar(value=1.0)
        self.duration = tk.IntVar(value=10)
        self.delay = tk.IntVar(value=3)
        self.gamma = tk.DoubleVar(value=1.0)

        self.create_widgets()

    def create_widgets(self):
        # Create and place widgets for the first page
        self.setup_page = ttk.Frame(self)
        ttk.Label(self.setup_page, text="Interval (s):").grid(row=0, column=0)
        ttk.Entry(self.setup_page, textvariable=self.interval).grid(row=0, column=1)
        ttk.Label(self.setup_page, text="Duration (s):").grid(row=1, column=0)
        ttk.Entry(self.setup_page, textvariable=self.duration).grid(row=1, column=1)
        ttk.Label(self.setup_page, text="Delay (s):").grid(row=2, column=0)
        ttk.Entry(self.setup_page, textvariable=self.delay).grid(row=2, column=1)
        ttk.Button(self.setup_page, text="Record", command=self.start_recording).grid(
            row=3, column=0, columnspan=2
        )
        self.setup_page.pack(fill="both", expand=True)

        # Create and place widgets for the second page
        self.record_page = ttk.Frame(self)
        self.countdown_label = ttk.Label(self.record_page, text="Waiting to start...")
        self.countdown_label.pack(pady=20)
        ttk.Button(self.record_page, text="Stop", command=self.stop_recording).pack()

        # Create and place widgets for the third page
        self.preview_page = ttk.Frame(self)
        self.image_label = ttk.Label(self.preview_page)
        self.image_label.pack(pady=20)
        gamma_scale = ttk.Scale(
            self.preview_page,
            from_=0.1,
            to=2.0,
            orient="horizontal",
            variable=self.gamma,
            command=self.on_gamma_change,
        )
        gamma_scale.pack()

        # Gamma text input
        self.gamma_entry = ttk.Entry(self.preview_page, textvariable=self.gamma)
        self.gamma_entry.pack()
        self.gamma_entry.bind(
            "<Return>", self.on_gamma_change
        )  # Update when Enter is pressed
        ttk.Button(self.preview_page, text="Save", command=self.save_image).pack()
        self.save_location_label = ttk.Label(self.preview_page, text="")
        self.save_location_label.pack()
        ttk.Button(
            self.preview_page, text="New Screenshot", command=self.start_new_screenshot
        ).pack()

    ##########################################################################
    ## Screenshot Capture Workflow
    ##########################################################################

    def start_recording(self):
        self.setup_page.pack_forget()
        self.record_page.pack(fill="both", expand=True)
        self.stop_event = threading.Event()
        self.capture_thread = threading.Thread(
            target=self.capture_and_average_screenshots
        )
        self.capture_thread.start()

    def stop_recording(self):
        self.stop_event.set()
        self.capture_thread.join()  # Wait for the capture thread to finish
        self.record_page.pack_forget()
        self.preview_page.pack(fill="both", expand=True)
        # You might want to display the image immediately after stopping
        # self.update_preview(self.gamma.get())

    def capture_and_average_screenshots(self):
        delay_remaining = self.delay.get()
        while delay_remaining > 0:
            self.countdown_label.config(text=f"starting in {delay_remaining}...")
            time.sleep(1)
            delay_remaining -= 1

        self.average_image = None
        frame_count = 0
        start_time = time.time()
        end_time = start_time + self.duration.get()
        self.update_countdown(end_time)

        while time.time() < end_time and not self.stop_event.is_set():
            screenshot = np.array(pyautogui.screenshot())
            if self.average_image is None:
                self.average_image = np.zeros_like(screenshot, dtype=np.float64)

            frame_count += 1
            self.average_image = (
                (frame_count - 1) * self.average_image + screenshot
            ) / frame_count
            time.sleep(self.interval.get())

        # When the capturing is done or stopped, show the preview page
        self.record_page.pack_forget()
        self.preview_page.pack(fill="both", expand=True)
        # Update the preview with the captured image
        self.update_preview(self.gamma.get())

    def update_countdown(self, end_time):
        remaining_time = int(end_time - time.time())
        if remaining_time >= 0:
            self.countdown_label.config(
                text=f"Time remaining: {remaining_time} seconds"
            )
            self.after(1000, lambda: self.update_countdown(end_time))
        else:
            self.countdown_label.config(text="Capturing finished.")

    ##########################################################################
    ## Image Processing and Display
    ##########################################################################

    def apply_gamma_correction(self, image, gamma):
        gamma_corrected = np.power(image / 255.0, gamma) * 255
        return gamma_corrected.clip(0, 255).astype(np.uint8)

    def update_preview(self, gamma_value):
        gamma = float(gamma_value)  # Convert the gamma value to float
        gamma_corrected_image = self.apply_gamma_correction(self.average_image, gamma)

        # Convert the NumPy array to a PIL image
        pil_image = Image.fromarray(gamma_corrected_image)

        # Resize the image to half its size in each dimension
        width, height = pil_image.size
        resized_size = (int(width / 2), int(height / 2))
        resized_image = pil_image.resize(resized_size, Image.BOX)

        # Convert the resized PIL image to a Tkinter-compatible image
        tk_image = ImageTk.PhotoImage(resized_image)

        # Update the image label
        self.image_label.config(image=tk_image)
        self.image_label.image = (
            tk_image  # Keep a reference to avoid garbage collection
        )

    def on_gamma_change(self, event=None):
        gamma_value = self.gamma.get()

        # Update the preview with the new gamma value
        self.update_preview(gamma_value)

    ##########################################################################
    ## Finalization and Utility Methods
    ##########################################################################

    def start_new_screenshot(self):
        # Hide the third page and show the first page
        self.preview_page.pack_forget()
        self.setup_page.pack(fill="both", expand=True)

        # Reset any other states if necessary
        # For example, you might want to clear the image label, reset variables, etc.
        self.image_label.config(image="")
        self.save_location_label.config(text="")

    def save_image(self):
        # Apply gamma correction to the average image
        gamma = self.gamma.get()
        gamma_corrected_image = self.apply_gamma_correction(self.average_image, gamma)

        # Convert the NumPy array to a PIL image
        pil_image = Image.fromarray(gamma_corrected_image)

        # Open file dialog to choose save location and file name
        file_options = {
            "defaultextension": ".png",
            "filetypes": [("PNG files", "*.png"), ("All files", "*.*")],
            "initialdir": "~",  # Default to home directory
            "title": "Save Image As",
        }
        filename = filedialog.asksaveasfilename(**file_options)

        if filename:  # Check if a filename was selected
            try:
                # Attempt to save the image
                pil_image.save(filename)
                # Update the label with a success message
                self.save_location_label.config(
                    text=f"Image successfully saved as: {filename}"
                )
            except Exception as e:
                # Update the label with an error message
                self.save_location_label.config(
                    text=f"Error saving file {filename}: {e}"
                )


if __name__ == "__main__":
    app = LongExposureApp()
    app.mainloop()
