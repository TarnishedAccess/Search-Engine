import re
import scrapy
from scrapy.crawler import CrawlerRunner
from scrapy.http import HtmlResponse
from pathlib import Path
from slugify import slugify
import cloudscraper
from twisted.internet import reactor, defer
from aiohttp import web
import aiohttp_cors
import asyncio

static_urls = [
    "https://www.nbcnews.com/",
    "https://time.com/",
    "https://www.cbsnews.com/",
]

dynamic_urls = [
    "https://unsplash.com/fr/s/photos/{keyword}",
    "https://en.wikipedia.org/w/index.php?fulltext=1&search={keyword}&ns0=1",
    "https://www.flickr.com/search/?text={keyword}",
    
]

#might just be a result of me cutting it early
partially_working_urls = [
    "https://librestock.com/photos/nature/",
    "https://stocksnap.io/search/nature",
    "https://www.nytimes.com/international/"
]


#Middleware
class AntiBanMiddleware:
    cloudflare_scraper = cloudscraper.create_scraper()

    def process_response(self, request, response, spider):
        request_url = request.url
        response_status = response.status
        if response_status not in (403, 503):
            return response

        spider.logger.info("Cloudflare detected. Using cloudscraper on URL: %s", request_url)
        cflare_response = self.cloudflare_scraper.get(request_url)
        cflare_res_transformed = HtmlResponse(url=request_url, body=cflare_response.text, encoding='utf-8')
        return cflare_res_transformed

#Spider
class MetroSpider(scrapy.Spider):
    name = "metro_spider"

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "HTTPERROR_ALLOWED_CODES": [404],
        "USER_AGENT": "metro_spider (+http://www.yourdomain.com)",
        "DOWNLOADER_MIDDLEWARES": {
            "__main__.AntiBanMiddleware": 543,
        }
    }

    def __init__(self, keyword=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyword = keyword

        self.static_urls = static_urls
        self.dynamic_urls = dynamic_urls
        self.start_urls = static_urls

        self.image_save_path = Path(f"images_downloaded/{slugify(keyword)}")
        self.image_save_path.mkdir(parents=True, exist_ok=True)
        self.downloaded_images = []

    def parse(self, response):
        image_index = 0
        for image in response.css("img"):
            image_url = image.css("img::attr(src)").get()
            if image_url:
                if image_url.startswith("//"):
                    image_url = "https:" + image_url
                elif image_url.startswith("/"):
                    image_url = response.urljoin(image_url)

                image_extension = self.get_image_extension(image_url)

                if image_extension:
                    image_name = slugify(f"{image_index}_{Path(image_url).stem}") + f".{image_extension}"
                    image_path = self.image_save_path / image_name

                    self.downloaded_images.append(str(image_path))
                    yield scrapy.Request(
                        url=image_url,
                        callback=self.save_image,
                        cb_kwargs={"path": image_path}
                    )

    def save_image(self, response, path):
        path.write_bytes(response.body)

    def get_image_extension(self, image_url):
        valid_extensions = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "svg"}
        parts = re.split(r"[?#]", image_url)[0].split(".")
        for part in reversed(parts):
            if part.lower() in valid_extensions:
                return part.lower()
        return None

# API
async def crawl_and_return_images(keyword):
    runner = CrawlerRunner()
    spider = MetroSpider(keyword=keyword)
    d = runner.crawl(spider)
    await defer.ensureDeferred(d)
    return spider.downloaded_images

async def get_images_by_keywords(request):
    keyword = request.query.get("keywords")
    if not keyword:
        return web.json_response({"error": "Keyword is required"}, status=400)

    try:
        print(keyword)
        images = await crawl_and_return_images(keyword)
        print("yep")
        return web.json_response({"images": images})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

def setup_cors(app):
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })
    for route in app.router.routes():
        cors.add(route)

app = web.Application()
app.router.add_get('/images_by_keywords', get_images_by_keywords)
setup_cors(app)

if __name__ == "__main__":
    web.run_app(app, port=8080)