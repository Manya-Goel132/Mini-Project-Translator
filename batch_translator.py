import pandas as pd
import json
import argparse
from pathlib import Path
import time
from ai_translator import AITranslator
import logging

class BatchTranslator:
    def __init__(self):
        self.translator = AITranslator()
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for batch operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('batch_translation.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def translate_csv(self, input_file, output_file, text_column, source_lang='auto', target_lang='en'):
        """Translate text in CSV file"""
        try:
            # Read CSV
            df = pd.read_csv(input_file)
            
            if text_column not in df.columns:
                raise ValueError(f"Column '{text_column}' not found in CSV")
            
            self.logger.info(f"Starting batch translation of {len(df)} rows")
            
            # Add translation columns
            df[f'{text_column}_translated'] = ''
            df['translation_method'] = ''
            df['translation_confidence'] = 0.0
            df['translation_time'] = 0.0
            
            # Translate each row
            for idx, row in df.iterrows():
                text = str(row[text_column])
                
                if pd.isna(text) or text.strip() == '':
                    continue
                
                self.logger.info(f"Translating row {idx + 1}/{len(df)}")
                
                result = self.translator.smart_translate(text, source_lang, target_lang)
                
                if result:
                    df.at[idx, f'{text_column}_translated'] = result['translation']
                    df.at[idx, 'translation_method'] = result['method']
                    df.at[idx, 'translation_confidence'] = result['confidence']
                    df.at[idx, 'translation_time'] = result['time']
                else:
                    df.at[idx, f'{text_column}_translated'] = 'TRANSLATION_FAILED'
                    df.at[idx, 'translation_method'] = 'FAILED'
                
                # Small delay to avoid rate limiting
                time.sleep(0.5)
            
            # Save results
            df.to_csv(output_file, index=False)
            self.logger.info(f"Batch translation completed. Results saved to {output_file}")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Batch translation failed: {e}")
            raise
    
    def translate_json(self, input_file, output_file, text_fields, source_lang='auto', target_lang='en'):
        """Translate text fields in JSON file"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                data = [data]  # Convert single object to list
            
            self.logger.info(f"Starting batch translation of {len(data)} JSON objects")
            
            for idx, item in enumerate(data):
                self.logger.info(f"Translating object {idx + 1}/{len(data)}")
                
                for field in text_fields:
                    if field in item and item[field]:
                        text = str(item[field])
                        
                        result = self.translator.smart_translate(text, source_lang, target_lang)
                        
                        if result:
                            item[f'{field}_translated'] = result['translation']
                            item[f'{field}_translation_info'] = {
                                'method': result['method'],
                                'confidence': result['confidence'],
                                'time': result['time'],
                                'source_lang': result['source_lang']
                            }
                        else:
                            item[f'{field}_translated'] = 'TRANSLATION_FAILED'
                
                time.sleep(0.5)  # Rate limiting
            
            # Save results
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"JSON batch translation completed. Results saved to {output_file}")
            
            return data
            
        except Exception as e:
            self.logger.error(f"JSON batch translation failed: {e}")
            raise
    
    def translate_text_file(self, input_file, output_file, source_lang='auto', target_lang='en'):
        """Translate plain text file"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                text = f.read()
            
            self.logger.info(f"Translating text file: {input_file}")
            
            # Split into chunks if text is too long
            max_chunk_size = 4000
            chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
            
            translated_chunks = []
            
            for idx, chunk in enumerate(chunks):
                self.logger.info(f"Translating chunk {idx + 1}/{len(chunks)}")
                
                result = self.translator.smart_translate(chunk, source_lang, target_lang)
                
                if result:
                    translated_chunks.append(result['translation'])
                else:
                    translated_chunks.append(f"[TRANSLATION_FAILED_CHUNK_{idx}]")
                
                time.sleep(1)  # Longer delay for large chunks
            
            # Combine translated chunks
            translated_text = ' '.join(translated_chunks)
            
            # Save result
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(translated_text)
            
            self.logger.info(f"Text file translation completed. Result saved to {output_file}")
            
            return translated_text
            
        except Exception as e:
            self.logger.error(f"Text file translation failed: {e}")
            raise

def main():
    parser = argparse.ArgumentParser(description='Batch Translation Tool')
    parser.add_argument('input_file', help='Input file path')
    parser.add_argument('output_file', help='Output file path')
    parser.add_argument('--source-lang', default='auto', help='Source language code')
    parser.add_argument('--target-lang', default='en', help='Target language code')
    parser.add_argument('--file-type', choices=['csv', 'json', 'txt'], help='File type (auto-detected if not specified)')
    parser.add_argument('--text-column', help='Column name for CSV files')
    parser.add_argument('--text-fields', nargs='+', help='Field names for JSON files')
    
    args = parser.parse_args()
    
    # Auto-detect file type if not specified
    if not args.file_type:
        file_ext = Path(args.input_file).suffix.lower()
        if file_ext == '.csv':
            args.file_type = 'csv'
        elif file_ext == '.json':
            args.file_type = 'json'
        else:
            args.file_type = 'txt'
    
    batch_translator = BatchTranslator()
    
    try:
        if args.file_type == 'csv':
            if not args.text_column:
                raise ValueError("--text-column is required for CSV files")
            
            batch_translator.translate_csv(
                args.input_file,
                args.output_file,
                args.text_column,
                args.source_lang,
                args.target_lang
            )
        
        elif args.file_type == 'json':
            if not args.text_fields:
                raise ValueError("--text-fields is required for JSON files")
            
            batch_translator.translate_json(
                args.input_file,
                args.output_file,
                args.text_fields,
                args.source_lang,
                args.target_lang
            )
        
        elif args.file_type == 'txt':
            batch_translator.translate_text_file(
                args.input_file,
                args.output_file,
                args.source_lang,
                args.target_lang
            )
        
        print(f"✅ Batch translation completed successfully!")
        print(f"📁 Output saved to: {args.output_file}")
        print(f"📊 Check batch_translation.log for detailed logs")
        
    except Exception as e:
        print(f"❌ Batch translation failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())