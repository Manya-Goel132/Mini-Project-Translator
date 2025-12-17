"""
Batch Translation Tool with Celery Task Queue
Professional, scalable batch processing using distributed workers
"""

import pandas as pd
import json
import argparse
from pathlib import Path
import time
from tasks import translate_batch
from celery.result import AsyncResult
from celery_config import celery_app
import logging


class CeleryBatchTranslator:
    """Batch translator using Celery for distributed processing"""
    
    def __init__(self):
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for batch operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('batch_translation_celery.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def wait_for_task(self, task_id, poll_interval=2):
        """Wait for task to complete and show progress"""
        task = AsyncResult(task_id, app=celery_app)
        
        while not task.ready():
            if task.state == 'PROGRESS':
                progress = task.info
                current = progress.get('current', 0)
                total = progress.get('total', 0)
                self.logger.info(f"Progress: {current}/{total} ({current/total*100:.1f}%)")
            else:
                self.logger.info(f"Task status: {task.state}")
            
            time.sleep(poll_interval)
        
        if task.successful():
            return task.result
        else:
            raise Exception(f"Task failed: {task.info}")
    
    def translate_csv(self, input_file, output_file, text_column, source_lang='auto', target_lang='en', wait=True):
        """Translate text in CSV file using Celery workers"""
        try:
            df = pd.read_csv(input_file)
            
            if text_column not in df.columns:
                raise ValueError(f"Column '{text_column}' not found in CSV")
            
            self.logger.info(f"Starting batch translation of {len(df)} rows")
            
            # Extract texts
            texts = df[text_column].fillna('').astype(str).tolist()
            
            # Queue batch translation task
            self.logger.info("Queuing translation task...")
            task = translate_batch.delay(texts, source_lang, target_lang)
            self.logger.info(f"Task queued with ID: {task.id}")
            
            if not wait:
                self.logger.info("Task queued. Run with --wait to wait for completion.")
                return task.id
            
            # Wait for completion
            self.logger.info("Waiting for task to complete...")
            result = self.wait_for_task(task.id)
            
            if not result['success']:
                raise Exception(f"Batch translation failed: {result.get('error')}")
            
            # Process results
            translations = result['results']
            
            df[f'{text_column}_translated'] = ''
            df['translation_method'] = ''
            df['translation_confidence'] = 0.0
            df['translation_cached'] = False
            
            for trans in translations:
                idx = trans['index']
                if trans['success']:
                    df.at[idx, f'{text_column}_translated'] = trans['translation']
                    df.at[idx, 'translation_method'] = trans['method']
                    df.at[idx, 'translation_confidence'] = trans['confidence']
                    df.at[idx, 'translation_cached'] = trans.get('cached', False)
                else:
                    df.at[idx, f'{text_column}_translated'] = 'TRANSLATION_FAILED'
                    df.at[idx, 'translation_method'] = 'FAILED'
            
            df.to_csv(output_file, index=False)
            self.logger.info(f"Batch translation completed. Results saved to {output_file}")
            
            # Statistics
            successful = sum(1 for t in translations if t['success'])
            cached = sum(1 for t in translations if t.get('cached', False))
            self.logger.info(f"Statistics: {successful}/{len(translations)} successful, {cached} from cache")
            
            return df
            
        except Exception as e:
            self.logger.error(f"Batch translation failed: {e}")
            raise
    
    def translate_json(self, input_file, output_file, text_fields, source_lang='auto', target_lang='en', wait=True):
        """Translate text fields in JSON file using Celery workers"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, dict):
                data = [data]
            
            self.logger.info(f"Starting batch translation of {len(data)} JSON objects")
            
            # Collect all texts to translate
            all_texts = []
            text_map = []  # Track which text belongs to which object/field
            
            for obj_idx, item in enumerate(data):
                for field in text_fields:
                    if field in item and item[field]:
                        text = str(item[field])
                        all_texts.append(text)
                        text_map.append((obj_idx, field))
            
            self.logger.info(f"Total texts to translate: {len(all_texts)}")
            
            # Queue batch translation task
            self.logger.info("Queuing translation task...")
            task = translate_batch.delay(all_texts, source_lang, target_lang)
            self.logger.info(f"Task queued with ID: {task.id}")
            
            if not wait:
                self.logger.info("Task queued. Run with --wait to wait for completion.")
                return task.id
            
            # Wait for completion
            self.logger.info("Waiting for task to complete...")
            result = self.wait_for_task(task.id)
            
            if not result['success']:
                raise Exception(f"Batch translation failed: {result.get('error')}")
            
            # Process results
            translations = result['results']
            
            for trans in translations:
                idx = trans['index']
                obj_idx, field = text_map[idx]
                
                if trans['success']:
                    data[obj_idx][f'{field}_translated'] = trans['translation']
                    data[obj_idx][f'{field}_translation_info'] = {
                        'method': trans['method'],
                        'confidence': trans['confidence'],
                        'cached': trans.get('cached', False)
                    }
                else:
                    data[obj_idx][f'{field}_translated'] = 'TRANSLATION_FAILED'
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"JSON batch translation completed. Results saved to {output_file}")
            
            # Statistics
            successful = sum(1 for t in translations if t['success'])
            cached = sum(1 for t in translations if t.get('cached', False))
            self.logger.info(f"Statistics: {successful}/{len(translations)} successful, {cached} from cache")
            
            return data
            
        except Exception as e:
            self.logger.error(f"JSON batch translation failed: {e}")
            raise
    
    def check_task_status(self, task_id):
        """Check status of a queued task"""
        task = AsyncResult(task_id, app=celery_app)
        
        status_info = {
            'task_id': task_id,
            'state': task.state,
            'ready': task.ready(),
            'successful': task.successful() if task.ready() else None
        }
        
        if task.state == 'PROGRESS':
            status_info['progress'] = task.info
        elif task.ready():
            if task.successful():
                status_info['result'] = task.result
            else:
                status_info['error'] = str(task.info)
        
        return status_info


def main():
    parser = argparse.ArgumentParser(description='Batch Translation Tool with Celery')
    parser.add_argument('input_file', nargs='?', help='Input file path')
    parser.add_argument('output_file', nargs='?', help='Output file path')
    parser.add_argument('--source-lang', default='auto', help='Source language code')
    parser.add_argument('--target-lang', default='en', help='Target language code')
    parser.add_argument('--file-type', choices=['csv', 'json'], help='File type (auto-detected if not specified)')
    parser.add_argument('--text-column', help='Column name for CSV files')
    parser.add_argument('--text-fields', nargs='+', help='Field names for JSON files')
    parser.add_argument('--no-wait', action='store_true', help='Queue task and exit without waiting')
    parser.add_argument('--check-task', help='Check status of a task by ID')
    
    args = parser.parse_args()
    
    batch_translator = CeleryBatchTranslator()
    
    # Check task status mode
    if args.check_task:
        status = batch_translator.check_task_status(args.check_task)
        print(f"\n📊 Task Status:")
        print(f"Task ID: {status['task_id']}")
        print(f"State: {status['state']}")
        print(f"Ready: {status['ready']}")
        
        if 'progress' in status:
            progress = status['progress']
            print(f"Progress: {progress.get('current', 0)}/{progress.get('total', 0)}")
        
        if status.get('successful'):
            print(f"✅ Task completed successfully")
            result = status.get('result', {})
            if 'total' in result:
                print(f"Total processed: {result['total']}")
        elif status.get('successful') is False:
            print(f"❌ Task failed: {status.get('error')}")
        
        return 0
    
    # Translation mode
    if not args.input_file or not args.output_file:
        parser.error("input_file and output_file are required for translation")
    
    # Auto-detect file type if not specified
    if not args.file_type:
        file_ext = Path(args.input_file).suffix.lower()
        if file_ext == '.csv':
            args.file_type = 'csv'
        elif file_ext == '.json':
            args.file_type = 'json'
        else:
            parser.error("Cannot auto-detect file type. Please specify --file-type")
    
    wait = not args.no_wait
    
    try:
        if args.file_type == 'csv':
            if not args.text_column:
                raise ValueError("--text-column is required for CSV files")
            
            result = batch_translator.translate_csv(
                args.input_file,
                args.output_file,
                args.text_column,
                args.source_lang,
                args.target_lang,
                wait=wait
            )
            
            if not wait:
                print(f"✅ Task queued with ID: {result}")
                print(f"Check status with: python app_batch_celery.py --check-task {result}")
            else:
                print(f"✅ Batch translation completed successfully!")
                print(f"📁 Output saved to: {args.output_file}")
        
        elif args.file_type == 'json':
            if not args.text_fields:
                raise ValueError("--text-fields is required for JSON files")
            
            result = batch_translator.translate_json(
                args.input_file,
                args.output_file,
                args.text_fields,
                args.source_lang,
                args.target_lang,
                wait=wait
            )
            
            if not wait:
                print(f"✅ Task queued with ID: {result}")
                print(f"Check status with: python app_batch_celery.py --check-task {result}")
            else:
                print(f"✅ Batch translation completed successfully!")
                print(f"📁 Output saved to: {args.output_file}")
        
        print(f"📊 Check batch_translation_celery.log for detailed logs")
        
    except Exception as e:
        print(f"❌ Batch translation failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
