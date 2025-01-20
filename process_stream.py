# process_stream.py
'''
watchdog script that watches the temp directory for new videos, scrapes the comments, and upserts the data into MongoDB
runs constantly, and will continue to scrape comments for videos that match the filter words
'''
import csv
import json
import os
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from datetime import datetime
import pandas as pd
import time
import subprocess
from pymongo import MongoClient

from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv('MONGO_URI')
client = MongoClient(MONGO_URI)
db = client['yt_comments']

class VideoDataHandler(FileSystemEventHandler):
    def __init__(self, master_csv='data/master_videos.csv'):
        self.master_csv = master_csv
        self.ensure_master_csv_exists()
        self.client = MongoClient(MONGO_URI)
        self.db = self.client['yt_comments']
        self.comments_scraped_file = 'data/comments_scraped.json'
        self.comments_scraped = self.load_comments_scraped()

    def ensure_master_csv_exists(self):
        """Create master CSV if it doesn't exist"""
        if not os.path.exists('data'):
            os.makedirs('data')
            
        if not os.path.exists(self.master_csv):
            with open(self.master_csv, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['channel_id', 'video_id', 'video_title', 
                               'video_url', 'views', 'timeScraped'])

    def load_comments_scraped(self):
        if os.path.exists(self.comments_scraped_file):
            with open(self.comments_scraped_file, 'r') as f:
                return json.load(f)
        else:
            with open(self.comments_scraped_file, 'w') as f:
                json.dump({}, f)
            return {}

    def save_comments_scraped(self):
        with open(self.comments_scraped_file, 'w') as f:
            json.dump(self.comments_scraped, f)

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('_videos.json'):
            return

        try:
            time.sleep(2)
            with open(event.src_path, 'r') as f:
                data = json.load(f)
            
            try:
                df_master = pd.read_csv(self.master_csv)
            except pd.errors.EmptyDataError:
                df_master = pd.DataFrame(columns=['channel_id', 'video_id', 
                                                'video_title', 'video_url', 
                                                'views', 'timeScraped'])
            
            new_rows = []
            for video in data['videos']:
                video_data = {
                    'channel_id': data['channelId'],
                    'video_id': video['videoId'],
                    'video_title': video['title'],
                    'video_url': video['url'],
                    'views': video['views'],
                    'timeScraped': video['timeScraped']
                }
                new_rows.append(video_data)
                #print rows added
                print(f"Added {len(new_rows)} rows to master CSV")
                # upsert
                self.db.video_data.update_one(
                    {'video_id': video_data['video_id']},
                    {'$set': video_data},
                    upsert=True
                )
            
            df_new = pd.DataFrame(new_rows)
            
            df_combined = pd.concat([df_master, df_new])
            df_combined = df_combined.sort_values('timeScraped', ascending=False)
            df_combined = df_combined.drop_duplicates(subset='video_id', keep='first')
            # these are the words that will be used to determine which videos to scrape comments for
            filter_words = ['traffic', 'accident', 'crash', 'road', 'highway', 'construction', 'commute', 'delays']
            # we want the videos that contain any of these words in the video title
            df_combined = df_combined[df_combined['video_title'].str.lower().str.contains(r'(?i)' + '|'.join(filter_words), regex=True)]
            
            df_combined.to_csv(self.master_csv, index=False)

            df_new = df_new.sort_values('timeScraped', ascending=False)
            df_new = df_new.drop_duplicates(subset='video_id', keep='first')
            df_new = df_new[
                (df_new['video_title'].str.contains(r'(?i)' + '|'.join(filter_words), regex=True)) & 
                (~df_new['video_id'].isin(self.comments_scraped))
            ]

            for _, row in df_new.iterrows():
                print("Scraping comments for: ", row['video_title'])
                # bottleneck here
                scrape_comments(row['video_id'], row['channel_id'])
                self.comments_scraped[row['video_id']] = True
                self.save_comments_scraped()
            os.remove(event.src_path)
            
            print(f"Processed and added videos from {data['channelId']}")
            
        except Exception as e:
            print(f"Error processing {event.src_path}: {str(e)}")

    def __del__(self):
        self.client.close()
        self.save_comments_scraped()

def scrape_comments(video_id, channel_id):
    # bottleneck, we're launching a new node process (and browser) for each video
    comment_scrape_cmd = f"xvfb-run -a node comment_scrape.js https://www.youtube.com/watch?v={video_id}"
    try:
        result = subprocess.run(comment_scrape_cmd, shell=True, check=True, capture_output=True, text=True, timeout=300)
        print(f"Successfully scraped comments for video {video_id}")
        #remove data.json
        os.remove('output/com_youtubei_v1_next/data.json')
        print(f"Output: {result.stdout}")
    except subprocess.TimeoutExpired:
        print(f"Timeout occurred while scraping comments for video {video_id}")
        return
    except subprocess.CalledProcessError as e:
        print(f"Error scraping comments for video {video_id}: {e}")
        #remove data.json
        os.remove('output/com_youtubei_v1_next/data.json')
        print(f"Error output: {e.output}")
        return
    except Exception as e:
        print(f"Unexpected error occurred while scraping comments for video {video_id}: {str(e)}")
        return

    output_dir = f"data/{channel_id}/{video_id}"
    os.makedirs(output_dir, exist_ok=True)
    source_file = f"transcript_scrape/scraped_comments/{video_id}_comments.csv"
    destination_file = f"{output_dir}/comments.csv"
    
    if os.path.exists(source_file):
        os.rename(source_file, destination_file)
        print(f"Moved comments file to {destination_file}")
    else:
        print(f"Warning: Comments file not found at {source_file}")

def main():
    observer = Observer()
    event_handler = VideoDataHandler()
    
    observer.schedule(event_handler, 'temp', recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    
    observer.join()

if __name__ == "__main__":
    main()
