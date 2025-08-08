# QR_code_generator
A **graphical QR code generator** that enables users to easily create standard or artistic QR codes, with customization options and educational step-by-step visualizations of the encoding process

---

## Application Description and operation instructions

### Description

This project is a graphical QR code generator that supports users to input any string to generate standard or artistic QR codes. This application includes the step-by-step generation of visualizations and enhances the transparency of how data is encoded as QR codes. It offers a user-friendly interface that allows non-technical users to easily generate, customize, preview and save QR codes.

---

### Getting Started 

**Requirements**
- Python version **3.11.7**
- Install the necessary libraries in the terminal:
```bash
pip install pillow reedsolo amzqr
```
**Note:** The amzqr library is used exclusively as an additional feature to handle the GIF background for dynamic QR codes; it is not involved in the core QR code construction process.
- Run the application:
In the root directory of the project, run:
```bash
python main.py
```
---

### User Operations

1. **Launch the App**
   Run the main program:

   ```bash
   python main.py
   ```

2. **Input Text**
   Type the text or URL you want to encode into a QR code.

3. **Optional Settings**

   * Choose **error correction level** (L / M / Q / H)
   * Set **QR code foreground/background colors**
   * Upload a background image
   * Embed a **logo image** in the center
   * Adjust **contrast and brightness**
   * Restore to **default settings**

4. **Generate QR Code**

   * Click **"Generate QR Code"** to preview
   * Click **"Show Generation Process"** to visualize how the QR is built step-by-step

5. **Save QR Code**

   * Click **"Save QR Code"** to export the image as `.png` or `.gif`

---

### Project Structure
```plaintext
qr_project/
│
├── main.py             # Entry point for launching the GUI
├── main_gui.py         # Main GUI logic and interface
├── bitstream.py        # Handles bitstream processing for QR code generation
├── datablock.py        # Encodes user data into structured blocks
├── matrix.py           # Builds the QR matrix based on encoded data
├── step_display.py     # Visualizes the QR generation steps
└── utils.py            # Utility functions and error definitions
```
---

## Programming paradigms used 

This project utilizes a combination of imperative, functional, and object-oriented programming paradigms to achieve its goals. Below is a summary of how each paradigm has been applied throughout the codebase.

### **Object-Oriented Programming (OOP)**

Object-oriented programming is the primary paradigm used in this project. The code is structured around classes and objects that encapsulate related data and behaviors. This approach provides a clear modular structure and promotes code reuse.

- **Classes and Objects**: The project defines several classes such as `QRDataBlock`, `QRMatrix`, `QRGeneratorGUI`, and `QRStepDisplay`. Each class represents a distinct entity with its own attributes and methods.
- **Encapsulation**: Data is encapsulated within classes, and access to this data is controlled through public methods. For example, `QRMatrix` class encapsulates the data and functionality related to generating QR codes.
- **Inheritance**: While not explicitly used in the provided code, inheritance could be utilized to extend the functionality of existing classes.
- **Polymorphism**: Methods such as `get_module` in the `QRMatrix` class demonstrate polymorphism by providing a unified interface to access different types of data within the QR code. Broadly speaking, this reflects a kind of polymorphism.

### **Imperative Programming**

Imperative programming is used to describe the algorithms and the step-by-step procedures for performing tasks.

- **Procedural Code**: Functions like `make_segments` in `QRDataBlock` and `draw_function_patterns` in `QRMatrix` contain imperative logic that describes the sequence of operations needed to execute a task.
- **Control Structures**: The code extensively uses control structures such as loops (`for`, `while`) and conditionals (`if`, `else`) to execute code based on certain conditions or to repeat actions.
- **Procedural Instructions**: The `generate_qr` method in `QRGeneratorGUI` is a good example of imperative programming, where it provides a sequence of steps to generate a QR code.

### **Functional Programming**

Functional programming concepts are used to enhance the code's readability and maintainability, especially in handling data transformations and collections.

