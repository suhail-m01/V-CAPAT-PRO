"""Run the shared mobile-responsive dashboard against a fresh simulator."""
from pathlib import Path
from ...config.settings import Scenario
from ...core.engine import Engine
from ..rest_server import serve

def main(host='0.0.0.0',port=8000):
    root=Path(__file__).resolve().parents[3]
    serve(Engine(Scenario.load(root/'scenarios'/'easy_clear_circular.json')),host,port,root/'scenarios',root/'reports')

if __name__=='__main__':main()
