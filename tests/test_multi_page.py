"""Smoke-test distinct browser routes against one persistent FSOC engine."""
import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
PAGES = {
    '/': 'Optical acquisition, under control.',
    '/mission': 'Live tracking',
    '/scenarios': 'Scenario library',
    '/benchmark': 'Video benchmark',
    '/analysis': 'Analysis &amp; reports',
    '/engineering': 'Algorithm lab',
}


def test_distinct_pages_shared_engine_and_video(tmp_path):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    root = f'http://127.0.0.1:{port}'
    proc = subprocess.Popen(
        [sys.executable, 'main.py', '--web', '--host', '127.0.0.1',
         '--port', str(port), '--output', str(tmp_path)],
        cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )

    def get(path):
        with urlopen(root + path, timeout=15) as response:
            return response.read(), response.headers['Content-Type']

    def api(path):
        return json.loads(get(path)[0])

    def post(path, data, headers=None, raw=False):
        payload = data if raw else json.dumps(data).encode()
        request = Request(root + path, data=payload,
                          headers=headers or {'Content-Type': 'application/json'})
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read())

    try:
        deadline = time.monotonic() + 18
        while True:
            try:
                assert api('/api/health')['ok']
                break
            except OSError:
                if time.monotonic() > deadline:
                    raise AssertionError('Browser engine failed to start')
                time.sleep(.15)

        post('/api/control', {'action': 'pause'})
        initial = api('/api/state')
        for path, heading in PAGES.items():
            html, mime = get(path)
            assert mime.startswith('text/html')
            assert heading.encode() in html
            assert b'{{' not in html
            assert b'/static/app.js' in html
            assert html.count(b'class="active"') == 1
        assert api('/api/state')['frame'] == initial['frame']
        for resource, kind in [('/static/app.css', 'text/css'),
                               ('/static/app.js', 'javascript'),
                               ('/static/logo.png', 'image/png')]:
            body, mime = get(resource)
            assert kind in mime and len(body) > 100

        assert len(api('/api/presets')) >= 13
        assert len(api('/api/features')) == 55
        assert api('/api/leaderboard') == []
        post('/api/scenario', {'id': 'medium_foggy_figure8'})
        assert api('/api/state')['scenario'] == 'Medium · Fog / Figure Eight'
        post('/api/config', {'name': 'Custom · Multi-page test',
                             'target': {'trajectory': 'spiral'}})
        assert api('/api/state')['settings']['target']['trajectory'] == 'spiral'
        assert post('/api/scenario/save', {'id': 'trial_1'})['ok']
        assert any(x['id']=='trial_1' for x in api('/api/presets'))
        exported, mime = get('/api/config/export')
        assert mime == 'application/json' and json.loads(exported)['control']['kp'] == 14
        assert post('/api/default/save', {})['ok']
        assert (tmp_path/'default_scenario.json').is_file()
        assert post('/api/scenario/random', {'seed': 313})['seed'] == 313
        assert api('/api/state')['settings']['seed'] == 313
        assert post('/api/scenario/import', json.loads(exported))['ok']
        assert api('/api/state')['scenario'] == 'Custom · Multi-page test'
        post('/api/config', {'control': {'kp': 8, 'search_pattern': 'raster'},
                             'tracking': {'hits_to_lock': 4},
                             'disturbance': {'sensor_enabled': True}})
        settings=api('/api/state')['settings']
        assert settings['control']['kp']==8 and settings['tracking']['hits_to_lock']==4
        assert settings['disturbance']['sensor_enabled']
        assert post('/api/network', {})['stations']
        assert post('/api/baseline', {'frames': 15})['frames'] == 15
        assert len(api('/api/leaderboard')) == 1
        weak=post('/api/weakness', {'trials': 2, 'frames': 10})
        assert weak['trials'] == 2
        assert get('/api/experiment.zip?id='+Path(weak['saved_to']).name)[1]=='application/zip'
        assert post('/api/sensitivity', {'frames': 10, 'values': [0, 3]})['parameter']=='disturbance.noise_std'
        post('/api/default/reset', {})
        assert not (tmp_path/'default_scenario.json').exists()
        assert get('/api/raw-frame')[1] == 'image/jpeg'
        deadline = time.monotonic() + 5
        while api('/api/state')['frame'] < 1 and time.monotonic() < deadline:
            time.sleep(.05)
        post('/api/control', {'action': 'pause'})
        post('/api/control', {'action': 'export'})
        assert 'rows' in api('/api/query?min_error=0')
        assert get('/api/report.zip')[1] == 'application/zip'

        source = (ROOT / 'assets/sample_beacon.mp4').read_bytes()
        post('/api/video', source,
             {'Content-Type': 'application/octet-stream', 'X-Extension': '.mp4'}, raw=True)
        assert api('/api/state')['mode'] == 'video'
        assert api('/api/state')['last_export'] is None
        labels = (ROOT / 'assets/sample_beacon.csv').read_text()
        assert post('/api/ground-truth', {'csv': labels})['rows'] == 120
        post('/api/control', {'action': 'seek', 'frame': 5})
        state = api('/api/state')
        assert state['mode'] == 'video' and state['frame'] == 6
        assert state['summary']['ground_truth_available']
        assert state['last_export'] is None
        # EOF replay and configured simulator end both need a real restart,
        # not a misleading Resume button that immediately stops again.
        post('/api/control',{'action':'seek','frame':119})
        assert post('/api/control',{'action':'start'})['restarted'] is True
        post('/api/scenario',{'id':'easy_clear_circular'})
        post('/api/config',{'duration_s':0.1})
        until=time.monotonic()+3
        while api('/api/state')['running'] and time.monotonic()<until:time.sleep(.04)
        assert api('/api/state')['complete']
        assert post('/api/control',{'action':'start'})['restarted'] is True
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)


def test_live_charts_and_map_use_inline_svg():
    """Avoid canvas-dependent charts turning into broken images in preview frames."""
    web = ROOT / 'vcapat/api/companion_web'
    for template, svg_ids in {
        'mission.html': ('mission-chart', 'minimap'),
        'benchmark.html': ('benchmark-chart',),
        'analysis.html': ('analysis-chart',),
    }.items():
        markup = (web / 'templates' / template).read_text(encoding='utf-8')
        for svg_id in svg_ids:
            assert f'<svg id="{svg_id}"' in markup
        assert '<canvas' not in markup
    client = (web / 'static/app.js').read_text(encoding='utf-8')
    assert 'function drawChart(' in client and 'function drawMap(' in client
    assert 'svg.innerHTML=' in client