- **First-Class Functions**: Functions like `choose_color` and `choose_background` in `QRGeneratorGUI` are passed as parameters to other functions, demonstrating that functions are treated as first-class citizens.
- **Pure Functions**: The `_get_bit` function in `utils.py` is a pure function that takes inputs and returns outputs without causing side effects.
- **Data Immutability**: The `BitStream` class in `bitstream.py` uses a list to store bits, which can be considered immutable since it is extended rather than modified in place.
- **Higher-Order Functions**: The use of `map`, `filter`, and `reduce` is not explicitly shown in the provided code, but these could be used to process data in a functional style.

In summary, the project effectively combines these programming paradigms to create a robust and flexible application. Object-oriented programming provides the structure, imperative programming provides the control flow, and functional programming principles help in managing data and operations more effectively.

---

## Social, Legal and Ethical Considerations

### Social Concepts

- **Accessibility**  
The application provides a graphical user interface (GUI) that is designed to be user-friendly and accessible to a wide range of users. Features such as clear labels, intuitive controls, and visual feedback aim to make the application usable for individuals with varying levels of technical expertise. Additionally, the application includes a security warning to inform users about potential risks associated with scanning QR codes, promoting awareness and caution.

- **Inclusivity**  
The application supports multiple languages and encodings (e.g., UTF-8), allowing users from different linguistic backgrounds to generate QR codes for their content. It also provides options for customizing the appearance of the QR code, such as color selection and background images, which can cater to diverse user preferences and cultural contexts.

- **Education**  
The application includes a demonstration mode that shows the step-by-step process of QR code generation. This feature can serve as an educational tool, helping users understand the underlying principles and components of QR codes. By visualizing the encoding process, users can gain insights into how data is represented and protected within a QR code.

### Legal Concepts

- **Data Protection**  
The application ensures that user data is handled securely. When generating QR codes, the application does not store user input or sensitive information beyond the temporary files required for processing. The temporary files are stored in a designated directory and are cleaned up after the QR code generation process is complete. Additionally, the application does not transmit user data to external servers, maintaining the privacy and confidentiality of user information.

- **Compliance with Regulations**  
The application adheres to relevant legal standards and regulations, such as data protection laws and intellectual property rights. It does not include any features that would encourage or facilitate the misuse of copyrighted material or personal data. The application also provides clear instructions and warnings to users, ensuring that they are aware of their responsibilities when generating and using QR codes.

### Ethical Concepts

- **Transparency**  
The application is designed to be transparent in its operations. It provides users with clear information about the QR code generation process, including the encoding modes, error correction levels, and customization options available. The application also includes a status bar that provides real-time feedback on the generation process, allowing users to understand what is happening at each step.

- **Risk Mitigation**  
The application includes a security warning to inform users about the potential risks associated with scanning QR codes from unknown sources. This warning highlights issues such as phishing, malicious websites, and personal information leakage, encouraging users to exercise caution and verify the reliability of QR code sources. Additionally, the application includes error handling and validation mechanisms to prevent the generation of invalid or potentially harmful QR codes.

---

## Data Modeling, Management and Security
### Information Modeling

#### 1. Data Modeling

##### (1) User Input:
- Users input data through the interface in the form of text (strings), binary data (such as image files), or custom QR code parameters (such as error correction level, color, background, logo, etc.).

##### (2) QR Code Generation:
###### Encoding:
- The input data is converted into the binary format required for QR code generation using functions like `makenumeric()`, `makealphanumeric()`, and `makebytes()`.
  - When the input is numeric or alphanumeric, it is converted using `makealphanumeric()` with the corresponding encoding method.
  - For more complex input data (like binary data), `makebytes()` is used to convert it into a byte stream.

###### Error Correction Code:
- Error correction is achieved by splitting the data into multiple blocks and adding correction codes. Functions like `addeccandinterleave()` are used to insert error correction data into the QR code.

###### QR Code Matrix:
- Functions such as `drawfinderpatterns()`, `drawalignmentpatterns()`, and `drawtimingpatterns()` are used to draw modules in the 2D matrix and standardize the QR code with patterns such as positioning, alignment, and timing patterns.
- The encoded data and error correction codes are then filled into the QR code matrix using `drawdatabits()` and `addeccandinterleave()`.

###### Masking Mode:
- The `drawmaskevaluation()` function calculates the score for each mask, and the mask with the lowest score (optimal mask) is selected.
- The mask can be applied to the QR code matrix using the `drawmask()` function to reduce the error rate during the scanning process.

