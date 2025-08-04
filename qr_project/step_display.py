"""
File Name: step_display.py
Description: A Python application for generating QR codes and display the generation step by step.
Author: Liu Yuhao 31808610
Date: May 27, 2025

File Name: step_display.py
Description: Functions to check if coordinates belong to QR code's finder, alignment or timing patterns.
Author: Ni Ruiyang 31808600
Date: May 28, 2025
"""


import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser, Toplevel
import os
from PIL import Image, ImageTk, ImageDraw, ImageEnhance, ImageSequence
import tempfile
from typing import Optional
import json
import shutil
from amzqr import amzqr  # Import amzqr
from matrix import QRMatrix  # Import qr_generator
from utils import _get_bit  # Import _get_bit function

class QRStepDisplay:
    def __init__(self, parent, qr_code, modules, raw_modules=None):
        self.window = Toplevel(parent)
        self.window.title("QR Code Generation Process")
        self.window.geometry("600x700")
        
        # Save QR code related information
        self.qr_code = qr_code
        self.modules = [row[:] for row in modules]  # Working copy of final modules
        self.raw_modules = [row[:] for row in (raw_modules or modules)]  # Raw modules before mask
        self.current_step = 0
        
        # Create interface
        self.create_widgets()
        
        # Bind window close event
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Start demonstration
        self.start_demonstration()
    
    def create_widgets(self):
        # Create main canvas with scrollbar
        self.canvas = tk.Canvas(self.window)
        self.scrollbar = ttk.Scrollbar(self.window, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        # Configure canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Pack scrollbar and canvas
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)
        
        # Add mouse wheel scrolling - bind to specific widgets
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.scrollable_frame.bind("<MouseWheel>", self._on_mousewheel)
        
        # Top description text
        self.description = ttk.Label(self.scrollable_frame, wraplength=550, justify="left")
        self.description.pack(pady=10, padx=10)
        
        # Image display area
        self.image_label = ttk.Label(self.scrollable_frame)
        self.image_label.pack(expand=True, pady=10)
        
        # Control buttons
        self.button_frame = ttk.Frame(self.scrollable_frame)
        self.button_frame.pack(pady=10)
        
        self.prev_btn = ttk.Button(self.button_frame, text="Previous", command=self.prev_step)
        self.prev_btn.pack(side=tk.LEFT, padx=5)
        
        self.next_btn = ttk.Button(self.button_frame, text="Next", command=self.next_step)
        self.next_btn.pack(side=tk.LEFT, padx=5)
        
        # Progress display
        self.progress_var = tk.StringVar()
        self.progress_label = ttk.Label(self.scrollable_frame, textvariable=self.progress_var)
        self.progress_label.pack(pady=5)
        
        # Penalty score display
        self.penalty_var = tk.StringVar()
        self.penalty_label = ttk.Label(self.scrollable_frame, textvariable=self.penalty_var)
        self.penalty_label.pack(pady=5)
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel scrolling"""
        try:
            self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        except:
            pass  # Ignore errors if canvas is destroyed
    
    def on_closing(self):
        """Handle window closing event"""
        # Unbind all events
        self.canvas.unbind("<MouseWheel>")
        self.scrollable_frame.unbind("<MouseWheel>")
        self.window.destroy()
    
    def start_demonstration(self):
        self.steps = [
            ("Finder Patterns", self.draw_finder_patterns),
            ("Alignment Patterns", self.draw_alignment_patterns),
            ("Timing Patterns", self.draw_timing_patterns),
            ("Data Area", self.draw_data_bits),
            ("Mask Evaluation", self.draw_mask_evaluation),
            ("Mask Application", self.draw_mask),
            ("Final Result", self.draw_final)
        ]
        self.update_display()
        
    def update_display(self):
        step_name, draw_func = self.steps[self.current_step]
        self.progress_var.set(f"Step {self.current_step + 1}/{len(self.steps)}")
        
        # Update description text
        descriptions = {
            "Finder Patterns": "The finder patterns in three corners are used to detect the position and orientation of the QR code. These patterns have fixed proportions for quick scanner detection.",
            "Alignment Patterns": "Alignment patterns help scanners correct distortion in the QR code. Higher versions have more alignment patterns.",
            "Timing Patterns": "Timing patterns are alternating black and white lines connecting finder patterns, used to determine module size in the QR code.",
            "Data Area": "The data area contains the actual encoded information, including data and error correction codes. Different colors represent different types of data.",
            "Mask Evaluation": "The QR code generator evaluates 8 different mask patterns (0-7) and selects the one with the lowest penalty score. The penalty score is calculated based on undesirable patterns that might make the QR code harder to scan.",
            "Mask Application": "The selected optimal mask pattern is applied to break up regular patterns in the data area, making the QR code easier for scanners to read.",
            "Final Result": "This is the final generated QR code, containing all necessary function patterns and data with the optimal mask pattern applied."
        }
        self.description.config(text=descriptions[step_name])
        
        # Generate current step image
        image = draw_func()
        
        # Adjust image size
        image = image.resize((400, 400), Image.Resampling.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        self.image_label.configure(image=photo)
        self.image_label.image = photo
        
        # Update button states
        self.prev_btn.config(state="disabled" if self.current_step == 0 else "normal")
        self.next_btn.config(state="disabled" if self.current_step == len(self.steps) - 1 else "normal")
        
        # Clear penalty score when not in mask evaluation step
        if step_name != "Mask Evaluation":
            self.penalty_var.set("")
    
    def next_step(self):
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
            self.update_display()
    
    def prev_step(self):
        if self.current_step > 0:
            self.current_step -= 1
            self.update_display()
    
    def is_function_module(self, x, y):
        """Determine if the given coordinates (x, y) are part of a functional module."""
        return (self.is_finder_pattern(x, y) or 
                self.is_alignment_pattern(x, y) or 
                self.is_timing_pattern(x, y) or 
                self.is_format_info(x, y))
    
    def is_format_info(self, x, y):
        """Determine if the given coordinates (x, y) are part of the format information area.
        The format information is located in two specific areas:
        1. Surrounding the finder pattern in the top left corner.
        2. Next to the finder patterns in the top right and bottom left corners.
        """
        if y == 8:
            return x <= 8 or x >= self.qr_code._size - 8
        if x == 8:
            return y <= 8 or y >= self.qr_code._size - 8
        return False
    
    def draw_finder_patterns(self):
        """Draw the finder patterns on the QR code.
        The finder patterns are the three large squares located at the corners of the QR code.
        They help scanners detect the position and orientation of the QR code.
        """
        size = self.qr_code._size
        image = Image.new("RGB", (size * 10, size * 10), "white")
        draw = ImageDraw.Draw(image)
        
        # Only draw the finder patterns
        for y in range(size):
            for x in range(size):
                if self.is_finder_pattern(x, y) and self.raw_modules[y][x]:
                    draw.rectangle([x*10, y*10, (x+1)*10-1, (y+1)*10-1], fill="black")
        return image
    
    def draw_alignment_patterns(self):
        """Draw the alignment patterns on the QR code.
        Alignment patterns are smaller squares that help scanners correct distortion in the QR code.
        Higher versions of QR codes have more alignment patterns to improve scanning accuracy.
        """
        size = self.qr_code._size
        image = Image.new("RGB", (size * 10, size * 10), "white")
        draw = ImageDraw.Draw(image)
        
        # Draw previous content
        for y in range(size):
            for x in range(size):
                if self.raw_modules[y][x]:
                    if self.is_finder_pattern(x, y):
                        draw.rectangle([x*10, y*10, (x+1)*10-1, (y+1)*10-1], fill="black")
                    elif self.is_alignment_pattern(x, y):
                        draw.rectangle([x*10, y*10, (x+1)*10-1, (y+1)*10-1], fill="blue")
        return image
    
    def draw_timing_patterns(self):
        """Draw the timing patterns on the QR code.
        Timing patterns are alternating black and white lines that help determine the size of the modules in the QR code.
        They are located between the finder patterns and are essential for accurate scanning.
        """
        size = self.qr_code._size
        image = Image.new("RGB", (size * 10, size * 10), "white")
        draw = ImageDraw.Draw(image)
        
        # Draw previous content and timing patterns
        for y in range(size):
            for x in range(size):
                if self.raw_modules[y][x]:
                    if self.is_finder_pattern(x, y):
                        draw.rectangle([x*10, y*10, (x+1)*10-1, (y+1)*10-1], fill="black")
                    elif self.is_alignment_pattern(x, y):
                        draw.rectangle([x*10, y*10, (x+1)*10-1, (y+1)*10-1], fill="blue")
                    elif self.is_timing_pattern(x, y):
                        draw.rectangle([x*10, y*10, (x+1)*10-1, (y+1)*10-1], fill="red")
        return image
    
    def draw_data_bits(self):
        """Draw the data bits on the QR code.
        The data area contains the actual encoded information, including data and error correction codes.
        Different colors are used to represent different types of data, making it easier for scanners to read.
        """
        size = self.qr_code._size
        image = Image.new("RGB", (size * 10, size * 10), "white")
        draw = ImageDraw.Draw(image)
        
        # Draw all content using raw_modules
        for y in range(size):
            for x in range(size):
                if self.raw_modules[y][x]:
                    if self.is_function_module(x, y):
                        if self.is_finder_pattern(x, y):
                            color = "black"
                        elif self.is_alignment_pattern(x, y):
                            color = "blue"
                        elif self.is_timing_pattern(x, y):
                            color = "red"
                        else:
                            color = "purple"  # Format information, etc.
                    else:
                        color = "green"  # Data bits
                    draw.rectangle([x*10, y*10, (x+1)*10-1, (y+1)*10-1], fill=color)
        return image
    
    def draw_mask_evaluation(self):
        """Draw the mask evaluation process.
        This step shows the evaluation of different mask patterns and their penalty scores.
        The mask pattern with the lowest penalty score will be selected.
        """
        size = self.qr_code._size
        image = Image.new("RGB", (size * 10, size * 10), "white")
        draw = ImageDraw.Draw(image)
        
        # Use a temporary copy to avoid modifying self.modules
        temp_modules = [row[:] for row in self.raw_modules]
        
        # Calculate penalty scores for each mask
        penalties = []
        for i in range(8):
            # Apply mask to temporary copy
            for y in range(size):
                for x in range(size):
                    if not self.is_function_module(x, y):
                        mask_value = QRMatrix._MASK_PATTERNS[i](x, y) == 0
                        temp_modules[y][x] ^= mask_value
            
            # Draw format bits
            format_data = self.qr_code._errcorlvl.formatbits << 3 | i
            rem = format_data
            for _ in range(10):
                rem = (rem << 1) ^ ((rem >> 9) * 0x537)
            bits = (format_data << 10 | rem) ^ 0x5412
            
            # Draw first copy of format bits
            for j in range(0, 6):
                temp_modules[8][j] = _get_bit(bits, j)
            temp_modules[8][7] = _get_bit(bits, 6)
            temp_modules[8][8] = _get_bit(bits, 7)
            temp_modules[7][8] = _get_bit(bits, 8)
            for j in range(9, 15):
                temp_modules[14 - j][8] = _get_bit(bits, j)
            
            # Draw second copy of format bits
            for j in range(0, 8):
                temp_modules[size - 1 - j][8] = _get_bit(bits, j)
            for j in range(8, 15):
                temp_modules[8][size - 15 + j] = _get_bit(bits, j)
            temp_modules[8][size - 8] = True
            
            # Calculate penalty
            penalty = self._calculate_penalty_score(temp_modules)
            penalties.append(penalty)
        
        # Find the best mask (lowest penalty)
        best_mask = penalties.index(min(penalties))
        min_penalty = min(penalties)
        
        # Display the evaluation result
        result = "Mask Pattern Penalties:\n"
        for i in range(8):
            result += f"\nMask {i}: {penalties[i]}"
            if i == best_mask:
                result += " (Selected)"
        
        self.penalty_var.set(result)
        
        # Draw the current state using raw_modules
        for y in range(size):
            for x in range(size):
                if self.raw_modules[y][x]:
                    if self.is_function_module(x, y):
                        if self.is_finder_pattern(x, y):
                            color = "black"
                        elif self.is_alignment_pattern(x, y):
                            color = "blue"
                        elif self.is_timing_pattern(x, y):
                            color = "red"
                        else:
                            color = "purple"
                    else:
                        color = "green"
                    draw.rectangle([x*10, y*10, (x+1)*10-1, (y+1)*10-1], fill=color)
                
                # Highlight both selected and best mask patterns
                if not self.is_function_module(x, y):
                    if QRMatrix._MASK_PATTERNS[self.qr_code._mask](x, y) == 0:
                        # Selected mask in yellow/orange
                        draw.rectangle([x*10, y*10, (x+1)*10-1, (y+1)*10-1], 
                                    fill="yellow" if not self.raw_modules[y][x] else "orange",
                                    outline="gray")
                    if best_mask != self.qr_code._mask and QRMatrix._MASK_PATTERNS[best_mask](x, y) == 0:
                        # Best calculated mask in red crosshatch
                        draw.line([x*10, y*10, (x+1)*10-1, (y+1)*10-1], fill="red", width=1)
                        draw.line([x*10, (y+1)*10-1, (x+1)*10-1, y*10], fill="red", width=1)
        
        return image

    def _calculate_penalty_score(self, modules):
        """Calculate the penalty score for a given QR code pattern using the same rules as in matrix.py."""
        size = self.qr_code._size
        score = 0
        
        # Rule 1: Adjacent modules in row/column having same color
        for y in range(size):
            runcolor = False
            runx = 0
            for x in range(size):
                if modules[y][x] == runcolor:
                    runx += 1
                    if runx == 5:
                        score += QRMatrix._PENALTY_N1
                    elif runx > 5:
                        score += 1
                else:
                    runcolor = modules[y][x]
                    runx = 1
        
        for x in range(size):
            runcolor = False
            runy = 0
            for y in range(size):
                if modules[y][x] == runcolor:
                    runy += 1
                    if runy == 5:
                        score += QRMatrix._PENALTY_N1
                    elif runy > 5:
                        score += 1
                else:
                    runcolor = modules[y][x]
                    runy = 1
        
        # Rule 2: 2x2 blocks of same color
        for y in range(size - 1):
            for x in range(size - 1):
                if modules[y][x] == modules[y][x + 1] == modules[y + 1][x] == modules[y + 1][x + 1]:
                    score += QRMatrix._PENALTY_N2
        
        # Rule 3: Finder-like patterns
        pattern = [True, False, True, True, True, False, True]
        for y in range(size):
            for x in range(size - 6):
                if all(modules[y][x + j] == pattern[j] for j in range(7)):
                    score += QRMatrix._PENALTY_N3
        
        for x in range(size):
            for y in range(size - 6):
                if all(modules[y + j][x] == pattern[j] for j in range(7)):
                    score += QRMatrix._PENALTY_N3
        
        # Rule 4: Balance of dark and light modules
        dark = sum(sum(row) for row in modules)
        total = size * size
        k = (abs(dark * 20 - total * 10) + total - 1) // total - 1
        score += k * QRMatrix._PENALTY_N4
        
        return score
    
    def draw_mask(self):
        """Draw the mask pattern on the QR code.
        Masks are used to break up regular patterns in the data area, making the QR code easier for scanners to read.
        The mask pattern is applied to the non-functional modules of the QR code.
        """
        size = self.qr_code._size
        image = Image.new("RGB", (size * 10, size * 10), "white")
        draw = ImageDraw.Draw(image)
        
        # Apply the selected mask to modules
        for y in range(size):
            for x in range(size):
                if not self.is_function_module(x, y):
                    mask_value = QRMatrix._MASK_PATTERNS[self.qr_code._mask](x, y) == 0
                    self.modules[y][x] = self.raw_modules[y][x] ^ mask_value
        
        # Draw the masked result
        for y in range(size):
            for x in range(size):
                if self.modules[y][x]:
                    if self.is_function_module(x, y):
                        if self.is_finder_pattern(x, y):
                            color = "black"
                        elif self.is_alignment_pattern(x, y):
                            color = "blue"
                        elif self.is_timing_pattern(x, y):
                            color = "red"
                        else:
                            color = "purple"
                    else:
                        color = "black"  # Data bits after mask
                    draw.rectangle([x*10, y*10, (x+1)*10-1, (y+1)*10-1], fill=color)
                # Highlight mask pattern
                if not self.is_function_module(x, y) and QRMatrix._MASK_PATTERNS[self.qr_code._mask](x, y) == 0:
                    draw.rectangle([x*10, y*10, (x+1)*10-1, (y+1)*10-1], outline="yellow", width=1)
        
        return image
    
    def draw_final(self):
        """Draw the final QR code.
        This function generates the final QR code image, filling all functional modules with black.
        The result is a complete QR code ready for scanning.
        """
        size = self.qr_code._size
        image = Image.new("RGB", (size * 10, size * 10), "white")
        draw = ImageDraw.Draw(image)
        
        # Use the masked modules for final result
        for y in range(size):
            for x in range(size):
                if self.modules[y][x]:
                    draw.rectangle([x*10, y*10, (x+1)*10-1, (y+1)*10-1], fill="black")
        
        return image


    def is_finder_pattern(self, x, y):
        """Check if the given coordinates (x, y) are part of a finder pattern.
        Finder patterns are located in three corners of the QR code and are essential for detection.
        """
        corners = [(0, 0), (0, self.qr_code._size - 7), (self.qr_code._size - 7, 0)]
        for corner_x, corner_y in corners:
            if corner_x <= x < corner_x + 7 and corner_y <= y < corner_y + 7:
                return True
        return False
    
    def is_alignment_pattern(self, x, y):
        """Check if the given coordinates (x, y) are part of an alignment pattern.
        Alignment patterns are used to correct distortion in the QR code and are present in higher versions.
        """
        if self.qr_code._version < 2:  # Version 1 does not have alignment patterns
            return False
        alignpatpos = self.qr_code._get_alignment_pattern_positions()
        for i in alignpatpos:
            for j in alignpatpos:
                if (i-2 <= x <= i+2) and (j-2 <= y <= j+2):
                    # Exclude positions overlapping with finder patterns
                    if not self.is_finder_pattern(x, y):
                        return True
        return False
    
    def is_timing_pattern(self, x, y):
        """Check if the given coordinates (x, y) are part of a timing pattern.
        Timing patterns are located at specific positions and help determine the module size.
        """
        return (x == 6 and 8 <= y <= self.qr_code._size-8) or (y == 6 and 8 <= x <= self.qr_code._size-8)

