# Web Scraping Project

## Overview
This project is a simple Python web scraper that fetches data from a specified website and saves the extracted information into a CSV file.

## Prerequisites
- **Google Chrome**: Ensure you have Google Chrome installed.
- **Python 3.x**
- `requests` library for making HTTP requests
- `re` (regular expressions) for data extraction
- `selenium` for browser automation (if using ChromeDriver)
- `pyyaml` for read yaml file

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

5. **Update Configuration File (`config.yaml`)**:
   Instead of specifying the URL and ChromeDriver path directly in the script, update them in the `config.yaml` file located in your project directory.

   Example `config.yaml` file:
   ```yaml
   # Configuration for the web scraper
   url: "https://www.capology.com/uk/premier-league/salaries/"
   chromedriver_path: "/opt/homebrew/bin/chromedriver"  # Update this path based on your setup
   ```

   **Note**: Modify the `chromedriver_path` value based on your ChromeDriver installation path.

   - On **macOS**, it might look like:
     ```yaml
     chromedriver_path: "/opt/homebrew/bin/chromedriver"
     ```
   - On **Windows**, it might look like:
     ```yaml
     chromedriver_path: "C:\\Program Files\\ChromeDriver\\chromedriver.exe"
     ```

## Usage

1. Run the script:
   ```bash
   python scraping_script.py
   ```

### Important Note:
- Make sure to update the `config.yaml` file with the correct paths and URLs as described above.
- This ensures that the script can locate and use ChromeDriver correctly and access the required webpage for scraping.

### Configuration Reference
- `url`: The URL of the website to scrape.
- `chromedriver_path`: The path to your installed ChromeDriver executable.

If the `config.yaml` file is not properly configured, the script will not be able to execute correctly, and you might encounter errors when trying to locate the ChromeDriver executable.