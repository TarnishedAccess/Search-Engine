import json
from aiohttp import web
import aiohttp_cors

#======Backend Processes=======#

with open('db.json') as f:
    keyword_database = json.load(f)['keywords']

def find_images_by_keyword(keyword):
    output = []
    for data in keyword_database:
        if keyword in keyword_database[data]:
            output.append(data)
    return output

#======API Call Handling=======#

async def get_images_by_keyword(request):
    keyword = request.query.get('keyword')
    images = find_images_by_keyword(keyword)
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
app.router.add_get('/images_by_keyword', get_images_by_keyword)

setup_cors(app)

if __name__ == '__main__':
    web.run_app(app, port=8080)
