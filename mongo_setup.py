#mongo_setup.py
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv
import os

load_dotenv()

def setup_mongodb_indexes(db_name='yt_comments'):
    MONGO_URI = os.getenv('MONGO_URI')
    
    try:
        client = MongoClient(MONGO_URI)
        db = client[db_name]
        
        print(f"Creating indexes for database: {db_name}...")
        
        db.state_analysis.create_index([("state", ASCENDING)], unique=True)
        print("✓ Created state_analysis index")
        
        db.video_analysis.create_index([("video_id", ASCENDING)], unique=True)
        print("✓ Created video_analysis index")

        db.comments.create_index([("comment_id", ASCENDING)], unique=True)
        db.comments.create_index([("state", ASCENDING)])
        db.comments.create_index([("video_id", ASCENDING)])
        db.video_data.create_index([("video_id", ASCENDING)], unique=True)
        db.video_data.create_index([("channel_id", ASCENDING)])
        db.video_data.create_index([("video_title", ASCENDING)])
        db.video_data.create_index([("video_url", ASCENDING)])
        db.video_data.create_index([("views", ASCENDING)])
        db.video_data.create_index([("timeScraped", ASCENDING)])
        print("✓ Created comments indexes")

        db.comments_with_video.create_index([("comment_id", ASCENDING)], unique=True)
        db.comments_with_video.create_index([("video_id", ASCENDING)])
        db.comments_with_video.create_index([("state", ASCENDING)])
        print("✓ Created comments_with_video indexes")

        # Verify indexes
        print("\nVerifying indexes...")
        print("\nIndexes for comments_with_video:")
        indexes = db.comments_with_video.list_indexes()
        for index in indexes:
            print(f" - {index['name']}: {index['key']}")
        
        print("\nVerifying indexes...")
        for collection in ['state_analysis', 'video_analysis', 'comments']:
            print(f"\nIndexes for {collection}:")
            indexes = db[collection].list_indexes()
            for index in indexes:
                print(f" - {index['name']}: {index['key']}")
        
        print(f"\nAll indexes created successfully for {db_name}!")
        
    except Exception as e:
        print(f"Error setting up indexes: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    #setup_mongodb_indexes('election_comments')
    setup_mongodb_indexes('yt_comments')