# SRT Subtitle Translator

A powerful Python script for translating SRT subtitle files from English to any language using AI, with OpenRouter.ai and Claude as the default model.

## Features

- Translate subtitle files while preserving all original timestamps
- Process subtitles in batches to maintain context and improve translation quality
- Support for any target language
- Configurable batch sizes to optimize for context vs. token limits
- Command-line interface for easy integration into workflows
- API key can be provided via command-line or environment variable
- Robust error handling with automatic retries
- Progress reporting during translation

## Requirements

- Python 3.6 or higher
- `requests` library (`pip install requests`)
- An [OpenRouter.ai](https://openrouter.ai/) API key

## Installation

1. Clone this repository or download the script
2. Install the required packages:

```bash
pip install requests
```

Or use the included requirements.txt:

```bash
pip install -r requirements.txt
```

## Usage

### Command Line

```bash
python translate_subtitles.py --input your_subtitle.srt --output translated.srt --api_key your_openrouter_api_key --language Italian --batch_size 15
```

#### Arguments

- `--input`: Path to the input SRT file (required)
- `--output`: Path for the translated output file (required)
- `--api_key`: Your OpenRouter API key (can be omitted if using environment variable)
- `--language`: Target language for translation (default: Italian)
- `--batch_size`: Number of subtitles to translate in each batch (default: 15)

### Using Environment Variable

You can set your API key as an environment variable and omit it from the command line:

```bash
# Set the API key as an environment variable
export OPENROUTER_API_KEY="your_api_key_here"

# Run without passing the API key argument
python translate_subtitles.py --input your_subtitle.srt --output translated.srt --language Italian
```

On Windows:
```cmd
set OPENROUTER_API_KEY=your_api_key_here
```
Or in PowerShell:
```powershell
$env:OPENROUTER_API_KEY = "your_api_key_here"
```

### As a Module

```python
from translate_subtitles import translate_srt

translate_srt(
    input_file="your_subtitle.srt", 
    output_file="translated.srt", 
    api_key="your_openrouter_api_key",
    language="French",  # Can be any language
    batch_size=20       # Adjust batch size as needed
)
```

## Optimizing Translations

### Batch Size

- **Larger batches** (20-30): Better context awareness but may hit token limits with the AI model
- **Smaller batches** (5-10): Processes more reliably but with potentially less context
- **Default** (15): A balanced approach for most subtitle files

### Performance Considerations

- The script includes a 2-second delay between batches to avoid rate limiting
- For very large SRT files, consider increasing the batch size to reduce the number of API calls
- Translations are processed sequentially with progress updates

## Error Handling

- The script will retry failed batches up to 3 times
- If a batch fails after all retries, the original text will be preserved
- Warning messages will be shown for any processing issues

## License

MIT

## Acknowledgments

- Uses [OpenRouter.ai](https://openrouter.ai/) as the API gateway
- Default model is Claude 3.7 Sonnet from Anthropic

---

*Note: This tool is designed for personal or educational use. Be mindful of copyright when translating commercial content.*