##### (3) Final Data Structure:
- The final data structure of the QR code is a 2D matrix (usually ranging from 21x21 to 177x177), where each cell represents a QR code module. The color of the module represents information (black for 1, white for 0). This matrix structure is then rendered into a scannable QR code image displayed on the user interface.

#### 2. Business Logic Modeling

##### (1) Input Validation:
- The system needs to validate whether the user's input is valid. Two validation methods are used: text format validation and binary data validation.
  - `validateurl(input)` checks whether the user-inputted text is a valid URL.
  - `validateqrcodefile(file)` checks whether the uploaded file meets the QR code data requirements.

##### (2) QR Code Version Selection:
- During QR code generation, `selectqrversion(datalength)` automatically selects the appropriate version based on the length of the input data (from version 1 to version 40).

##### (3) Error Handling:
- `checkdataoverflow(data)` checks if the input data exceeds the maximum capacity of the QR code. If the data overflows, the system returns an error message via `showerrormessage("Data Overflow")`.
- `checkinvalidimage(file)` detects whether the uploaded image file is a valid QR code content. If the recognition fails, `showerror_message("Invalid QR code image")` prompts the user.

#### 3. Graphical User Interface Modeling

##### (1) User Input Field:
- `createinputfield()` creates an input field where the user can input a URL or text. The placeholder is set with `inputfield.setplaceholder("Please enter URL or text")`.

##### (2) Generate Button:
- `creategeneratebutton()` generates the QR code button. When clicked, it triggers the function `generateqr(data)` to generate the QR code.

##### (3) Display Area:
- `createdisplayarea()` creates a display area to show the generated QR code. It returns a label containing the QR code image and a save button.

##### (4) Information Label:
- `createinfolabel()` is used to display information messages to the user.

##### (5) Custom Options:
- Custom options like QR code color, background, error correction level, etc., are provided through the `createcustom_options()` function. These options are linked to the user interface.

##### (6) QR Code Rendering:
- The final QR code image is rendered using various graphic processing functions such as `drawfunctionpatterns()`, `drawdatabits()`, etc.
- Users can view the QR code generation process using `showqrsteps()`, providing a more intuitive experience.

### User Input Management

#### 1. Receive and Validate Input Format

##### (1) GUI: Create an Input Area
- Use the `createinputarea()` function to provide a text input area for the user to enter QR code content.

##### (2) CLI: Direct Input Using `input()`
- Use the `input()` function to directly retrieve QR code content from the user in a CLI environment.

##### (3) Text Validation
- Use the `is_alphanumeric()` and `is_numeric()` methods to validate whether the input text follows the QR code requirements, ensuring it follows a numeric or alphanumeric pattern.

##### (4) URL Validation
- When the input is a URL, use regular expressions to validate whether it follows a proper URL format.

##### (5) Length Check
- Use conditional checks to ensure the length of the input text does not exceed the maximum allowed length for QR codes.

#### 2. Process User Input

##### (1) Encode Input Data
- Use the `encodetext()` function (or `encodebinary()`) to encode the user input (either text or binary data), ensuring the data can be correctly converted into QR code format.

##### (2) Error Correction
- In `Reed-Solomon error`, configure the error correction level (L, M, Q, H) for QR code generation, ensuring the QR code can still be read correctly even when partially damaged.

##### (3) Generate QR Matrix
- Use the `init()` method to generate a 2D matrix for the QR code, which includes data modules, position patterns, alignment patterns, separators, timing patterns, format information, etc.

##### (4) Apply Mask
- Call the `applymask()` function along with `encode_segments` to handle the application of masking, preventing long bars from appearing and ensuring the QR code’s scannability.

#### 3. Handle Invalid Input

##### (1) Empty Input
- If the input is empty, prompt the user via CLI with "Input cannot be empty" and require the user to re-enter the input.

##### (2) Format Error
- If the input format is incorrect (e.g., an invalid URL format or contains invalid characters), use the validation functions (e.g., regular expressions, `isnumeric()`, `isalphanumeric()`) to notify the user and require re-entry.

##### (3) Input Too Long
- When the input exceeds the maximum length supported by QR codes, check the length using `length check` and display a user-friendly prompt, asking the user to shorten the input.

### Data Security and Integrity

