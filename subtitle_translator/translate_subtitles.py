import re
import requests
import json
import time
import argparse
import os
import pathlib
import logging

# Configure logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to parse SRT
def parse_srt(srt_content):
    if logger.level == logging.DEBUG:
        logger.debug(f"Parsing SRT file with length: {len(srt_content)} characters")
    
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n([\s\S]*?)(?=\n\n\d+\n|$)'
    matches = re.findall(pattern, srt_content)
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Found {len(matches)} subtitle entries")
    
    return [(m[0], m[1], m[2], m[3].strip()) for m in matches]

# Function to create batches of subtitles for translation
def create_batches(parsed_srt, batch_size=15):
    batches = []
    for i in range(0, len(parsed_srt), batch_size):
        batch = parsed_srt[i:i+batch_size]
        batches.append(batch)
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Created {len(batches)} batches with batch_size={batch_size}")
        for i, batch in enumerate(batches):
            logger.debug(f"Batch {i+1} contains {len(batch)} subtitles")
    
    return batches

# Function to translate text using Openrouter.ai with Claude
def translate_batch(batch, api_key, language):
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Create a structured format for the batch
    batch_text = ""
    for idx, (index, start_time, end_time, text) in enumerate(batch):
        batch_text += f"SUBTITLE {index}:\n{text}\n\n"
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Preparing to translate batch with {len(batch)} subtitles to {language}")
        logger.debug(f"First subtitle in batch: SUBTITLE {batch[0][0]}:\n{batch[0][3]}")
        logger.debug(f"Using endpoint: {url}")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "anthropic/claude-3-7-sonnet",
        "messages": [
            {"role": "system", "content": f"You are a professional subtitle translator that translates to {language}. Maintain the meaning and tone of the original text. Do not add or remove content. Return ONLY the translated text for each subtitle, keeping the 'SUBTITLE X:' format intact."},
            {"role": "user", "content": f"Translate these subtitles to {language}. Keep the format with 'SUBTITLE X:' markers:\n\n{batch_text}"}
        ]
    }
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Request payload: {json.dumps(data, indent=2)}")
    
    try:
        if logger.level == logging.DEBUG:
            logger.debug("Sending request to OpenRouter API...")
        
        response = requests.post(url, headers=headers, data=json.dumps(data))
        
        if logger.level == logging.DEBUG:
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response headers: {dict(response.headers)}")
        
        response.raise_for_status()  # Raise exception for HTTP errors
        
        response_json = response.json()
        
        if logger.level == logging.DEBUG:
            logger.debug(f"Response JSON: {json.dumps(response_json, indent=2)}")
            logger.debug(f"Translation model used: {response_json.get('model', 'unknown')}")
            logger.debug(f"Tokens used - prompt: {response_json.get('usage', {}).get('prompt_tokens', 'unknown')}, completion: {response_json.get('usage', {}).get('completion_tokens', 'unknown')}")
        
        translated_content = response_json["choices"][0]["message"]["content"]
        
        if logger.level == logging.DEBUG:
            preview = translated_content[:200] + "..." if len(translated_content) > 200 else translated_content
            logger.debug(f"Translation preview: {preview}")
        
        return translated_content
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        if 'response' in locals():
            logger.error(response.text if hasattr(response, 'text') else "No response text")
        return None

