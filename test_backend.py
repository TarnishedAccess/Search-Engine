#might just be a result of me cutting it early
partially_working_urls = [
    "https://librestock.com/photos/nature/",
    "https://stocksnap.io/search/nature",
    "https://www.nytimes.com/international/"
]

import random
import re
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.http import HtmlResponse
from twisted.internet import reactor
from pathlib import Path
import slugify
import cloudscraper
from aiohttp import web
import aiohttp_cors

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

    ignorable_extensions = []

    image_save_path = Path("downloaded_images")
    if not image_save_path.exists():
        image_save_path.mkdir(parents=True)

    def __init__(self, keyword=None, output=None, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.start_urls.extend(static_urls)
        self.dynamic_urls = dynamic_urls
        self.keyword = keyword
        self.output = output

        for dynamic_url in self.dynamic_urls:
            dynamic_url = dynamic_url.format(keyword=self.keyword)
            self.start_urls.append(dynamic_url)


    def parse(self, response):
        image_index = 0

        for image in response.css("img"):
            image_url = image.css("img::attr(src)").get()
            alt_text = image.css("img::attr(alt)").get() or ""
            surrounding_text = " ".join(
                image.xpath("ancestor::p//text()").getall()
            )

            if image_url:
                if image_url.startswith("//"):
                    image_url = "https:" + image_url
                elif image_url.startswith("/"):
                    image_url = response.urljoin(image_url)

                image_extension = self.get_image_extension(image_url)

                if (
                    image_extension
                    and image_extension not in self.ignorable_extensions
                    and self.keyword in image_url.lower()
                    or self.keyword in alt_text.lower()
                    or self.keyword in surrounding_text.lower()
                    or self.keyword in response.url.lower()
                    or self.keyword in response.xpath("//title/text()").get("").lower()
                ):
                    random_seed = random.randint(0, 1000000)
                    image_name = slugify.slugify(f"{image_index}_{random_seed}") + "." + image_extension
                    image_path = self.image_save_path / image_name

                    yield scrapy.Request(
                        url=image_url,
                        callback=self.save_image,
                        cb_kwargs={"path": image_path}
                    )
                    image_index += 1
                else:
                    self.logger.info(f"Skipping image without keyword match: {image_url}")

        for link in response.css("a::attr(href)").getall():
            yield response.follow(link, callback=self.parse)

    def save_image(self, response, path):
        path.write_bytes(response.body)

        with open(self.output, "a") as f:
            f.write(f"{path}\n")

    def get_image_extension(self, image_url):
        valid_extensions = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff", "webp"}
        
        image_url_base = re.split(r'[?#]', image_url)[0]
        
        parts = image_url_base.split(".")
        for part in reversed(parts):
            if part.lower() in valid_extensions:
                return part.lower()
        
        query_extension_match = re.search(r'[?&](fm|ext)=([a-zA-Z0-9]+)', image_url)
        if query_extension_match:
            query_extension = query_extension_match.group(2).lower()
            if query_extension in valid_extensions:
                return query_extension
        
        return None

#======API Call Handling=======#

search_time = 5

async def get_images(request):
    for f in Path("downloaded_images").iterdir():
        f.unlink()

    with open("output.txt", "w") as f:
        f.write("")

    keywords = request.query.get('keywords')
    process = CrawlerProcess()

    def stop_reactor():
        if reactor.running:
            reactor.stop()

    reactor.callLater(search_time, stop_reactor)

    process.crawl(MetroSpider, keyword=f"{keywords}", output="output.txt")
    process.start()

    with open("output.txt", "r") as f:
        images = f.read().splitlines()

    return web.json_response({'images': images})

def setup_cors(app):

    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    for route in list(app.router.routes()):
        cors.add(route)

app = web.Application()


#Routes
app.router.add_get('/get_images', get_images)
setup_cors(app)

if __name__ == '__main__':
    web.run_app(app, port=8080)

