

__all__ = ['start_application', 'place_block', 'place_image_data', 'wait_client']

import threading
import random
import string
import io
import logging

try:
    from flask import Flask, request, render_template, send_file, jsonify, Response
except ImportError:
    from ..errors import LineProcessError
    raise LineProcessError('Cannot start server -- please install flask first')


app = Flask('line', template_folder='remote/templates', static_folder='remote/static')

history = []
client_last_sent = {}   # clientid: lastindex of history

img_storage = {}
_img_ids = list(string.digits + string.ascii_letters)
_has_started = False
_conn_event = threading.Event()

logging.getLogger('werkzeug').setLevel(logging.DEBUG)

@app.route('/')
def index():
    # print an HTML with ajax; such ajax will visit /s to see if 
    # there is anything new to append.
    return render_template('index.html')


@app.route('/img')
def img():
    img_id = request.args.get('id')
    fmt, data = img_storage[img_id]
    return send_file(io.BytesIO(data), mimetype='image/%s' % fmt)


@app.route('/s')
def sequence():
    """ Routinely check. 
    Need an id in request -- defaults to '';
    Response format:
    {
        data: [ array of
            {
                code: str,
                has_svg: bool,
                has_img: bool,
                svg_text: str,
                img_id: str,
                img_name: str,
            }
        ]
    }
    """
    client_id = request.args.get('id', '')
    if client_id not in client_last_sent:
        logging.getLogger('line').info('Found new client %s' % client_id)
        client_last_sent[client_id] = 0
        _conn_event.set()
    
    last_index = client_last_sent[client_id]
    client_last_sent[client_id] = len(history)

    return jsonify(data=history[last_index:client_last_sent[client_id]])


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


def place_block(code, img_id=None, is_svg=False, img_name='image'):
    """ place a code block.
    """
    history.append({
        'code': code,
        'has_img': img_id and not is_svg,
        'has_svg': img_id and is_svg,
        'svg_text': img_storage[img_id][1] if img_id and is_svg else '',
        'img_id': img_id,
        'img_name': img_name,
    })


def place_image_data(data, fmt):
    """ Add a new image to buffer, return the auto-generated id
    """
    random.shuffle(_img_ids)
    newid = ''.join(_img_ids[:10])
    img_storage[newid] = (fmt, data)
    return newid


def wait_client():
    while len(client_last_sent) == 0 or any((c != len(history) for c in client_last_sent.values())):
        _conn_event.wait(2)
