from src.config import CACHE_PATH
from src.extract.extractor import YT_API_Crawler
from src.extract.lfm_loader import Loader

## Main function for extracting youtube music videos and storing it in the database
if __name__ == '__main__':
    loader = Loader(CACHE_PATH)
    crawler = YT_API_Crawler()

    shuffler = loader.shuffled_list()

    for i in range(0, 2):
        crawler.search_for_music_video(next(shuffler))
