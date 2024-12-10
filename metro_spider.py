import scrapy
from scrapy.crawler import CrawlerProcess
from pathlib import Path
import re
import slugify
import random

dynamic_urls = [
    "https://unsplash.com/fr/s/photos/{keyword}",
    "https://en.wikipedia.org/w/index.php?fulltext=1&search={keyword}&ns0=1",
    "https://www.flickr.com/search/?text={keyword}",
]

static_urls = [
    "https://www.nbcnews.com/",
    "https://time.com/",
    "https://www.cbsnews.com/",
]

class MetroSpider(scrapy.Spider):
    name = "metro_spider"

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "HTTPERROR_ALLOWED_CODES": [404],
        "USER_AGENT": "metro_spider (+http://www.yourdomain.com)",
        "DEPTH_LIMIT": 1,
    }

    def __init__(self, keyword=None, output=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = static_urls + [url.format(keyword=keyword) for url in dynamic_urls]
        self.keyword = keyword
        self.output = output
        self.image_save_path = Path("downloaded_images")
        if not self.image_save_path.exists():
            self.image_save_path.mkdir(parents=True)

    def parse(self, response):
        image_index = 0

        for image in response.css("img"):
            image_url = image.css("img::attr(src)").get()
            alt_text = image.css("img::attr(alt)").get() or ""
            surrounding_text = " ".join(image.xpath("ancestor::p//text()").getall())

            if image_url:
                if image_url.startswith("//"):
                    image_url = "https:" + image_url
                elif image_url.startswith("/"):
                    image_url = response.urljoin(image_url)

                image_extension = self.get_image_extension(image_url)
                if (
                    image_extension
                    and self.keyword in image_url.lower()
                    or self.keyword in alt_text.lower()
                    or self.keyword in surrounding_text.lower()
                ):
                    image_name = slugify.slugify(f"{random.randint(0, 100000000000)}") + "." + image_extension
                    image_path = self.image_save_path / image_name

                    yield scrapy.Request(
                        url=image_url,
                        callback=self.save_image,
                        cb_kwargs={"path": image_path}
                    )
                    image_index += 1

        for link in response.css("a::attr(href)").getall():
            next_page = response.urljoin(link)
            yield scrapy.Request(url=next_page, callback=self.parse)

    def save_image(self, response, path):
        path.write_bytes(response.body)
        with open(self.output, "a") as f:
            f.write(f"{path}\n")

    def get_image_extension(self, image_url):
        valid_extensions = {"jpg", "jpeg", "png", "gif", "bmp", "webp", "tiff"}
        image_url_base = re.split(r"[?#]", image_url)[0]
        parts = image_url_base.split(".")
        for part in reversed(parts):
            if part.lower() in valid_extensions:
                return part.lower()
        return None


if __name__ == "__main__":
    import sys

    keyword = sys.argv[1]
    output = sys.argv[2]
    process = CrawlerProcess()
    process.crawl(MetroSpider, keyword=keyword, output=output)
    process.start()
