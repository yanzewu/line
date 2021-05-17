

__all__ = ['start_application', 'place_block', 'place_image_data', 'wait_client', 'mute_logging']

import threading
import random
import string
import io
import logging
import base64
import json
import queue

try:
    from flask import Flask, request, render_template, send_file, jsonify, Response
except ImportError:
    from ..errors import LineProcessError
    raise LineProcessError('Cannot start server -- please install flask first')


app = Flask('line', template_folder='remote/templates', static_folder='remote/static')
logger = logging.getLogger('line')

history = []
client_queue = {}   # {id: queue of int}

img_storage = {}
_img_ids = list(string.digits + string.ascii_letters)
_has_started = False
_conn_event = threading.Event()
_place_event = threading.Event()

@app.route('/')
def index():
    # print an HTML with ajax; such ajax will visit /s to see if 
    # there is anything new to append.
    return render_template('index.html')


#@app.route('/img')
#def img(img_id):
#    img_id = request.args.get('id')
#    filename, data = img_storage[img_id]
#    return send_file(io.BytesIO(data), mimetype='image/%s' % filename[-3:], attachment_filename=filename, as_attachment=True)


@app.route('/s')
def sequence():
    """ Routinely check. 
    Need an id in request -- defaults to '';
    Response format:
    {
        data: [ array of
            {
                code: str,      <-- code to display
                has_svg: bool,  <-- has svg
                has_img: bool,  <-- has non-svg image
                svg_text: str,  <-- svg text
                img_url: str,   <-- base64 encoded dataurl of image
                img_name: str,  <-- str of image name
            }
        ]
    }
    """
    client_id = request.args.get('id', '')
    logging.getLogger('line').info('Found new client %s' % client_id)

    return Response(stream_block(client_id), mimetype="text/event-stream")


def stream_block(client_id):

    def send_block(id_start, id_end):
        return "data: %s\n\n" % json.dumps({'data':history[id_start:id_end]})

    client_queue[client_id] = queue.Queue()

    yield send_block(0, len(history))   # first time
    _conn_event.set()
    
    while True:
        block_id = client_queue[client_id].get()
        yield send_block(block_id, block_id+1)


def start_application(port):
    """ start the application thread; it can only be ended with the process.
    """
    global _has_started
    if _has_started:
        raise RuntimeError('Application has already started')
    else:
        t = threading.Thread(target=lambda:app.run(port=port, debug=False), daemon=True)
        t.start()
        _has_started = True

def encode_dataurl(data:bytes):
    return 'data:image/png;base64,%s' % base64.b64encode(data).decode('ascii')


def place_block(code, img_id=None, is_svg=False, img_name='image'):
    """ place a code block.
    """
    logger.debug('Sending remote data: code=%s, img_id=%s, img_name=%s, is_svg=%s' % (code, img_id, img_name, is_svg))
    history.append({
        'code': code,
        'has_img': img_id and not is_svg,
        'has_svg': img_id and is_svg,
        'svg_text': img_storage[img_id][1] if img_id and is_svg else '',
        'img_url': encode_dataurl(img_storage[img_id][1]) if img_id and not is_svg else '',
        'img_name': img_name,
    })
    for c in client_queue.values():
        c.put(len(history)-1)


def place_image_data(data, filename):
    """ Add a new image to buffer, return the auto-generated id.
    filename must have 3 char suffix (*.???)
    """
    logger.debug('Image data placed: %s, %d bytes' % (filename, len(data)))
    random.shuffle(_img_ids)
    newid = ''.join(_img_ids[:10])
    img_storage[newid] = (filename, data)
    return newid


def wait_client():
    """ Block until there is a client connected and all the clients are up to date.
    """
    while len(client_queue) == 0 or any(not c.empty() for c in client_queue.values()):
        _conn_event.wait(2)


def mute_logging():
    """ Disable native log of flask
    """
    from flask import cli
    cli.show_server_banner = lambda a,b,c,d:None
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
