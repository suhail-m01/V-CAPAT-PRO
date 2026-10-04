"""One pipeline for desktop, browser and headless/video operation."""
import time
import cv2
import numpy as np
from ..simulation.camera import Simulator
from ..detection.arena import Detector
from .state_machine import Tracker
from ..control.pid import PID
from ..control.manual import ManualCommand
from ..security.spoof_detector import trust_score
from ..link.ber_model import bpsk_ber
from ..control.lead_angle import lead_angle_rad
from ..control.search import search_velocity
from ..link.link_quality import quality_percent
from ..tracking.handover import should_handover
from ..tracking.multi_target import image_candidate_at,truth_identity_for_evaluation
from .event_bus import EventBus
from ..plugins.loader import load_plugin,DetectorAdapter
from ..utils.geometry import pixels_to_degrees
from ..io.session_recorder import SessionRecorder
from ..io.video_source import VideoSource
from ..io.webcam_source import open_webcam

class Engine:
    def __init__(self,scenario):
        self.config=scenario.validate();self.source='simulator';self.sim=Simulator(scenario)
        self.detector=self._make_detector(scenario.detector);self.tracker=self._tracker()
        self.controller_plugin=self._make_controller(scenario.controller)
        speed=scenario.camera.max_pan_speed;t=scenario.control
        self.pan_pid=PID(t.kp,t.ki,t.kd,speed,t.deadband_deg);self.tilt_pid=PID(t.kp,t.ki,t.kd,speed,t.deadband_deg)
        self.frame_id=0;self.rows=[];self.last=None;self.manual=False;self.command=(0,0)
        self.search_pattern=scenario.control.search_pattern;self.events=[];self.bus=EventBus();self.started=time.monotonic();self.video=None;self.video_gt={}
        self.history=[];self.last_annotated=None;self.last_raw=None;self.lead_px=(0.,0.)
        self.designated_target=0;self.handover_events=[];self.xray=False
        self._last_camera_center=None
        self._previous_world_measurement=None;self._velocity_world=np.zeros(2,float)
        self.recorder=None;self.recording_path=None
        self.trust=0.;self.warning='';self.simulated_bytes=0.

    def _tracker(self):
        c=self.config.tracking
        return Tracker(c.hits_to_lock,c.coast_after,c.reacquire_after,c.process_noise,c.measurement_noise)

    @staticmethod
    def _make_detector(name):
        if name.startswith('plugin:'):
            kind,instance=load_plugin(name.split(':',1)[1])
            if kind!='detector':raise ValueError('Selected plugin is not a detector')
            return DetectorAdapter(name.split(':',1)[1],instance)
        return Detector(name)

    @staticmethod
    def _make_controller(name):
        if not name.startswith('plugin:'):return None
        kind,instance=load_plugin(name.split(':',1)[1])
        if kind!='controller':raise ValueError('Selected plugin is not a controller')
        return instance

    def change_detector(self,name):
        new=self._make_detector(name)
        self.detector=new;self.config.detector=name

    def open_video(self,path,ground_truth=None):
        if self.recorder:self.stop_recording()
        cap=VideoSource(path).cap
        if self.video:self.video.release()
        self.video=cap;self.source='video';self.frame_id=0;self.rows=[];self.tracker=self._tracker();self.detector=self._make_detector(self.config.detector)
        self.video_gt=ground_truth or {};self.video_fps=cap.get(cv2.CAP_PROP_FPS) or 30
        self.history=[];self.events=[];self.last=None;self.last_candidates=[];self.last_annotated=None

    def open_webcam(self,index=0):
        if self.recorder:self.stop_recording()
        cap=open_webcam(index)
        if self.video:self.video.release()
        self.video=cap;self.source='webcam';self.frame_id=0;self.rows=[];self.tracker=self._tracker();self.detector=self._make_detector(self.config.detector);self.video_gt={}
        self.video_fps=cap.get(cv2.CAP_PROP_FPS) or 30

    def designate_candidate(self,x,y):
        """Manual CV-candidate selection; ground truth is used for *evaluation* only.

        The Kalman hint is the image candidate position, never the simulator truth.
        """
        if self.source!='simulator' or not self.sim.last_truths:
            raise ValueError('Candidate designation requires an active simulator frame')
        if not hasattr(self,'last_candidates') or not self.last_candidates:
            raise ValueError('No CV candidate available at this frame')
        chosen=image_candidate_at(self.last_candidates,x,y)
        if chosen is None:raise ValueError('Click closer to a detected beacon candidate')
        target_id=self._identity_at(chosen['x'],chosen['y'])
        if target_id is None:raise ValueError('No labelled beacon matches this candidate')
        prior=self.designated_target;self.designated_target=target_id
        self.tracker=self._tracker();self.tracker.kalman.update(chosen['x'],chosen['y'])
        self.tracker.state='ACQUIRING';self.tracker.hits=1
        self.pan_pid.integral=self.tilt_pid.integral=0
        self.pan_pid.prev=self.tilt_pid.prev=None
        self._previous_world_measurement=None;self._velocity_world[:]=0
        event={'frame':self.frame_id,'time_s':self.last['timestamp_s'],'event':'MANUAL_DESIGNATION',
               'from_id':prior,'to_id':target_id,'candidate':[chosen['x'],chosen['y']]}
        self.events.append(event);self.bus.publish(event);self.handover_events.append(event)
        return event

    def _identity_at(self,x,y):
        """Post-hoc evaluator association; never an input to detection or control."""
        if self.source!='simulator':return None
        return truth_identity_for_evaluation(x,y,self.sim.last_truths,max(15,self.config.target.size_px*1.8))

    def seek_video(self,index):
        if self.video is None:raise ValueError('Open a video first')
        total=int(self.video.get(cv2.CAP_PROP_FRAME_COUNT))
        index=max(0,min(int(index),max(0,total-1)))
        self.video.set(cv2.CAP_PROP_POS_FRAMES,index)
        self.frame_id=index;self.rows=[];self.history=[];self.events=[];self.last=None
        self.tracker=self._tracker();self.detector=self._make_detector(self.config.detector)
        return index

    def start_recording(self,path):
        if self.recorder:raise RuntimeError('A recording is already active')
        size=(self.last_annotated.shape[1],self.last_annotated.shape[0]) if self.last_annotated is not None else tuple(self.config.camera.resolution)
        fps=self.video_fps if self.source!='simulator' else self.config.camera.update_hz
        self.recorder=SessionRecorder(path,fps,size)
        self.recording_path=None

    def stop_recording(self):
        if self.recorder:
            self.recorder.close();self.recording_path=self.recorder.path;self.recorder=None
        return self.recording_path

    def close(self):
        self.stop_recording()
        if self.video:self.video.release();self.video=None

    def step(self):
        start=time.perf_counter();c=self.config
        dt=1/(self.video_fps if self.source!='simulator' else c.camera.update_hz)
        if self.source=='simulator':
            self.frame_id+=1;t=self.frame_id*dt
            raw,truths=self.sim.frame(dt);w,h=c.camera.resolution
            camera_centre=(float(self.sim.cx),float(self.sim.cy))
            if self._last_camera_center is not None and self.tracker.kalman.state is not None:
                # Ego-motion compensation: prediction is in the current camera frame.
                # Motor encoders are known; target world truth remains inaccessible.
                self.tracker.kalman.state[:2]-=np.array(camera_centre)-np.array(self._last_camera_center)
            self._last_camera_center=camera_centre
            x,y,visible=truths[self.designated_target]
            gt=(x,y) if visible else None
        else:
            ok,raw=self.video.read()
            if not ok:return None
            self.frame_id+=1;t=self.frame_id*dt
            if raw.ndim==3:raw=cv2.cvtColor(raw,cv2.COLOR_BGR2GRAY)
            h,w=raw.shape[:2];data=self.video_gt.get(self.frame_id-1)
            gt=(float(data[0]),float(data[1])) if data and data[2] else None
            visible=bool(data[2]) if data else None
        pred=self.tracker.kalman.state[:2].copy() if self.tracker.kalman.state is not None else None
        # At initial multi-beacon acquisition, the scene prior is the viewport centre;
        # later, association uses ONLY the Kalman prediction, never simulator truth.
        if pred is None and self.source=='simulator' and c.target.count>1:pred=np.array([w/2,h/2])
        gate=(38 if self.tracker.state in ('LOCKED','ACQUIRING') and self.tracker.kalman.state is not None else 55 if self.tracker.state=='COASTING' else 100 if self.tracker.state=='REACQUIRING' else 100) if pred is not None else None
        # The old Kalman location is not a valid association prior after a long
        # outage. Search the image again rather than permanently rejecting an
        # in-frame beacon because it moved more than 100 px during the gap.
        if self.tracker.state=='REACQUIRING':
            detection=self.detector.detect(raw,None,None)
        else:
            detection=self.detector.detect(raw,pred,gate)
        prior=self.tracker.state;prediction=self.tracker.step(detection,t,dt)
        if (self.source=='simulator' and c.target.auto_handover and c.target.count>1
            and should_handover(prior,(detection.x,detection.y) if detection.found else None,pred,c.target.size_px)):
            # Select by CV only; truth maps the observed spot to an ID *after* selection.
            new_id=self._identity_at(detection.x,detection.y)
            if new_id is not None and new_id!=self.designated_target:
                event={'frame':self.frame_id,'time_s':round(t,3),'event':'AUTO_HANDOVER',
                       'from_id':self.designated_target,'to_id':new_id}
                self.designated_target=new_id;self.events.append(event);self.bus.publish(event);self.handover_events.append(event)
                self._previous_world_measurement=None;self._velocity_world[:]=0
                x,y,visible=truths[new_id];gt=(x,y) if visible else None
        if prior!=self.tracker.state:self._state_event({'frame':self.frame_id,'time_s':round(t,2),'event':self.tracker.state})
        fx=fy=None
        if self.tracker.kalman.state is not None:fx,fy=map(float,self.tracker.kalman.state[:2])
        self.lead_px=(0.,0.)
        if self.source=='simulator' and detection.found:
            # Camera-motion compensation in image space: measured spot + encoder pose.
            # Never use simulator target coordinates in the lead estimator.
            measurement=np.array([detection.x+self.sim.cx-w/2,detection.y+self.sim.cy-h/2])
            if self._previous_world_measurement is not None:
                delta=measurement-self._previous_world_measurement
                if np.linalg.norm(delta)<max(11,5*c.target.speed_pps*dt):
                    velocity=delta/dt
                    cap=max(1.,2*c.target.speed_pps)
                    velocity=np.clip(velocity,-cap,cap)
                    self._velocity_world=.82*self._velocity_world+.18*velocity
            self._previous_world_measurement=measurement
        if self.source=='simulator' and fx is not None and c.link.point_ahead:
            flight_time=lead_angle_rad(1.0,c.link.distance_km,c.link.round_trip)
            vector=np.clip(self._velocity_world*flight_time,[-w/3,-h/3],[w/3,h/3])
            self.lead_px=(float(vector[0]),float(vector[1]))
        if self.source=='simulator':
            if self.manual and c.control.assist_fraction<=0:u,v=self.command
            elif fx is not None and self.tracker.state not in ('REACQUIRING','SEARCHING'):
                aim_x=.85*detection.x+.15*fx if detection.found else fx
                aim_y=.85*detection.y+.15*fy if detection.found else fy
                error_x=pixels_to_degrees(aim_x+self.lead_px[0]-w/2,c.camera.fov_deg[0]/c.camera.digital_zoom,w)
                error_y=pixels_to_degrees(aim_y+self.lead_px[1]-h/2,c.camera.fov_deg[1]/c.camera.digital_zoom,h)
                if self.controller_plugin:
                    u,v=self.controller_plugin.step(error_x,error_y,dt,c.camera.max_pan_speed)
                else:
                    u=self.pan_pid.step(error_x,dt);v=self.tilt_pid.step(error_y,dt)
                if self.manual:
                    u,v=ManualCommand(*self.command,c.control.assist_fraction).blend(u,v,c.camera.max_pan_speed)
            elif self.manual:u,v=self.command
            elif self.tracker.state=='REACQUIRING':
                # Search about the last known position in camera coordinates.
                u,v=search_velocity(t,c.camera.max_pan_speed,self.search_pattern,c.seed)
            else:u=v=0
            self.sim.point(u,v,dt)
        centroid_error=float(np.hypot(detection.x-gt[0],detection.y-gt[1])) if gt and detection.found else None
        correct=(centroid_error<=max(15,c.target.size_px*1.8)) if centroid_error is not None else (None if visible is None else False)
        pointing_error=float(np.hypot(gt[0]-w/2,gt[1]-h/2)) if gt else None
        proc=(time.perf_counter()-start)*1000
        link=quality_percent(pointing_error,detection.confidence,c.disturbance.atmosphere)
        row={'frame_id':self.frame_id,'timestamp_s':round(t,4),'source_mode':self.source,
             'gt_x':round(gt[0],3) if gt else None,'gt_y':round(gt[1],3) if gt else None,
             'detected_x':round(detection.x,3) if detection.found else None,'detected_y':round(detection.y,3) if detection.found else None,
             'filtered_x':round(fx,3) if fx is not None else None,'filtered_y':round(fy,3) if fy is not None else None,
             'detection_confidence':round(detection.confidence,4),'target_visible':visible,'detected':detection.found,
             'lock_state':self.tracker.state,'designated_id':self.designated_target if self.source=='simulator' else None,
             'correct_target':correct,'centroid_error_px':round(centroid_error,3) if centroid_error is not None else None,
             'pointing_error_px':round(pointing_error,3) if pointing_error is not None else None,
             'pan_deg':round(self.sim.pan,5) if self.source=='simulator' else None,
             'tilt_deg':round(self.sim.tilt,5) if self.source=='simulator' else None,
             'pan_velocity_deg_s':round(self.sim.pan_velocity,4) if self.source=='simulator' else None,
             'tilt_velocity_deg_s':round(self.sim.tilt_velocity,4) if self.source=='simulator' else None,
             'processing_time_ms':round(proc,3),'instantaneous_fps':round(1000/max(proc,.01),2),
             'noise_mode':'+'.join(c.disturbance.noise_types) or 'none','atmosphere_mode':c.disturbance.atmosphere,
             'link_quality':round(link,2),'lead_x_px':round(self.lead_px[0],4),
             'lead_y_px':round(self.lead_px[1],4),'lead_distance_km':c.link.distance_km if c.link.point_ahead else None}
        selected=min(detection.candidates,key=lambda item:(item['x']-detection.x)**2+(item['y']-detection.y)**2) if detection.found and detection.candidates else None
        self.trust=trust_score(selected,pred,c.target.brightness if self.source=='simulator' else None) if selected else 0.
        self.warning='UNVERIFIED CANDIDATE' if detection.found and self.trust<.25 else ''
        self.simulated_bytes+=5e9/8*dt*link/100 if self.source=='simulator' else 0
        self.rows.append(row);self.history.append({'t':t,'error':pointing_error,'centroid':centroid_error,'fps':row['instantaneous_fps'],'link':link,'pan':row['pan_deg'],'tilt':row['tilt_deg']})
        if len(self.history)>600:self.history.pop(0)
        self.last=row;self.last_candidates=detection.candidates;self.last_raw=raw.copy()
        self.last_annotated=self.annotate(raw,detection,pred,row)
        if self.recorder:self.recorder.append(self.last_annotated)
        return row

    @staticmethod
    def _link(error,confidence,atmosphere):
        if error is None: return float(confidence*75)
        return quality_percent(error,confidence,atmosphere)

    def annotate(self,raw,d,pred,row):
        im=cv2.cvtColor(raw,cv2.COLOR_GRAY2BGR) if raw.ndim==2 else raw.copy();h,w=im.shape[:2]
        cyan=(244,215,65); green=(133,233,91)
        cv2.line(im,(w//2-16,h//2),(w//2+16,h//2),cyan,1,cv2.LINE_AA)
        cv2.line(im,(w//2,h//2-16),(w//2,h//2+16),cyan,1,cv2.LINE_AA)
        cv2.circle(im,(w//2,h//2),34,cyan,1,cv2.LINE_AA)
        if pred is not None:cv2.circle(im,tuple(np.int32(pred)),9,(255,172,79),1,cv2.LINE_AA)
        if self.xray:
            for i,candidate in enumerate(d.candidates[:8]):
                x,y,bw,bh=candidate['bbox']
                cv2.rectangle(im,(x,y),(x+bw,y+bh),(75,197,245),1,cv2.LINE_AA)
                cv2.putText(im,f"{i+1} {candidate['score']:.2f}",(x,max(37,y-5)),cv2.FONT_HERSHEY_SIMPLEX,.37,(75,197,245),1,cv2.LINE_AA)
            if d.debug is not None:
                inset=cv2.resize(d.debug,(130,96),interpolation=cv2.INTER_NEAREST)
                ix=w-145;im[34:130,ix:ix+130]=cv2.cvtColor(inset,cv2.COLOR_GRAY2BGR)
                cv2.putText(im,'BINARY / X-RAY',(ix,145),cv2.FONT_HERSHEY_SIMPLEX,.36,(75,197,245),1,cv2.LINE_AA)
            if self.tracker.kalman.state is not None:
                cov=self.tracker.kalman.P[:2,:2]
                eig,vec=np.linalg.eigh(cov);axes=tuple(max(3,int(2*np.sqrt(max(0,v)))) for v in eig[::-1])
                angle=float(np.degrees(np.arctan2(vec[1,1],vec[0,1])))
                cv2.ellipse(im,(int(self.tracker.kalman.state[0]),int(self.tracker.kalman.state[1])),axes,angle,0,360,(255,172,79),1,cv2.LINE_AA)
        if d.found:
            x,y,bw,bh=d.bbox;cv2.rectangle(im,(x,y),(x+bw,y+bh),green,1,cv2.LINE_AA)
            cv2.circle(im,(int(d.x),int(d.y)),3,(76,100,255),-1,cv2.LINE_AA)
            cv2.line(im,(w//2,h//2),(int(d.x),int(d.y)),green,1,cv2.LINE_AA)
        if self.config.link.point_ahead and self.source=='simulator' and d.found:
            lead=(int(round(d.x+self.lead_px[0])),int(round(d.y+self.lead_px[1])))
            cv2.arrowedLine(im,(int(d.x),int(d.y)),lead,(102,184,255),1,cv2.LINE_AA,tipLength=.25)
            cv2.circle(im,lead,6,(102,184,255),1,cv2.LINE_AA)
            cv2.putText(im,'LEAD', (max(0,lead[0]+8),max(12,lead[1]-8)),cv2.FONT_HERSHEY_SIMPLEX,.34,(102,184,255),1,cv2.LINE_AA)
        cv2.rectangle(im,(0,0),(w-1,h-1),(92,76,37),1)
        cv2.putText(im,'VC / OPTICAL ACQUISITION', (17,25),cv2.FONT_HERSHEY_SIMPLEX,.49,(193,179,136),1,cv2.LINE_AA)
        cv2.putText(im,'TARGET '+str(self.designated_target+1)+'  /  '+self.tracker.state,(17,h-19),cv2.FONT_HERSHEY_SIMPLEX,.45,green if self.tracker.state=='LOCKED' else (114,190,255),1,cv2.LINE_AA)
        cv2.putText(im,f'{self.frame_id:06d}  /  {row["timestamp_s"]:06.2f} S',(w-178,h-19),cv2.FONT_HERSHEY_SIMPLEX,.44,(193,179,136),1,cv2.LINE_AA)
        return im

    def _state_event(self,event):
        self.events.append(event);self.bus.publish(event)

    def snapshot(self):
        r=self.last or {};total=len(self.rows)
        return {'status':self.tracker.state,'confidence':round(self.tracker.confidence*100,1),
                'frame':self.frame_id,'elapsed':r.get('timestamp_s',0),'fps':round(1000/max(r.get('processing_time_ms',1),.01),1),
                'processing_ms':r.get('processing_time_ms',0),'pointing_error':r.get('pointing_error_px'),
                'centroid_error':r.get('centroid_error_px'),'pan':r.get('pan_deg'),'tilt':r.get('tilt_deg'),
                'link':r.get('link_quality',0),'lead_px':list(self.lead_px),
                'lead_deg':[round(self.lead_px[0]*self.config.camera.fov_deg[0]/self.config.camera.resolution[0]/self.config.camera.digital_zoom,5),round(self.lead_px[1]*self.config.camera.fov_deg[1]/self.config.camera.resolution[1]/self.config.camera.digital_zoom,5)],
                'lead_distance_km':self.config.link.distance_km,'lead_enabled':self.config.link.point_ahead,
                'throughput_gbps':round(5*r.get('link_quality',0)/100,2),
                'lock_retention':(round(100*sum(x['lock_state']=='LOCKED' and x['correct_target'] is True and x['target_visible'] is True for x in self.rows)/sum(x['target_visible'] is True for x in self.rows),1)
                                   if any(x['target_visible'] is True for x in self.rows) else None),
                'acquisition':self.tracker.first_lock,'losses':self.tracker.losses,
                'designated_id':self.designated_target,'handover_count':len(self.handover_events),'xray':self.xray,
                'audit_warning':('FALSE LOCK / candidate is not designated beacon' if self.source=='simulator' and r.get('target_visible') is True and r.get('correct_target') is False and self.tracker.state=='LOCKED' else ''),
                'recording':self.recorder is not None,'manual':self.manual,'assist_fraction':self.config.control.assist_fraction,
                'search_pattern':self.search_pattern,'trust':round(self.trust,3),'warning':self.warning,
                'ber_proxy':round(bpsk_ber(max(0,r.get('link_quality',0)/100*10)),8),
                'bytes_proxy':round(self.simulated_bytes),'mode':self.source,'video_total':int(self.video.get(cv2.CAP_PROP_FRAME_COUNT)) if self.video is not None and self.source=='video' else None,
                'scenario':self.config.name,'detector':self.config.detector,'controller':self.config.controller,'candidates':self.detector.mode and (self.last_candidates if hasattr(self,'last_candidates') else []),
                'target':list(self.sim.positions[self.designated_target]) if self.sim.positions else None,'targets':[list(pos) for pos in self.sim.positions],'camera':[float(self.sim.cx),float(self.sim.cy)],
                'world':[self.config.world.width,self.config.world.height],'fov_pixels':self.config.camera.resolution,
                'world_fov_pixels':[v/self.config.camera.digital_zoom for v in self.config.camera.resolution],
                'history':self.history[-100:],'events':self.events[-15:]}
