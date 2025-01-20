# misc on the fly operations
from pymongo import MongoClient
from dotenv import load_dotenv
import os
import pprint

load_dotenv()

def print_video_data():
    MONGO_URI = os.getenv('MONGO_URI')
    MONGO_URI = os.getenv('MONGO_URI')
    
    try:
        client = MongoClient(MONGO_URI)
        db = client['yt_comments']
        
        video_data_collection = db.video_data
        
        video_data_documents = video_data_collection.find()
        
        print("Contents of video_data collection:")
        for document in video_data_documents:
            pprint.pprint(document)
        
    except Exception as e:
        print(f"Error accessing video_data collection: {e}")
    finally:
        client.close()

def print_comments_with_video_data():
    MONGO_URI = os.getenv('MONGO_URI')
    
    try:
        client = MongoClient(MONGO_URI)
        db = client['yt_comments']
        
        comments_with_video_collection = db.comments_with_video
        
        comments_with_video_documents = comments_with_video_collection.find()
        
        print("Contents of comments_with_video collection:")
        for document in comments_with_video_documents:
            pprint.pprint(document)
        
    except Exception as e:
        print(f"Error accessing comments_with_video collection: {e}")
    finally:
        client.close()

def clear_comments_with_video_collection():
    MONGO_URI = os.getenv('MONGO_URI')
    
    try:
        client = MongoClient(MONGO_URI)
        db = client['yt_comments']
        
        comments_with_video_collection = db.comments_with_video
        
        result = comments_with_video_collection.delete_many({})
        print(f"Deleted {result.deleted_count} documents from comments_with_video collection.")
        
    except Exception as e:
        print(f"Error clearing comments_with_video collection: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    #print_video_data()
    print_comments_with_video_data()
    #clear_comments_with_video_collection()
