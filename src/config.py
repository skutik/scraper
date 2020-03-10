import os

MONGODB_CONN_STRING = f"mongodb+srv://rw_dave:{os.getenv('MONGODB_RW_PASS')}@cluster0-6lpd8.mongodb.net/test?retryWrites=true&w=majority"