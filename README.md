# Web Scraping Project

## Overview
This project is a simple Python web scraper that fetches data from a specified website and saves the extracted information into a CSV file.

## Prerequisites
- **Google Chrome**: Ensure you have Google Chrome installed.
- **Python 3.x**
- `requests` library for making HTTP requests
- `BeautifulSoup` from `bs4` for parsing HTML (not use)
- `re` (regular expressions) for data extraction
- `selenium` for browser automation (if using ChromeDriver)

## Installation

1. **Install Google Chrome**:
   - **macOS**:
     - Download Google Chrome from [the official website](https://www.google.com/chrome/) and follow the installation instructions.
   - **Windows**:
     - Download Google Chrome from [the official website](https://www.google.com/chrome/) and follow the installation instructions.

2. **Clone the repository or download the script**.

3. **Install the required dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

4. **Install ChromeDriver**:
   - **macOS**:
     - If you haven’t installed Homebrew yet, you can do so by running:
       ```bash
       /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
       ```
     - After Homebrew is installed, you can install ChromeDriver with:
       ```bash
       brew install chromedriver
       ```
     - Verify the installation by checking the version:
       ```bash
       chromedriver --version
       ```

   - **Windows**:
     - Download ChromeDriver from the [ChromeDriver download page](https://chromedriver.chromium.org/downloads) and unzip it.
     - Move `chromedriver.exe` to a directory of your choice, such as `C:\Program Files\ChromeDriver`.
     - Add the path to the directory containing `chromedriver.exe` to your system's PATH environment variable.

5. **Configure ChromeDriver in your script**:
   - Replace the executable path in the following line with the path where `chromedriver` is installed on your system:
     ```python
     service = Service(executable_path='YOUR_CHROMEDRIVER_PATH')
     ```
   For example:
   - On **macOS**, it might look like:
     ```python
     service = Service(executable_path='/opt/homebrew/bin/chromedriver')
     ```
   - On **Windows**, it might look like:
     ```python
     service = Service(executable_path='C:\\Program Files\\ChromeDriver\\chromedriver.exe')
     ```

## Usage

1. Run the script:
   ```bash
   python scraping_script.py
   ```

### Important Note:
Make sure to replace any placeholder values such as `YOUR_CHROMEDRIVER_PATH` with the actual paths on your system. This will ensure that the script can locate and use ChromeDriver correctly.
