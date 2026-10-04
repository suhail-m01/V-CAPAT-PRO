"""No-extra-dependency local control room + JSON REST API. Bind intentionally configurable."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import json,threading,time,cv2,io,zipfile,datetime,mimetypes,html,secrets,logging
from urllib.parse import urlparse,parse_qs
from ..config.settings import Scenario
from ..core.feature_registry import feature_payload
from ..core.engine import Engine
from ..metrics.reporter import export_session
from ..io.ground_truth import load_ground_truth
from ..metrics.collector import summarize
from ..metrics.compliance import compliance
from ..stress.stress_suite import compare_detectors,stress_suite,signal_injection,save_experiment
from ..stress.sensitivity import sweep
from ..stress.adversarial import search_weakness
from ..io.scenario_manager import perturb_scenario
from ..io.tle_loader import ground_station_look_angles
from datetime import timezone
from ..metrics.achievements import earned_achievements
from ..metrics.forecast import forecast_risk
from ..metrics.baseline import compare_to_static
from ..link.network import evaluate_network
from ..metrics.time_series_db import query_anomalies
from ..plugins.loader import discover
from .websocket_stream import handle_websocket
from ..utils.qr_code import dashboard_qr_png

class Runtime:
    def __init__(self,engine,presets,output):
        self.engine=engine;self.presets=Path(presets);self.output=Path(output)
        self.lock=threading.RLock();self.running=True;self.alive=True;self.last_export=None;self.error=None
        threading.Thread(target=self.loop,daemon=True).start()
    def loop(self):
        while self.alive:
            before=time.monotonic()
            with self.lock:
                if self.running:
                    try:result=self.engine.step()
                    except Exception as exc:
                        logging.exception('Engine frame failed');self.error=str(exc);self.running=False;result=None
                    if result is None:self.running=False
                    elif self.engine.source=='simulator' and result['timestamp_s']>=self.engine.config.duration_s:self.running=False
            interval=1/(self.engine.video_fps if self.engine.source!='simulator' else self.engine.config.camera.update_hz)
            time.sleep(max(.001,interval-(time.monotonic()-before)))
    def snapshot(self):
        with self.lock:
            result=self.engine.snapshot()
            result['running']=self.running
            result['complete']=bool(not self.running and ((self.engine.source=='simulator' and self.engine.last is not None and self.engine.last['timestamp_s']>=self.engine.config.duration_s) or (self.engine.source=='video' and self.engine.video is not None and self.engine.video.get(cv2.CAP_PROP_POS_FRAMES)>=self.engine.video.get(cv2.CAP_PROP_FRAME_COUNT)>0)))
            result['summary']=summarize(self.engine.rows,self.engine.tracker)
            result['compliance']=compliance(result['summary']) if result['summary'] else {}
            result['settings']=self.engine.config.to_dict()
            result['last_export']=self.last_export
            result['runtime_error']=self.error
            result['achievements']=earned_achievements(self.engine.rows,result['summary'])
            result['forecast']=forecast_risk(self.engine.rows)
            return result
    def reset(self,scenario=None):
        with self.lock:
            self.engine.close();self.engine=Engine(scenario or self.engine.config);self.last_export=None;self.error=None;self.running=True

def serve(engine,host='0.0.0.0',port=8000,presets='scenarios',output='reports'):
    runtime=Runtime(engine,presets,output)
    class Handler(BaseHTTPRequestHandler):
        protocol_version='HTTP/1.1'  # required by RFC 6455 browser WebSocket upgrade
        def log_message(self,fmt,*args):pass
        def send(self,status,body,content='application/json',filename=None):
            if isinstance(body,(dict,list)):body=json.dumps(body,default=str).encode()
            elif isinstance(body,str):body=body.encode()
            self.send_response(status);self.send_header('Content-Type',content);self.send_header('Cache-Control','no-store')
            if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
            self.send_header('Content-Length',str(len(body)));self.end_headers()
            try:
                self.wfile.write(body)
                self.wfile.flush()
            except OSError:
                # Browsers intentionally cancel stale JPEG/asset requests while the
                # live dashboard is refreshing.  On Windows this commonly surfaces
                # as ConnectionAbortedError / WinError 10053.  A disconnected client
                # is not a server failure, so close only this request quietly.
                self.close_connection=True
        def do_GET(self):
            path=urlparse(self.path).path
            web_root=Path(__file__).parent/'companion_web'
            pages={'/':('overview','Overview'),'/mission':('mission','Live tracking'),
                   '/scenarios':('scenarios','Scenarios'),'/benchmark':('benchmark','Video benchmark'),
                   '/analysis':('analysis','Analysis & reports'),'/engineering':('engineering','Algorithm lab')}
            if path in pages:
                page,title=pages[path]
                shell=(web_root/'templates'/'index.html').read_text(encoding='utf-8')
                body=(web_root/'templates'/f'{page}.html').read_text(encoding='utf-8')
                shell=shell.replace('{{CONTENT}}',body).replace('{{PAGE_ID}}',page).replace('{{TITLE}}',html.escape(title))
                for nav in ('overview','mission','scenarios','benchmark','analysis','engineering'):
                    shell=shell.replace('{{NAV_'+nav.upper()+'}}','active' if nav==page else '')
                return self.send(200,shell,'text/html; charset=utf-8')
            static={'/static/app.css':web_root/'static'/'app.css',
                    '/static/app.js':web_root/'static'/'app.js',
                    '/static/logo.png':Path(__file__).resolve().parents[2]/'assets'/'logo.png'}
            if path in static:return self.send(200,static[path].read_bytes(),
                                              mimetypes.guess_type(path)[0] or 'application/octet-stream')
            if path in ('/api/state','/metrics'):return self.send(200,runtime.snapshot())
            if path=='/ws':return handle_websocket(self,runtime.snapshot)
            if path=='/api/experiment.zip':
                label=parse_qs(urlparse(self.path).query).get('id',[''])[0]
                if not label.startswith('experiment_') or not label.replace('_','').replace('-','').isalnum():
                    return self.send(400,{'error':'Invalid experiment identifier'})
                folder=runtime.output/label
                if not folder.is_dir():return self.send(404,{'error':'Experiment not found'})
                memory=io.BytesIO()
                with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as archive:
                    for file in folder.rglob('*'):
                        if file.is_file():archive.write(file,file.relative_to(folder))
                return self.send(200,memory.getvalue(),'application/zip',label+'.zip')
            if path in ('/api/report.zip','/api/query'):
                with runtime.lock:
                    if not runtime.last_export:
                        if not runtime.engine.rows:return self.send(400,{'error':'Process at least one frame before exporting evidence.'})
                        runtime.last_export=export_session(runtime.engine,runtime.output)
                    folder=Path(runtime.last_export)
                if path=='/api/query':
                    try:
                        args=parse_qs(urlparse(self.path).query)
                        records=query_anomalies(folder/'frames.sqlite',float(args.get('min_error',[15])[0]),int(args.get('limit',[100])[0]),args.get('metric',['pointing'])[0])
                        return self.send(200,{'rows':records,'session':folder.name})
                    except (ValueError,TypeError) as exc:return self.send(400,{'error':str(exc)})
                memory=io.BytesIO()
                with zipfile.ZipFile(memory,'w',zipfile.ZIP_DEFLATED) as archive:
                    for file in folder.rglob('*'):
                        if file.is_file():archive.write(file,file.relative_to(folder))
                return self.send(200,memory.getvalue(),'application/zip',folder.name+'.zip')
            if path=='/api/features':return self.send(200,feature_payload())
            if path=='/api/plugins':return self.send(200,discover())
            if path=='/api/config/export':
                with runtime.lock:payload=json.dumps(runtime.engine.config.to_dict(),indent=2).encode()
                return self.send(200,payload,'application/json','vcapat_scenario.json')
            if path=='/api/default':
                file=runtime.output/'default_scenario.json'
                return self.send(200,{'saved':file.is_file(),'path':str(file)})
            if path=='/api/leaderboard':
                file=runtime.output/'leaderboard.json'
                return self.send(200,json.loads(file.read_text()) if file.is_file() else [])
            if path=='/api/achievements':
                state=runtime.snapshot();return self.send(200,{'earned':state['achievements']})
            if path=='/api/presets':
                result=[]
                for file in sorted(set(runtime.presets.glob('*.json')) | set((runtime.output/'scenarios').glob('*.json'))):
                    try:cfg=Scenario.load(file);result.append({'id':file.stem,'name':cfg.name,'trajectory':cfg.target.trajectory,'atmosphere':cfg.disturbance.atmosphere,'seed':cfg.seed,'count':cfg.target.count})
                    except Exception:pass
                return self.send(200,result)
            if path in ('/api/frame','/frame','/api/raw-frame'):
                with runtime.lock:
                    frame=runtime.engine.last_raw if path=='/api/raw-frame' else runtime.engine.last_annotated
                    data=cv2.imencode('.jpg',frame,[cv2.IMWRITE_JPEG_QUALITY,83])[1].tobytes() if frame is not None else b''
                return self.send(200,data,'image/jpeg')
            if path=='/favicon.ico':return self.send(200,(Path(__file__).parent.parent.parent/'assets'/'icon.ico').read_bytes(),'image/x-icon')
            if path=='/api/qr.png':
                host=self.headers.get('Host','localhost:8000')
                if any(char not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.:-' for char in host):
                    return self.send(400,{'error':'Invalid dashboard host'})
                scheme='https' if host.endswith('.e2b.app') else 'http'
                try:return self.send(200,dashboard_qr_png(f'{scheme}://{host}/'),'image/png')
                except RuntimeError as exc:return self.send(503,{'error':str(exc)})
            if path=='/api/health':return self.send(200,{'ok':True})
            self.send(404,{'error':'Not found'})
        def do_POST(self):
            path=urlparse(self.path).path
            length=int(self.headers.get('Content-Length',0))
            if length>150_000_000:return self.send(413,{'error':'Upload too large (150 MB maximum).'})
            raw=self.rfile.read(length)
            try:
                if path=='/api/video':
                    upload=runtime.output/'uploads';upload.mkdir(parents=True,exist_ok=True)
                    suffix=self.headers.get('X-Extension','.mp4').lower()
                    if suffix not in ('.mp4','.mov','.avi'):raise ValueError('Supported video formats: MP4, MOV, AVI')
                    file=upload/('benchmark_'+str(int(time.time()))+suffix);file.write_bytes(raw)
                    with runtime.lock:
                        runtime.engine.open_video(str(file));runtime.last_export=None;runtime.running=True
                    return self.send(200,{'ok':True,'file':file.name})
                if length>1_000_000:raise ValueError('JSON request too large (1 MB maximum)')
                data=json.loads(raw or b'{}')
                if path in ('/api/control','/simulation/start','/simulation/stop'):
                    cmd=data.get('action','start' if path.endswith('start') else 'stop' if path.endswith('stop') else '')
                    with runtime.lock:
                        restarted=False
                        if cmd=='pause':runtime.running=False
                        elif cmd=='start':
                            if runtime.engine.source=='simulator' and runtime.engine.last is not None and runtime.engine.last['timestamp_s']>=runtime.engine.config.duration_s:
                                runtime.reset();restarted=True
                            elif runtime.engine.source=='video' and runtime.engine.video is not None and runtime.engine.video.get(cv2.CAP_PROP_POS_FRAMES)>=runtime.engine.video.get(cv2.CAP_PROP_FRAME_COUNT)>0:
                                runtime.engine.seek_video(0);runtime.last_export=None;runtime.running=True;restarted=True
                            else:runtime.running=True
                        elif cmd=='reset':runtime.reset()
                        elif cmd=='stop':runtime.running=False
                        elif cmd=='step':
                            runtime.running=False
                            if runtime.engine.source=='video':runtime.engine.step()
                        elif cmd=='seek':
                            runtime.engine.seek_video(int(data.get('frame',0)));runtime.last_export=None;runtime.running=False
                            runtime.engine.step()
                        elif cmd=='export':
                            if not runtime.engine.rows:raise ValueError('Process at least one frame before exporting evidence.')
                            runtime.last_export=export_session(runtime.engine,runtime.output)
                        elif cmd=='record_start':
                            filename='session_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.mp4'
                            runtime.engine.start_recording(runtime.output/'recordings'/filename)
                        elif cmd=='record_stop':runtime.engine.stop_recording()
                        elif cmd=='xray':runtime.engine.xray=not runtime.engine.xray
                        elif cmd=='manual':runtime.engine.manual=bool(data.get('enabled',False))
                        elif cmd=='autolock':runtime.engine.manual=False
                        elif cmd=='calibrate':
                            if runtime.engine.source!='simulator':raise ValueError('Calibration requires a simulator scene')
                            runtime.engine.sim.thermal_reference_c=runtime.engine.config.disturbance.temperature_c
                        elif cmd=='move':
                            limit=runtime.engine.config.camera.max_pan_speed
                            runtime.engine.command=tuple(max(-limit,min(limit,float(data.get(axis,0)))) for axis in ('pan','tilt'))
                        else:raise ValueError('Unknown action')
                        return self.send(200,{'ok':True,'running':runtime.running,'restarted':restarted,'export':runtime.last_export})
                if path=='/api/scenario':
                    slug=str(data.get('id',''))
                    if not slug.replace('_','').isalnum():raise ValueError('Invalid preset id')
                    file=runtime.presets/(slug+'.json')
                    if not file.is_file():file=runtime.output/'scenarios'/(slug+'.json')
                    runtime.reset(Scenario.load(file))
                    return self.send(200,{'ok':True})
                if path=='/api/config':
                    with runtime.lock:
                        obj=runtime.engine.config.to_dict()
                        for section,patch in data.items():
                            if section in ('world','target','camera','disturbance','link','control','tracking') and isinstance(patch,dict):obj[section].update(patch)
                            elif section in ('detector','controller','duration_s','name'):obj[section]=patch
                        scenario=Scenario.from_dict(obj)
                    runtime.reset(scenario);return self.send(200,{'ok':True})
                if path=='/api/scenario/save':
                    slug=str(data.get('id','')).lower()
                    if not 1<=len(slug)<=48 or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789_-' for c in slug):
                        raise ValueError('Scenario ID must contain 1–48 lowercase letters, digits, _ or -')
                    folder=runtime.output/'scenarios';folder.mkdir(parents=True,exist_ok=True)
                    with runtime.lock:cfg=Scenario.from_dict(runtime.engine.config.to_dict())
                    cfg.save(folder/(slug+'.json'));return self.send(200,{'ok':True,'id':slug})
                if path=='/api/scenario/import':
                    cfg=Scenario.from_dict(data)
                    runtime.reset(cfg);return self.send(200,{'ok':True,'scenario':cfg.name})
                if path=='/api/scenario/random':
                    seed=int(data.get('seed',secrets.randbelow(1_000_000)))
                    if not 0<=seed<=2**32-1:raise ValueError('Seed out of range')
                    with runtime.lock:cfg=perturb_scenario(runtime.engine.config,seed)
                    runtime.reset(cfg);return self.send(200,{'ok':True,'seed':seed,'scenario':cfg.name})
                if path=='/api/default/save':
                    runtime.output.mkdir(parents=True,exist_ok=True)
                    with runtime.lock:runtime.engine.config.save(runtime.output/'default_scenario.json')
                    return self.send(200,{'ok':True})
                if path=='/api/default/reset':
                    (runtime.output/'default_scenario.json').unlink(missing_ok=True)
                    runtime.reset(Scenario.load(runtime.presets/'easy_clear_circular.json'))
                    return self.send(200,{'ok':True})
                if path=='/api/network':
                    with runtime.lock:
                        if runtime.engine.source!='simulator':raise ValueError('Network world-plane proxy requires simulator mode')
                        target=runtime.engine.sim.positions[runtime.engine.designated_target] if runtime.engine.sim.positions else (runtime.engine.config.world.width/2,runtime.engine.config.world.height/2)
                        fov=[v/runtime.engine.config.camera.digital_zoom for v in runtime.engine.config.camera.resolution]
                        stations=data.get('stations',[[700,1000],[1000,1000],[1300,1000]])
                        return self.send(200,evaluate_network(target,stations,fov,data.get('previous')))
                if path=='/api/baseline':
                    with runtime.lock:cfg=Scenario.from_dict(runtime.engine.config.to_dict())
                    result=compare_to_static(cfg,int(data.get('frames',90)))
                    result['saved_to']=save_experiment(result,runtime.output,'baseline.json')
                    file=runtime.output/'leaderboard.json'
                    entries=json.loads(file.read_text()) if file.is_file() else []
                    entries.append({k:result[k] for k in ('scenario','seed','controlled_rmse_px','fixed_camera_rmse_px','improvement_pct')})
                    entries.sort(key=lambda x:x['controlled_rmse_px'] if x['controlled_rmse_px'] is not None else float('inf'))
                    file.parent.mkdir(parents=True,exist_ok=True);file.write_text(json.dumps(entries[:25],indent=2))
                    return self.send(200,result)
                if path=='/api/tle':
                    tle=str(data.get('tle',''))
                    if len(tle)>400:raise ValueError('TLE exceeds 400 characters')
                    when=datetime.datetime.fromisoformat(data.get('at_utc',datetime.datetime.now(timezone.utc).isoformat()))
                    return self.send(200,ground_station_look_angles(tle,when,float(data.get('lat',0)),float(data.get('lon',0)),float(data.get('alt_km',0))))
                if path=='/api/sensitivity':
                    section=str(data.get('section','disturbance'));parameter=str(data.get('parameter','noise_std'))
                    allowed={('disturbance','noise_std'),('target','speed_pps'),('camera','max_pan_speed'),('camera','digital_zoom')}
                    if (section,parameter) not in allowed:raise ValueError('Unsupported bounded sensitivity parameter')
                    values=data.get('values',[0,5,10,15,20]);frames=int(data.get('frames',60))
                    if not isinstance(values,list) or not 1<=len(values)<=8 or not 10<=frames<=240:raise ValueError('Sensitivity values/frames exceed bounds')
                    with runtime.lock:cfg=Scenario.from_dict(runtime.engine.config.to_dict())
                    result={'parameter':section+'.'+parameter,'values':sweep(cfg,section,parameter,values,frames)}
                    result['saved_to']=save_experiment(result,runtime.output,'sensitivity.json')
                    return self.send(200,result)
                if path=='/api/weakness':
                    trials=int(data.get('trials',6));frames=int(data.get('frames',60))
                    if not 2<=trials<=12 or not 10<=frames<=180:raise ValueError('Trials/frames exceed bounds')
                    with runtime.lock:cfg=Scenario.from_dict(runtime.engine.config.to_dict())
                    result={'weakness':search_weakness(cfg,frames,trials),'trials':trials,'frames':frames,
                            'note':'Bounded seeded hill-climb; not an ML adversary.'}
                    result['saved_to']=save_experiment(result,runtime.output,'weakness.json')
                    return self.send(200,result)
                if path in ('/api/compare','/api/stress','/api/validate'):
                    with runtime.lock:cfg=Scenario.from_dict(runtime.engine.config.to_dict())
                    if path=='/api/compare':result=compare_detectors(cfg)
                    elif path=='/api/stress':result=stress_suite(cfg)
                    else:result=signal_injection(float(data.get('offset_px',5)))
                    result['saved_to']=save_experiment(result,runtime.output,('comparison' if path.endswith('compare') else 'stress' if path.endswith('stress') else 'validation')+'.json')
                    return self.send(200,result)
                if path=='/api/ground-truth':
                    upload=runtime.output/'uploads';upload.mkdir(parents=True,exist_ok=True)
                    file=upload/'ground_truth.csv';file.write_text(data.get('csv',''),encoding='utf-8')
                    truth=load_ground_truth(file)
                    with runtime.lock:
                        if runtime.engine.source!='video':raise ValueError('Open a benchmark video before adding ground-truth labels')
                        runtime.engine.video_gt=truth;runtime.engine.seek_video(0);runtime.last_export=None;runtime.running=True
                    return self.send(200,{'ok':True,'rows':len(truth)})
                if path=='/target/change':
                    with runtime.lock:event=runtime.engine.designate_candidate(float(data['x']),float(data['y']))
                    return self.send(200,{'ok':True,'event':event})
                return self.send(404,{'error':'Not found'})
            except Exception as exc:return self.send(400,{'error':str(exc)})
    server=ThreadingHTTPServer((host,port),Handler)
    print(f'V-CAPAT control room: http://{host}:{port}',flush=True)
    try:server.serve_forever()
    finally:runtime.alive=False;runtime.engine.close();server.server_close()
