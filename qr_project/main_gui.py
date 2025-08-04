# Written by Zichen Liao, 31808642
"""
Main GUI module for the Artistic QR Code Generator application.
This module provides a graphical user interface for generating customized QR codes
with various features like background images, logos, and color customization.
"""

# Standard library imports
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, Toplevel
import os
from typing import Optional
import json
import shutil
import tempfile

# Third-party library imports
from PIL import Image, ImageTk, ImageDraw, ImageEnhance, ImageSequence
from amzqr import amzqr  # Library for generating artistic QR codes
from matrix import QRMatrix  # Custom QR code matrix generator
from step_display import QRStepDisplay  # Custom module for displaying QR generation steps

class QRGeneratorGUI:
    """
    Main GUI class for the QR Code Generator application.
    This class handles all the UI elements and QR code generation functionality.
    """
    
    def __init__(self, root):
        """
        Initialize the QR Generator GUI.
        
        Args:
            root: The root Tkinter window
        """
        self.root = root
        self.root.title("Artistic QR Code Generator")
        self.root.geometry("1200x800")
        self.root.configure(bg="#f0f0f0")
        
        # Initialize instance variables
        self.background_path = None  # Path to the background image
        self.logo_path = None       # Path to the logo image
        self.qr_image = None        # Generated QR code image
        self.temp_dir = os.path.join(os.path.expanduser('~'), '.qrcode_temp')  # Temporary directory for storing files
        self.qr_color = "#000000"   # Default QR code color (black)
        self.frames = []            # List to store GIF animation frames
        self.current_frame = 0      # Index of current GIF frame
        self.is_playing = False     # Flag to track GIF animation playback status
        self.qr_code = None         # QR code matrix object
        self.qr_modules = None      # QR code module data
        
        # Set up the GUI components
        self.setup_styles()
        
        # Create main container frame
        self.main_frame = ttk.Frame(root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create GUI sections
        self.create_security_warning()
        self.create_input_area()
        self.create_options_area()
        self.create_display_area()
        
        # Create status bar at the bottom
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_styles(self):
        """
        Configure the visual styles for various TTK widgets used in the application.
        Sets up consistent fonts, colors, and appearances for labels, buttons, and other widgets.
        """
        style = ttk.Style()
        style.configure("TLabel", background="#f0f0f0", font=("Arial", 10))
        style.configure("TButton", font=("Arial", 10))
        style.configure("TEntry", font=("Arial", 10))
        style.configure("Warning.TLabel", foreground="red", font=("Arial", 9, "italic"))
        style.configure("Title.TLabel", font=("Arial", 12, "bold"))

    def create_security_warning(self):
        """
        Create and display a security warning message at the top of the application.
        Warns users about potential risks associated with scanning unknown QR codes.
        """
        warning_frame = ttk.Frame(self.main_frame)
        warning_frame.pack(fill=tk.X, pady=(0, 10))
        
        warning_text = "⚠️ Security Warning: Please note that scanning QR codes from unknown sources may involve risks, including but not limited to:\n" \
                      "• Phishing and fraud\n" \
                      "• Malicious websites and viruses\n" \
                      "• Personal information leakage\n" \
                      "Please verify the reliability of QR code sources before scanning."
        
        warning_label = ttk.Label(warning_frame, text=warning_text, style="Warning.TLabel",
                                wraplength=800, justify=tk.LEFT)
        warning_label.pack(fill=tk.X)

    def create_input_area(self):
        """
        Create the input area where users can enter the text content to be encoded in the QR code.
        Sets up a labeled entry field for text input.
        """
        self.input_frame = ttk.LabelFrame(self.main_frame, text="Input", padding="10")
        self.input_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Text input field with label
        ttk.Label(self.input_frame, text="Text Content:").pack(anchor=tk.W)
        self.text_input = ttk.Entry(self.input_frame, width=50)
        self.text_input.pack(fill=tk.X, pady=(5, 10))

    def create_options_area(self):
        """
        Create the options area containing all customization controls for the QR code.
        This includes error correction level, colors, background image, logo, and image effects.
        The options are organized in a two-column layout for better usability.
        """
        options_frame = ttk.LabelFrame(self.main_frame, text="Options", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Create two-column layout for better organization
        left_frame = ttk.Frame(options_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        right_frame = ttk.Frame(options_frame)
        right_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(20, 0))
        
        # Left column options
        # Error correction level selector
        ecl_frame = ttk.Frame(left_frame)
        ecl_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ecl_frame, text="Error Correction Level:").pack(side=tk.LEFT)
        self.error_level = ttk.Combobox(ecl_frame, 
                                      values=["L", "M", "Q", "H"],
                                      width=10,
                                      state="readonly")
        self.error_level.set("H")  # Set default to highest error correction
        self.error_level.pack(side=tk.LEFT, padx=5)
        
        # QR code color selector
        color_frame = ttk.Frame(left_frame)
        color_frame.pack(fill=tk.X, pady=5)
        ttk.Label(color_frame, text="QR Code Color:").pack(side=tk.LEFT)
        self.color_button = ttk.Button(color_frame, text="Choose Color", command=self.choose_color, width=15)
        self.color_button.pack(side=tk.LEFT, padx=5)
        self.color_preview = tk.Label(color_frame, bg=self.qr_color, width=3)
        self.color_preview.pack(side=tk.LEFT)
        
        # Right column options
        # Image settings section
        image_frame = ttk.Frame(right_frame)
        image_frame.pack(fill=tk.X, pady=5)
        
        # Background image selector
        bg_frame = ttk.Frame(image_frame)
        bg_frame.pack(fill=tk.X, pady=2)
        ttk.Button(bg_frame, text="Choose Background", 
                  command=self.choose_background).pack(side=tk.LEFT, padx=5)
        self.bg_label = ttk.Label(bg_frame, text="No background selected")
        self.bg_label.pack(side=tk.LEFT, padx=5)
        
        # Logo image selector
        logo_frame = ttk.Frame(image_frame)
        logo_frame.pack(fill=tk.X, pady=2)
        ttk.Button(logo_frame, text="Choose Logo", 
                  command=self.choose_logo).pack(side=tk.LEFT, padx=5)
        self.logo_label = ttk.Label(logo_frame, text="No logo selected")
        self.logo_label.pack(side=tk.LEFT, padx=5)
        
        # Image effect controls
        effect_frame = ttk.Frame(right_frame)
        effect_frame.pack(fill=tk.X, pady=5)
        
        # Contrast adjustment slider
        contrast_frame = ttk.Frame(effect_frame)
        contrast_frame.pack(fill=tk.X, pady=2)
        ttk.Label(contrast_frame, text="Contrast:").pack(side=tk.LEFT)
        self.contrast_scale = ttk.Scale(contrast_frame, from_=0.2, to=2.0, orient=tk.HORIZONTAL)
        self.contrast_scale.set(1.0)  # Default contrast value
        self.contrast_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Brightness adjustment slider
        brightness_frame = ttk.Frame(effect_frame)
        brightness_frame.pack(fill=tk.X, pady=2)
        ttk.Label(brightness_frame, text="Brightness:").pack(side=tk.LEFT)
        self.brightness_scale = ttk.Scale(brightness_frame, from_=0.2, to=2.0, orient=tk.HORIZONTAL)
        self.brightness_scale.set(1.0)  # Default brightness value
        self.brightness_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Action buttons
        button_frame = ttk.Frame(options_frame)
        button_frame.pack(pady=10)
        
        # Generate QR code button
        self.generate_btn = ttk.Button(button_frame, 
                                     text="Generate QR Code",
                                     command=self.generate_qr)
        self.generate_btn.pack(side=tk.LEFT, padx=5)
        
        # Reset settings button
        self.reset_btn = ttk.Button(button_frame,
                                  text="Reset Settings",
                                  command=self.reset_all)
        self.reset_btn.pack(side=tk.LEFT, padx=5)
        
        # Demo button for showing generation process
        self.demo_btn = ttk.Button(button_frame,
                                text="Show Generation Process",
                                command=self.show_qr_steps)
        self.demo_btn.pack(side=tk.LEFT, padx=5)

    def create_display_area(self):
        """
        Create the display area for showing the generated QR code preview.
        Includes the preview label and a save button for exporting the QR code.
        """
        self.display_frame = ttk.LabelFrame(self.main_frame, text="QR Code Preview", padding="10")
        self.display_frame.pack(fill=tk.BOTH, expand=True)
        
        # QR code preview label
        self.qr_label = ttk.Label(self.display_frame)
        self.qr_label.pack(expand=True)
        
        # Save QR code button
        self.save_btn = ttk.Button(self.display_frame, 
                                 text="Save QR Code",
                                 command=self.save_qr_code)
        self.save_btn.pack(pady=10)

    def choose_background(self):
        file_types = [
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("All files", "*.*")
        ]
        file_path = filedialog.askopenfilename(filetypes=file_types)
        if file_path:
            self.background_path = file_path
            self.bg_label.config(text=os.path.basename(file_path))

    def choose_logo(self):
        file_types = [
            ("Image files", "*.png *.jpg *.jpeg *.gif *.bmp"),
            ("All files", "*.*")
        ]
        file_path = filedialog.askopenfilename(filetypes=file_types)
        if file_path:
            self.logo_path = file_path
            self.logo_label.config(text=os.path.basename(file_path))

    def choose_color(self):
        """Choose the color for the QR code"""
        color = colorchooser.askcolor(color=self.qr_color, title="Choose QR Code Color")
        if color[1]:  # color is a tuple (RGB values, hexadecimal color value)
            self.qr_color = color[1]
            self.color_preview.configure(bg=self.qr_color)

    def show_qr_steps(self):
        """Display a demonstration window for the QR code generation process"""
        if not self.qr_image:
            messagebox.showwarning("Warning", "Please generate a QR code first!")
            return
            
        if not self.qr_code:
            messagebox.showwarning("Warning", "The current mode does not support process demonstration!")
            return
            
        QRStepDisplay(self.root, self.qr_code, self.qr_modules, self.raw_modules)  # Pass raw_modules if available


    def generate_qr(self):
        text = self.text_input.get().strip()
        if not text:
            messagebox.showwarning("Warning", "Please enter text content!")
            return

        try:
            # Clean temporary directory
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            os.makedirs(self.temp_dir)
            
            # Get error correction level
            ecl = self.error_level.get()  # Use L, M, Q, H directly
            
            # Prepare save name
            save_name = "qrcode"
            if self.background_path and self.background_path.lower().endswith('.gif'):
                save_name += ".gif"
            else:
                save_name += ".png"
                
            # Convert error correction level
            ecl_map = {
                "L": QRMatrix.Ecc.LOW,
                "M": QRMatrix.Ecc.MEDIUM,
                "Q": QRMatrix.Ecc.QUARTILE,
                "H": QRMatrix.Ecc.HIGH
            }
            
            # Convert color from HEX to RGB
            color = tuple(int(self.qr_color[i:i+2], 16) for i in (1, 3, 5))
            
            if self.background_path and self.background_path.lower().endswith('.gif'):
                # Handle GIF animation
                version, level, qr_name = amzqr.run(
                    words=text,
                    level=ecl,
                    picture=self.background_path,
                    colorized=True,
                    save_name=save_name,
                    save_dir=self.temp_dir
                )
                qr_path = os.path.join(self.temp_dir, qr_name)
                self.qr_image = qr_path
                self.qr_code = None
                self.qr_modules = None
                self.raw_modules = None
            else:
                # Generate QR code
                qr = QRMatrix.encode_text(text, ecl_map[ecl], color)
                self.qr_code = qr
                
                # Save raw modules (before mask) and final modules
                self.raw_modules = [row[:] for row in qr._modules_before_mask]
                self.qr_modules = [row[:] for row in qr._modules]
                
                # Create image
                scale = 10  # Scale factor
                size = qr.get_size() * scale
                image = Image.new("RGBA", (size, size), (255, 255, 255, 0))  # Use RGBA mode
                
                # Draw QR code
                qr_color = qr.get_color() + (255,)  # Add alpha channel
                for y in range(qr.get_size()):
                    for x in range(qr.get_size()):
                        if qr.get_module(x, y):
                            for i in range(scale):
                                for j in range(scale):
                                    image.putpixel((x * scale + i, y * scale + j), qr_color)

                # If there's a background image
                if self.background_path:
                    bg = Image.open(self.background_path).convert('RGBA')
                    bg = self.adjust_image(bg)  # Apply brightness and contrast adjustments
                    bg = bg.resize((size, size), Image.Resampling.LANCZOS)
                    
                    # Create result image
                    result = Image.new('RGBA', (size, size), (255, 255, 255, 0))
                    result.paste(bg, (0, 0))
                    result.paste(image, (0, 0), image)
                    image = result

                # If there's a Logo
                if self.logo_path:
                    logo = Image.open(self.logo_path).convert('RGBA')
                    logo_size = int(size * 0.25)
                    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                    
                    # Create rounded corner mask
                    mask = Image.new('L', (logo_size, logo_size), 0)
                    draw = ImageDraw.Draw(mask)
                    draw.rounded_rectangle([0, 0, logo_size, logo_size], radius=int(logo_size*0.1), fill=255)
                    
                    # Calculate paste position
                    pos = ((size - logo_size) // 2, (size - logo_size) // 2)
                    image.paste(logo, pos, mask)

                # Save image
                qr_path = os.path.join(self.temp_dir, save_name)
                image.save(qr_path)
                self.qr_image = image  # Store as PIL.Image for saving
            
            # Show preview
            if isinstance(self.qr_image, str):
                self.display_qr_preview(self.qr_image)
            else:
                self.display_qr_preview(qr_path)
            
            self.status_var.set("QR code generated successfully!")

        except Exception as e:
            messagebox.showerror("Error", f"Error generating QR code: {str(e)}")
            self.status_var.set("Generation failed")

    def save_qr_code(self):
        """
        Save the generated QR code to a user-specified location.
        Supports saving both static images (PNG) and animated GIFs.
        Handles different save operations based on the QR code type and preserves animation if present.
        
        Shows appropriate warning messages if no QR code has been generated.
        Updates the status bar with the save operation result.
        """
        if not self.qr_image:
            messagebox.showwarning("Warning", "Please generate a QR code first!")
            return
            
        file_types = [("PNG Image", "*.png")]
        if self.background_path and self.background_path.lower().endswith('.gif'):
            file_types = [("GIF Animation", "*.gif")] + file_types
            
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=file_types,
            initialfile="qrcode"
        )
        if file_path:
            try:
                if isinstance(self.qr_image, str):
                    # For GIF animations from amzqr
                    shutil.copy2(self.qr_image, file_path)
                else:
                    # For static images
                    preview_size = 400
                    if file_path.lower().endswith('.gif'):
                        # Save animated GIF with all frames
                        frames = []
                        for frame in ImageSequence.Iterator(self.qr_image):
                            frame = frame.copy()
                            frame.thumbnail((preview_size, preview_size), Image.Resampling.LANCZOS)
                            frames.append(frame)
                        frames[0].save(file_path, save_all=True, append_images=frames[1:], loop=0)
                    else:
                        # Save static PNG
                        image = self.qr_image.copy()
                        image.thumbnail((preview_size, preview_size), Image.Resampling.LANCZOS)
                        image.save(file_path, "PNG")
                self.status_var.set(f"QR code saved to: {file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving file: {str(e)}")
                self.status_var.set("Save failed")

    def display_qr_preview(self, qr_path):
        """
        Display a preview of the generated QR code in the UI.
        
        Args:
            qr_path (str): Path to the generated QR code image file
            
        Handles both static images and animated GIFs:
        - For static images: Displays a single preview
        - For GIFs: Sets up animation playback with frame transitions
        """
        if qr_path.lower().endswith('.gif'):
            # Handle GIF animation preview
            self.frames = []
            image = Image.open(qr_path)
            
            # Process all frames
            for frame in ImageSequence.Iterator(image):
                frame = frame.copy()
                frame.thumbnail((400, 400), Image.Resampling.LANCZOS)
                self.frames.append(ImageTk.PhotoImage(frame))
            
            # Initialize animation
            self.current_frame = 0
            self.qr_label.configure(image=self.frames[0])
            
            # Start animation if not already playing
            if not self.is_playing:
                self.is_playing = True
                self.animate_gif()
        else:
            # Handle static image preview
            image = Image.open(qr_path)
            image.thumbnail((400, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self.qr_label.configure(image=photo)
            self.qr_label.image = photo
            self.is_playing = False

    def animate_gif(self):
        """
        Handle GIF animation playback in the preview area.
        Cycles through frames continuously while animation is playing.
        Each frame is displayed for 100ms before switching to the next one.
        """
        if self.is_playing and self.frames:
            self.current_frame = (self.current_frame + 1) % len(self.frames)
            self.qr_label.configure(image=self.frames[self.current_frame])
            self.root.after(100, self.animate_gif)

    def adjust_image(self, image: Image.Image) -> Image.Image:
        """
        Apply brightness and contrast adjustments to an image.
        
        Args:
            image (PIL.Image.Image): The input image to adjust
            
        Returns:
            PIL.Image.Image: The adjusted image
            
        The adjustment values are taken from the UI sliders for brightness and contrast.
        If adjustment fails, returns the original image and shows a warning.
        """
        try:
            contrast = float(self.contrast_scale.get())
            brightness = float(self.brightness_scale.get())
            
            # Apply contrast and brightness enhancements
            image = ImageEnhance.Contrast(image).enhance(contrast)
            image = ImageEnhance.Brightness(image).enhance(brightness)
            
            return image
            
        except Exception as e:
            messagebox.showwarning("Warning", f"Image adjustment failed: {str(e)}")
            return image

    def reset_all(self):
        """
        Reset all settings to their default values.
        This includes:
        - Error correction level
        - QR code color
        - Background and logo selections
        - Contrast and brightness values
        - Clearing the generated QR code
        - Stopping any ongoing animations
        
        Updates the UI to reflect the reset state.
        """
        # Reset error correction level
        self.error_level.set("H")
        
        # Reset QR code color
        self.qr_color = "#000000"
        self.color_preview.configure(bg=self.qr_color)
        
        # Clear image selections
        self.background_path = None
        self.logo_path = None
        self.bg_label.config(text="No background selected")
        self.logo_label.config(text="No logo selected")
        
        # Reset image adjustment values
        self.contrast_scale.set(1.0)
        self.brightness_scale.set(1.0)
        
        # Clear generated QR code
        self.qr_image = None
        self.qr_label.configure(image="")
        
        # Update status
        self.status_var.set("All settings have been reset")
        
        # Stop animation if playing
        self.is_playing = False
        self.frames = []
        self.current_frame = 0