# Function to parse batch translation response
def parse_batch_response(response_text, batch):
    if logger.level == logging.DEBUG:
        logger.debug(f"Parsing translation response with length: {len(response_text)} characters")
    
    translations = {}
    
    # Split by subtitle markers
    parts = re.split(r'SUBTITLE (\d+):', response_text)
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Split response into {len(parts)} parts")
    
    # Skip the first empty element if it exists
    parts = parts[1:] if parts and parts[0] == '' else parts
    
    # Process pairs of (index, translation)
    for i in range(0, len(parts), 2):
        if i+1 < len(parts):
            subtitle_index = parts[i].strip()
            translation = parts[i+1].strip()
            translations[subtitle_index] = translation
            
            if logger.level == logging.DEBUG and i < 2:  # Show first item as example
                preview = translation[:50] + "..." if len(translation) > 50 else translation
                logger.debug(f"Parsed translation for subtitle {subtitle_index}: {preview}")
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Successfully parsed {len(translations)} subtitle translations")
        missing = [index for index, _, _, _ in batch if index not in translations]
        if missing:
            logger.debug(f"Missing translations for subtitle indices: {', '.join(missing[:5])}{' and more...' if len(missing) > 5 else ''}")
    
    # If some indices are missing, use placeholder
    result = []
    for index, start_time, end_time, text in batch:
        if index in translations:
            result.append((index, start_time, end_time, translations[index]))
        else:
            logger.warning(f"Missing translation for subtitle {index}. Using original text.")
            result.append((index, start_time, end_time, text))
    
    return result

# Function to get language code
def get_language_code(language):
    language_codes = {
        'italian': 'it',
        'french': 'fr',
        'spanish': 'es',
        'german': 'de',
        'portuguese': 'pt',
        'dutch': 'nl',
        'russian': 'ru',
        'japanese': 'ja',
        'chinese': 'zh',
        'korean': 'ko',
        'arabic': 'ar',
        'hindi': 'hi',
        'swedish': 'sv',
        'finnish': 'fi',
        'danish': 'da',
        'norwegian': 'no',
        'polish': 'pl',
        'turkish': 'tr', 
        'czech': 'cs',
        'greek': 'el',
        'hungarian': 'hu',
        'romanian': 'ro',
        'thai': 'th',
        'ukrainian': 'uk',
        'vietnamese': 'vi',
        'english': 'en'
        # Add more languages as needed
    }
    
    code = language_codes.get(language.lower(), language.lower()[:2])
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Language code for '{language}': {code}")
    
    return code

# Function to generate output filename
def generate_output_filename(input_file, language):
    language_code = get_language_code(language)
    
    # Parse the input path
    path = pathlib.Path(input_file)
    stem = path.stem
    suffix = path.suffix
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Generating output filename for input: {input_file}")
        logger.debug(f"File stem: {stem}, suffix: {suffix}, language code: {language_code}")
    
    # Check if stem already has a language code (like "subtitles.en")
    parts = stem.split('.')
    if len(parts) > 1 and len(parts[-1]) == 2:
        # Replace existing language code
        old_code = parts[-1]
        parts[-1] = language_code
        new_stem = '.'.join(parts)
        
        if logger.level == logging.DEBUG:
            logger.debug(f"Replacing existing language code '{old_code}' with '{language_code}'")
    else:
        # Add language code
        new_stem = f"{stem}.{language_code}"
        
        if logger.level == logging.DEBUG:
            logger.debug(f"Adding language code '{language_code}' to filename")
    
    # Construct the new path
    result = str(path.with_stem(new_stem))
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Generated output filename: {result}")
    
    return result

