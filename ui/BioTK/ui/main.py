from flask import Flask

UI = Flask(__name__)

@UI.route('/')
def index():
    return "<span style='color:red'>I am app 2</span>"
