import re
import requests
import json
import time
import argparse
import os
import pathlib

# Function to parse SRT
def parse_srt(srt_content):
    pattern = r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n([\s\S]*?)(?=\n\n\d+\n|$)'
    matches = re.findall(pattern, srt_content)
    return [(m[0], m[1], m[2], m[3].strip()) for m in matches]

# Function to create batches of subtitles for translation
def create_batches(parsed_srt, batch_size=15):
    batches = []
    for i in range(0, len(parsed_srt), batch_size):
        batch = parsed_srt[i:i+batch_size]
        batches.append(batch)
    return batches

# Function to translate text using Openrouter.ai with Claude
def translate_batch(batch, api_key, language):
    url = "https://openrouter.ai/api/v1/chat/completions"
    
    # Create a structured format for the batch
    batch_text = ""
    for idx, (index, start_time, end_time, text) in enumerate(batch):
        batch_text += f"SUBTITLE {index}:\n{text}\n\n"
    
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
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        response.raise_for_status()  # Raise exception for HTTP errors
        
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error: {str(e)}")
        if 'response' in locals():
            print(response.text if hasattr(response, 'text') else "No response text")
        return None

# Function to parse batch translation response
def parse_batch_response(response_text, batch):
    translations = {}
    
    # Split by subtitle markers
    parts = re.split(r'SUBTITLE (\d+):', response_text)
    
    # Skip the first empty element if it exists
    parts = parts[1:] if parts and parts[0] == '' else parts
    
    # Process pairs of (index, translation)
    for i in range(0, len(parts), 2):
        if i+1 < len(parts):
            subtitle_index = parts[i].strip()
            translation = parts[i+1].strip()
            translations[subtitle_index] = translation
    
    # If some indices are missing, use placeholder
    result = []
    for index, start_time, end_time, text in batch:
        if index in translations:
            result.append((index, start_time, end_time, translations[index]))
        else:
            print(f"Warning: Missing translation for subtitle {index}. Using original text.")
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
    
    return language_codes.get(language.lower(), language.lower()[:2])

# Function to generate output filename
def generate_output_filename(input_file, language):
    language_code = get_language_code(language)
    
    # Parse the input path
    path = pathlib.Path(input_file)
    stem = path.stem
    suffix = path.suffix
    
    # Check if stem already has a language code (like "subtitles.en")
    parts = stem.split('.')
    if len(parts) > 1 and len(parts[-1]) == 2:
        # Replace existing language code
        parts[-1] = language_code
        new_stem = '.'.join(parts)
    else:
        # Add language code
        new_stem = f"{stem}.{language_code}"
    
    # Construct the new path
    return str(path.with_stem(new_stem))

# Main process
def translate_srt(input_file, output_file=None, api_key=None, language='Italian', batch_size=15):
    # Get API key from environment if not provided
    if not api_key:
        api_key = os.environ.get('OPENROUTER_API_KEY')
        if not api_key:
            raise ValueError("API key is required. Please provide it as an argument or set the OPENROUTER_API_KEY environment variable.")
    
    # Generate output filename if not provided
    if not output_file:
        output_file = generate_output_filename(input_file, language)
        print(f"Auto-generated output filename: {output_file}")
    
    with open(input_file, 'r', encoding='utf-8') as f:
        srt_content = f.read()
    
    parsed_srt = parse_srt(srt_content)
    batches = create_batches(parsed_srt, batch_size)
    
    translated_srt = []
    
    for i, batch in enumerate(batches):
        print(f"Translating batch {i+1}/{len(batches)} ({len(batch)} subtitles)")
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                translated_batch_text = translate_batch(batch, api_key, language)
                
                if translated_batch_text:
                    translated_items = parse_batch_response(translated_batch_text, batch)
                    
                    for index, start_time, end_time, translated_text in translated_items:
                        translated_srt.append(f"{index}\n{start_time} --> {end_time}\n{translated_text}\n\n")
                    
                    break  # Success, exit retry loop
                else:
                    print(f"Batch translation failed. Attempt {attempt+1}/{max_retries}")
                    time.sleep(5)  # Wait before retrying
            except Exception as e:
                print(f"Error processing batch: {str(e)}")
                print(f"Attempt {attempt+1}/{max_retries}")
                time.sleep(5)
        else:  # This runs if the for loop completes without a break
            print(f"Failed to translate batch {i+1} after {max_retries} attempts. Using original text.")
            for index, start_time, end_time, text in batch:
                translated_srt.append(f"{index}\n{start_time} --> {end_time}\n{text}\n\n")
        
        # Add delay to avoid rate limiting
        time.sleep(2)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("".join(translated_srt))
    
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Translate SRT subtitles using AI')
    parser.add_argument('--input', required=True, help='Input SRT file')
    parser.add_argument('--output', help='Output SRT file (optional, will be auto-generated if not provided)')
    parser.add_argument('--api_key', help='OpenRouter API key (can also use OPENROUTER_API_KEY env variable)')
    parser.add_argument('--language', default='Italian', help='Target language (default: Italian)')
    parser.add_argument('--batch_size', type=int, default=15, help='Number of subtitles per batch (default: 15)')
    
    args = parser.parse_args()
    
    # Get API key from argument or environment variable
    api_key = args.api_key or os.environ.get('OPENROUTER_API_KEY')
    
    if not api_key:
        print("Error: API key is required. Please provide it with --api_key or set the OPENROUTER_API_KEY environment variable.")
        exit(1)
    
    output_file = translate_srt(args.input, args.output, api_key, args.language, args.batch_size)
    print(f"Translation completed! Output saved to {output_file}")