import multiprocessing
from pathlib import Path
import subprocess
from aiohttp import web
import aiohttp_cors

timeout = 20

def target(keywords, output_file):
    subprocess.run(
        ["python", "metro_spider.py", keywords, output_file],
        capture_output=True,
        text=True
    )

def run_crawler(keywords, output_file, timeout):
    """Runs the crawler with a timeout."""
    process = multiprocessing.Process(
        target=target, 
        args=(keywords, output_file)
    )
    process.start()
    process.join(timeout)
    if process.is_alive():
        process.terminate()
        process.join()
        print("Terminated the crawler due to timeout.")
        
async def get_images(request):
    keywords = request.query.get("keywords")
    print(keywords)
    if not keywords:
        return web.json_response({"error": "No keyword provided"}, status=400)

    for f in Path("downloaded_images").iterdir():
        f.unlink()
    
    output_file = "output.txt"
    with open(output_file, "w") as f:
        f.write("")

    run_crawler(keywords, output_file, timeout)

    # Read results
    with open(output_file, "r") as f:
        images = f.read().splitlines()

    return web.json_response({"images": images})

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
app.router.add_get("/get_images", get_images)
setup_cors(app)

if __name__ == "__main__":
    web.run_app(app, port=8080)
