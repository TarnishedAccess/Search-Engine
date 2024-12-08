import json
from aiohttp import web
import aiohttp_cors

#======Backend Processes=======#

with open('db.json') as f:
    keyword_database = json.load(f)['keywords']

def find_images_by_keywords(keywords):
    
    orSplit = keywords.split('|')
    andSplit = [element.split(',') for element in orSplit]
    output = []

    for orList in andSplit:
        for data in keyword_database:
            if all(element in list(keyword_database[data]) for element in orList) and data not in output:
                output.append(data)

    return output

#======API Call Handling=======#

async def get_images_by_keywords(request):
    keywords = request.query.get('keywords')
    images = find_images_by_keywords(keywords)
    return web.json_response({'images': images})

#======Backend Proper=======#

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
app.router.add_get('/images_by_keywords', get_images_by_keywords)

setup_cors(app)

if __name__ == '__main__':
    web.run_app(app, port=8080)
