import tkinter as tk
from tkinter import ttk

def populate_frame(frame):
    # Add a bunch of labels to the frame for demonstration
    for i in range(20):
        label = tk.Label(frame, text=f"Label {i}")
        label.grid(row=i, column=0, pady=5, padx=10, sticky="w")
        frame.grid_rowconfigure(i, weight=1)

def add_label():
    # Create a new label and add it to the grid
    new_label = tk.Label(scrollable_frame, text="New Label Created!")
    new_label.grid(row=scrollable_frame.grid_size()[1], column=0, pady=5, padx=10, sticky="w")

    # Update the scroll region of the canvas
    canvas.update_idletasks()
    canvas.config(scrollregion=canvas.bbox("all"))

# Create the main window
root = tk.Tk()
root.title("Scrollable Tab with Dynamic Label Example (Grid Layout)")

# Create a Notebook widget
notebook = ttk.Notebook(root)
notebook.pack(fill=tk.BOTH, expand=True)

# Create a Frame to hold the scrollable content
tab_frame = ttk.Frame(notebook)
notebook.add(tab_frame, text="Scrollable Tab")

# Create a Canvas widget inside the tab frame
canvas = tk.Canvas(tab_frame)
canvas.grid(row=0, column=0, sticky="nsew")

# Add a scrollbar to the canvas
scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
scrollbar.grid(row=0, column=1, sticky="ns")
canvas.configure(yscrollcommand=scrollbar.set)

# Create another Frame inside the Canvas
scrollable_frame = ttk.Frame(canvas)
canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")

# Populate the scrollable frame with initial widgets
populate_frame(scrollable_frame)

# Function to add a new label when the button is pressed
add_button = ttk.Button(root, text="Add Label", command=add_label)
add_button.pack(pady=10)

# Configure the scroll region after the frame is populated
scrollable_frame.update_idletasks()
canvas.config(scrollregion=canvas.bbox("all"))

# Configure grid resizing
tab_frame.grid_rowconfigure(0, weight=1)
tab_frame.grid_columnconfigure(0, weight=1)

# Start the main event loop
root.mainloop()
