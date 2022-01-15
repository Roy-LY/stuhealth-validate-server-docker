from flask import Flask
from validation import *

app = Flask(__name__)


@app.route("/refreshToken")
def validation_api():
    return {
        "validation_token": getValidation()
    }


if __name__ == "__main__":
    listen_host = os.environ.get("STUHEALTH_VALIDATOR_LISTEN_HOST")
    if listen_host == None:
        listen_host = "localhost"
    listen_port = os.environ.get("STUHEALTH_VALIDATOR_LISTEN_PORT")
    if listen_port == None:
        listen_port = 5000
    else:
        listen_port = int(listen_port)
    app.run(host=listen_host, port=listen_port)