# Main process
def translate_srt(input_file, output_file=None, api_key=None, language='Italian', batch_size=15):
    if logger.level == logging.DEBUG:
        logger.debug(f"Starting translation process for {input_file}")
        logger.debug(f"Parameters: language={language}, batch_size={batch_size}")
        logger.debug(f"API key present: {'Yes' if api_key else 'No'}")
    
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if logger.level == logging.DEBUG:
            logger.debug(f"Using API key from environment: {'Found' if api_key else 'Not found'}")
        
        if not api_key:
            raise ValueError("API key is required. Please provide it as an argument or set the OPENROUTER_API_KEY environment variable.")
    
    # Generate output filename if not provided
    if not output_file:
        output_file = generate_output_filename(input_file, language)
        logger.info(f"Auto-generated output filename: {output_file}")
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Reading input file: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Read {len(srt_content)} characters from input file")
    
    parsed_srt = parse_srt(srt_content)
    batches = create_batches(parsed_srt, batch_size)
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Parsed {len(parsed_srt)} subtitles, divided into {len(batches)} batches")
    
    translated_srt = []
    total_batches = len(batches)
    
    for i, batch in enumerate(batches):
        logger.info(f"Translating batch {i+1}/{total_batches} ({len(batch)} subtitles)")
        
        if logger.level == logging.DEBUG:
            batch_indices = [item[0] for item in batch]
            logger.debug(f"Batch {i+1} contains subtitle indices: {', '.join(batch_indices[:5])}{' and more...' if len(batch_indices) > 5 else ''}")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                if logger.level == logging.DEBUG:
                    logger.debug(f"Translation attempt {attempt+1}/{max_retries} for batch {i+1}")
                
                translated_batch_text = translate_batch(batch, api_key, language)
                
                if translated_batch_text:
                    if logger.level == logging.DEBUG:
                        logger.debug(f"Translation successful for batch {i+1}, parsing response")
                    
                    translated_items = parse_batch_response(translated_batch_text, batch)
                    
                    for index, start_time, end_time, translated_text in translated_items:
                        translated_srt.append(f"{index}\n{start_time} --> {end_time}\n{translated_text}\n\n")
                        
                        if logger.level == logging.DEBUG and len(translated_srt) <= 3:  # Show first few as examples
                            preview = translated_text[:50] + "..." if len(translated_text) > 50 else translated_text
                            logger.debug(f"Added translation for subtitle {index}: {preview}")
                    
                    break  # Success, exit retry loop
                else:
                    logger.warning(f"Batch translation failed. Attempt {attempt+1}/{max_retries}")
                    time.sleep(5)  # Wait before retrying
            except Exception as e:
                logger.error(f"Error processing batch: {str(e)}")
                logger.info(f"Attempt {attempt+1}/{max_retries}")
                if logger.level == logging.DEBUG:
                    logger.debug(f"Exception details: {type(e).__name__}: {str(e)}")
                time.sleep(5)
        else:  # This runs if the for loop completes without a break
            logger.error(f"Failed to translate batch {i+1} after {max_retries} attempts. Using original text.")
            for index, start_time, end_time, text in batch:
                translated_srt.append(f"{index}\n{start_time} --> {end_time}\n{text}\n\n")
                if logger.level == logging.DEBUG:
                    logger.debug(f"Using original text for subtitle {index}")
        
        # Add delay to avoid rate limiting
        if i < total_batches - 1:  # No need to delay after the last batch
            if logger.level == logging.DEBUG:
                logger.debug("Waiting between batches to avoid rate limiting...")
            time.sleep(2)
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Writing {len(translated_srt)} translated subtitles to output file: {output_file}")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("".join(translated_srt))
    
    if logger.level == logging.DEBUG:
        logger.debug(f"Translation completed successfully. Output saved to: {output_file}")
    
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Translate SRT subtitles using AI')
    parser.add_argument('--input', required=True, help='Input SRT file')
    parser.add_argument('--output', help='Output SRT file (optional, will be auto-generated if not provided)')
    parser.add_argument('--api_key', help='OpenRouter API key (can also use OPENROUTER_API_KEY env variable)')
    parser.add_argument('--language', default='Italian', help='Target language (default: Italian)')
    parser.add_argument('--batch_size', type=int, default=15, help='Number of subtitles per batch (default: 15)')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    
    args = parser.parse_args()
    
    # Set debug level if requested
    if args.debug:
        logger.setLevel(logging.DEBUG)
        logger.debug("Debug mode enabled")
    
    # Get API key from argument or environment variable
    api_key = args.api_key or os.environ.get('OPENROUTER_API_KEY')
    
    if not api_key:
        logger.error("Error: API key is required. Please provide it with --api_key or set the OPENROUTER_API_KEY environment variable.")
        exit(1)
    
    output_file = translate_srt(args.input, args.output, api_key, args.language, args.batch_size)
    logger.info(f"Translation completed! Output saved to {output_file}")