#### 1. Data Security and Error Handling

##### (1) Filter Special Characters
- Use regular expressions and string processing functions (like `adjust_image`) to filter out invalid characters from the QR code data.

##### (2) User Security Warning
- Use the `createsecuritywarning()` function to create and display security warning messages, informing the user of potential risks, such as links leading to malicious websites, when scanning the QR code.

##### (3) Catch Input Errors
- Use the `append_bits()` function to ensure that data is correctly added to the bitstream, validating the input is within the valid range. If invalid values (e.g., negative or out-of-range values) are passed, `append_bits()` will raise a `ValueError`, ensuring data integrity and security.

##### (4) Catch System Errors
- Use the `on_closing()` function to handle errors during window closure, binding the event and safely destroying the window to prevent exceptions or resource leaks during the program shutdown.

#### 2. Ensure Data Integrity

##### (1) Ensure Consistent Data Encoding
- The `QRDataBlock` class’s `__init__()` method checks and stores the data mode, character count, and bit data during initialization, ensuring that different data types can consistently be converted into a format suitable for QR code generation.

##### (2) Prevent Data Loss During Generation
- Functions like `get_total_bits`, `getnumdatacodewords`, and `QRDataBlock.gettotalbits` calculate and verify the data capacity, ensuring the generated QR code meets length restrictions and prevents overflow. The `DataTooLongError` is raised when the data is too long, ensuring program robustness.

##### (3) Error Correction
- The `drawformat_bits()` function ensures proper encoding of error correction and mask data for the QR code, maintaining data integrity throughout the QR code generation process.


## Real-World Applications
### Application in Marketing and Product Information Acquisition Scenarios
It is suitable for scenarios such as marketing campaigns and quick access to product information. It provides a simple and intuitive GUI or website, allowing users to quickly input information and generate QR codes without complex operations.

### Application in Inventory and Logistics Scenarios
It is applicable to scenarios like inventory management and logistics tracking that require high reliability and data integrity. Multiple masking patterns are used to ensure that the QR code can be scanned correctly even if it is damaged or blocked. This improves the fault tolerance of QR codes in practical applications, ensures reliable reading by scanners, and adapts to possible environmental interferences.

### Brand Enhancement in Marketing Campaigns
It is suitable for marketing campaigns and helps brands enhance brand recognition. Users are allowed to customize the appearance of QR codes, including color, module shape, and size. This increases the personalization of QR codes, enables combination with brand design, adds visual appeal, and strengthens brand influence.

### Security Risk Prevention
It prevents users from accidentally scanning malicious QR codes. When generating QR codes, users are alerted to potential security risks (such as phishing websites). This raises users' security awareness and reduces risks caused by malicious QR codes, especially in environments where QR codes need to be frequently generated and shared.

### Application in Advertising and Product Tracking Scenarios
It is suitable for scenarios such as advertising and product tracking that require high efficiency in information transmission. The optimal masking pattern is evaluated and selected to optimize the readability of QR codes in different environments, ensuring that QR codes can be scanned quickly and accurately in various environments, and enhancing the information transmission efficiency and user experience.

## Functionality Proof with Test String

### Test String: "Hello"
For a Version 1 QR code (21x21 matrix) with error correction level L, the following intermediate steps validate functionality:
#### - **Encoding**: "Hello" 
![encode data](./generateQR/version1_encode.png)
#### - **Error Correction**: Data is split into blocks, with 7 data codewords and 7 ECC codewords added.
![error correction](./generateQR/bits.png)
#### - **Matrix Construction**: Finder patterns, alignment patterns (1 at center), and timing patterns are drawn. Data and ECC are filled into the matrix.
#### - **Masking**: Mask 0 is applied (e.g., (x + y) % 2 == 0), optimizing readability.
![masking](./generateQR/version1_fig.png)
#### - **Final Output**: The resulting QR code is scannable, decoding back to "Hello".
![result](./generateQR/version1_result.png)


## Demonstration
### This is a demonstration of the QR code generation process.
### The first one is a simple QR code, the second one is a dynamic QR code.
### The QR code results are in the folder `./generateQR`, you can use your phone to scan them!
![simple](./generateQR/simple.gif)
![dynamic](./generateQR/dynamic.gif)

