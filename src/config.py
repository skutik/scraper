import os

# TODO: Change values for env variables
MONGODB_CONN_STRING = f"mongodb+srv://rw_dave:{os.getenv('MONGODB_RW_PASS')}@cluster0-6lpd8.mongodb.net/test?retryWrites=true&w=majority"
TEST_DATABALSE = "test_db"
ESTATE_COLLECTION = "estates"
USERS_COLLECTION = "users"
FILTERS_COLLECTION = "filters"
PRODUCTION_DATABASE = "estate_scraper"
