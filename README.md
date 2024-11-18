# Web Crawler for Text Extraction
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![GitHub Issues](https://img.shields.io/github/issues/simonpierreboucher/llm-generate-function)](https://github.com/simonpierreboucher/llm-generate-function/issues)
[![GitHub Forks](https://img.shields.io/github/forks/simonpierreboucher/llm-generate-function)](https://github.com/simonpierreboucher/llm-generate-function/network)
[![GitHub Stars](https://img.shields.io/github/stars/simonpierreboucher/llm-generate-function)](https://github.com/simonpierreboucher/llm-generate-function/stargazers)

A robust, modular web crawler built in Python for extracting and saving content from websites. This crawler is specifically designed to extract text content from both HTML and PDF files, saving them in a structured format with metadata.

## Features

- Extracts and saves text content from HTML and PDF files
- Adds metadata (URL and timestamp) to each saved file
- Concurrent crawling with configurable workers
- Robust error handling and detailed logging
- Configurable through YAML files
- URL sanitization and normalization
- State preservation and recovery
- Rate limiting and polite crawling
- Command-line interface
- Saves images (PNG, JPG, JPEG) in the `image` folder with their respective formats
- Displays ASCII art ("POWERED", "BY", "M-LAI") every 5 steps during the crawl

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/simonpierreboucher/Crawler.git
   cd Crawler
   ```

2. Create and activate a virtual environment:
   ```bash
   # On Unix/MacOS
   python3 -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. Install the package and dependencies:
   ```bash
   pip install -e .
   ```

## Output Format

Each extracted page is saved as a text file with the following format:

```text
URL: https://www.example.com/page
Timestamp: 2024-11-12 23:45:12
====================================================================================================

[Extracted content from the page]

====================================================================================================
End of content from: https://www.example.com/page
```

Images are saved in the `image` folder with the respective format (PNG, JPG, JPEG).

## Configuration

Configure the crawler through `config/settings.yaml`:

```yaml
domain:
  name: "www.example.com"
  start_url: "https://www.example.com"

timeouts:
  connect: 10
  read: 30
  max_retries: 3
  max_redirects: 5

crawler:
  max_workers: 5
  max_queue_size: 10000
  chunk_size: 8192
  delay_min: 1
  delay_max: 3

files:
  max_length: 200
  max_url_length: 2000
  max_log_size: 10485760  # 10MB
  max_log_backups: 5

excluded:
  extensions:
    - ".jpg"
    - ".jpeg"
    - ".png"
    - ".gif"
    - ".css"
    - ".js"
    - ".ico"
    - ".xml"
  
  patterns:
    - "login"
    - "logout"
    - "signin"
    - "signup"
```

## Usage

### Basic Usage

```bash
python run.py
```

### With Custom Configuration

```bash
python run.py --config path/to/config.yaml --output path/to/output
```

### Resume Previous Crawl

```bash
python run.py --resume
```

### Command-line Options

- `--config, -c`: Path to configuration file (default: config/settings.yaml)
- `--output, -o`: Output directory for crawled content (default: text)
- `--resume, -r`: Resume from previous crawl state

## Project Structure

```
crawler/
│
├── config/
│   ├── __init__.py
│   └── settings.yaml
│
├── src/
│   ├── __init__.py
│   ├── constants.py
│   ├── session.py
│   ├── extractors.py
│   ├── processors.py
│   ├── crawler.py
│   └── utils.py
│
├── requirements.txt
├── setup.py
└── run.py
```

## Dependencies

- requests>=2.31.0
- beautifulsoup4>=4.12.2
- PyPDF2>=3.0.1
- fake-useragent>=1.1.1
- tldextract>=5.0.1
- urllib3>=2.0.7
- pyyaml>=6.0.1
- click>=8.1.7

## Error Handling

The crawler includes:
- Automatic retries for failed requests
- Detailed logging of all errors
- Graceful shutdown on interruption
- State preservation on errors

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Authors

- **Simon-Pierre Boucher** - *Initial work* - [Github](https://github.com/simonpierreboucher)

## Version History

* 0.2
    * Added metadata to saved files
    * Improved error handling
    * Enhanced logging system
    * Display ASCII art at regular intervals (every 5 steps)

* 0.1
    * Initial Release
    * Basic functionality with HTML and PDF support
    * Configurable crawling parameters

## Contact

Project Link: [https://github.com/simonpierreboucher/Crawler](https://github.com/simonpierreboucher/Crawler)
