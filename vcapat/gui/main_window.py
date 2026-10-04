"""PySide6 desktop mission control. Import only when desktop mode is selected."""
from pathlib import Path
import numpy as np
import cv2
import datetime
from PySide6.QtCore import Qt,QTimer,QPointF,Signal
from PySide6.QtGui import QImage,QPixmap,QPainter,QPen,QColor,QFont,QIcon
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QComboBox,QGroupBox,QFileDialog,QMessageBox,QDialog,QTabWidget,QFormLayout,QSpinBox,QDoubleSpinBox,QCheckBox,QScrollArea,QFrame,QSplashScreen,QInputDialog,QStackedWidget)
from ..config.settings import Scenario
from ..core.engine import Engine
from ..metrics.reporter import export_session
from ..io.ground_truth import load_ground_truth
from ..metrics.collector import summarize
from ..metrics.compliance import compliance

from .theme import STYLE
from .viewport_widget import CameraLabel
from .plots_panel import Plot
from .minimap_widget import Map
from .settings_dialog import Settings
from .xray_overlay import XRayOverlay
from .metrics_panel import MetricsPanel
from .multi_algo_widget import MultiAlgoWidget
from .stress_test_widget import StressTestWidget
from .sensitivity_widget import SensitivityWidget
from .achievements import Achievements
from .tutorial import Tutorial
from .replay_widget import ReplayWidget
from .judge_demo import JudgeDemo
from .compliance_widget import ComplianceWidget
from .link_quality_widget import LinkQualityWidget
from .feature_audit_widget import FeatureAudit

class Window(QMainWindow):
    def __init__(self,engine,presets,output):
        super().__init__();self.engine=engine;self.presets=Path(presets);self.output=output;self.running=True
        self._tools=[]
        self.setWindowTitle('V-CAPAT PRO · Optical Acquisition Laboratory');self.setWindowIcon(QIcon(str(Path(__file__).resolve().parent.parent.parent/'assets'/'icon.ico')));self.resize(1370,900);self.setMinimumSize(970,700)
        scroll=QScrollArea();scroll.setWidgetResizable(True);scroll.setFrameShape(QFrame.NoFrame)
        page=QWidget();scroll.setWidget(page);layout=QVBoxLayout(page);layout.setContentsMargins(22,20,22,20);layout.setSpacing(13)
        top=QHBoxLayout();heading=QVBoxLayout();eyebrow=QLabel('OPTICAL TRACKING  /  MISSION CONTROL');eyebrow.setObjectName('eyebrow');heading.addWidget(eyebrow);title=QLabel('V-CAPAT  PRO');title.setObjectName('heading');heading.addWidget(title);heading.addWidget(QLabel('Virtual Camera Acquisition, Pointing & Tracking System'));top.addLayout(heading);top.addStretch();badge=QLabel('●  LIVE COARSE ALIGNMENT LAB');badge.setStyleSheet('background:#16322f;color:#7deac9;padding:12px;border:1px solid #366257;border-radius:9px;font-weight:bold');top.addWidget(badge);layout.addLayout(top)
        toolbar=QHBoxLayout();toolbar.addWidget(QLabel('SCENARIO'));self.scenarios=QComboBox()
        for file in sorted(self.presets.glob('*.json')):
            try:self.scenarios.addItem(Scenario.load(file).name,str(file))
            except Exception:pass
        self.scenarios.setCurrentText(engine.config.name);self.scenarios.currentIndexChanged.connect(self.change_scenario);toolbar.addWidget(self.scenarios,3)
        toolbar.addWidget(QLabel('DETECTOR'));self.detectors=QComboBox();self.detectors.addItems(['ai_auto','tinyml','adaptive','top_hat','template','optical_flow','auto','plugin:example_detector_plugin']);self.detectors.setCurrentText(engine.config.detector);self.detectors.currentTextChanged.connect(self.change_detector);toolbar.addWidget(self.detectors,1)
        toolbar.addWidget(QLabel('CONTROLLER'));self.controllers=QComboBox();self.controllers.addItems(['pid','plugin:example_controller_plugin']);self.controllers.setCurrentText(engine.config.controller);self.controllers.currentTextChanged.connect(self.change_controller);toolbar.addWidget(self.controllers,1)
        settings=QPushButton('⚙  Settings');settings.clicked.connect(self.settings);toolbar.addWidget(settings);layout.addLayout(toolbar)
        main=QGridLayout();main.setHorizontalSpacing(14);main.setVerticalSpacing(12);layout.addLayout(main)
        viewport=QGroupBox('01 / LIVE CAMERA VIEWPORT');v=QVBoxLayout(viewport);self.image=CameraLabel('Camera initialising…');self.image.selected.connect(self.designate_at);self.image.setAlignment(Qt.AlignCenter);self.image.setMinimumSize(560,360);self.image.setStyleSheet('background:#030a11;border-radius:8px');v.addWidget(self.image,1);self.source=QLabel('FPA  640 × 480     /     SIMULATOR     /     FOV  4.0° × 3.0°');self.source.setObjectName('muted');v.addWidget(self.source);main.addWidget(viewport,0,0,3,1)
        state=QGroupBox('02 / TRACKING STATE');sl=QVBoxLayout(state);self.status=QLabel('SEARCHING');self.status.setObjectName('large');sl.addWidget(self.status);self.substatus=QLabel('Waiting for beacon acquisition');self.substatus.setObjectName('muted');sl.addWidget(self.substatus);main.addWidget(state,0,1)
        telemetry=QGroupBox('03 / FLIGHT TELEMETRY');grid=QGridLayout(telemetry);self.metrics={}
        for i,(key,label) in enumerate([('fps','PIPELINE FPS'),('processing','PROCESSING MS'),('error','POINTING ERROR'),('centroid','CENTROID ERROR'),('pan','PAN / TILT'),('retention','LOCK RETENTION')]):
            cell=QVBoxLayout();small=QLabel(label);small.setObjectName('muted');value=QLabel('—');value.setObjectName('large');cell.addWidget(small);cell.addWidget(value);grid.addLayout(cell,i//2,i%2);self.metrics[key]=value
        main.addWidget(telemetry,1,1)
        link=QGroupBox('04 / OPTICAL LINK · MODELLED');ll=QVBoxLayout(link);self.link=QLabel('— %    /    — Gbps');self.link.setObjectName('large');ll.addWidget(self.link);main.addWidget(link,2,1)
        plotbox=QGroupBox('05 / POINTING ERROR OVER TIME');pl=QVBoxLayout(plotbox);self.plot=Plot(self.engine);pl.addWidget(self.plot);main.addWidget(plotbox,3,0)
        mapbox=QGroupBox('06 / WORLD OVERVIEW');ml=QVBoxLayout(mapbox);self.map=Map(self.engine);ml.addWidget(self.map);main.addWidget(mapbox,3,1)
        main.setColumnStretch(0,7);main.setColumnStretch(1,4)
        buttons=QHBoxLayout();self.play=QPushButton('Ⅱ  Pause');self.play.setObjectName('primary');self.play.clicked.connect(self.toggle);buttons.addWidget(self.play)
        for label,callback in [('◈  X-Ray',self.toggle_xray),('↺  Reset',self.reset),('▤  Open video',self.open_video),('◉  Webcam',self.open_webcam),('◎  Load truth CSV',self.open_truth),('⇩  Export report',self.export),('⦿  Record MP4',self.record),('◫  Screenshot',self.screenshot)]:
            b=QPushButton(label);b.clicked.connect(callback);buttons.addWidget(b)
        buttons.addStretch();layout.addLayout(buttons)
        self.checks=QLabel('SPEC CHECKS  /  collecting evidence…');self.checks.setStyleSheet('color:#a6bac8;padding:13px;background:#112332;border:1px solid #263d4c;border-radius:9px');layout.addWidget(self.checks)
        note=QLabel('METROLOGY NOTE  •  Ground-truth accuracy is unavailable for external footage until a matching CSV is loaded. Processing FPS is independent of source playback rate.');note.setWordWrap(True);note.setObjectName('muted');layout.addWidget(note)
        file_menu=self.menuBar().addMenu('File')
        file_menu.addAction('Save scenario JSON',self.desktop_save_scenario)
        file_menu.addAction('Load scenario JSON',self.desktop_import_scenario)
        file_menu.addAction('Generate seeded random scenario',self.desktop_random_scenario)
        file_menu.addAction('Save current settings as startup default',self.desktop_default)
        file_menu.addAction('Restore factory settings',self.desktop_factory)
        file_menu.addAction('Open report directory',self.desktop_open_reports)
        help_menu=self.menuBar().addMenu('Help')
        help_menu.addAction('FSOC tutorial',lambda:self.show_tool('tutorial'))
        help_menu.addAction('About & limitations',self.desktop_about)
        help_menu.addAction('55-feature audit',lambda:self.show_tool('features'))
        tools_menu=self.menuBar().addMenu('Tools')
        for title,kind in [('X-Ray explanation','xray'),('Detector arena','arena'),('Stress matrix','stress'),('Sensitivity analysis','sensitivity'),('Achievements','achievements'),('Tutorial','tutorial'),('Replay MP4','replay'),('Guided demo','demo'),('Compliance checks','compliance'),('Link proxy','link'),('Telemetry table','metrics')]:
            tools_menu.addAction(title,lambda checked=False,k=kind:self.show_tool(k))
        self.build_pages(scroll)
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(max(1,round(1000/self.engine.config.camera.update_hz)));self.setFocusPolicy(Qt.StrongFocus)
    def build_pages(self,live_scroll):
        """Purpose-built desktop pages; the same Engine instance survives navigation."""
        root=QWidget();outer=QHBoxLayout(root);outer.setContentsMargins(0,0,0,0);outer.setSpacing(0)
        rail=QWidget();rail.setFixedWidth(212);rail.setStyleSheet('background:#0c1c2a;border-right:1px solid #294455')
        nav=QVBoxLayout(rail);nav.setContentsMargins(13,22,13,19);nav.setSpacing(7)
        mark=QLabel('◈  V-CAPAT  PRO');mark.setStyleSheet('font-size:15px;font-weight:900;color:#79e4c1;padding:12px 5px');nav.addWidget(mark)
        sub=QLabel('OPTICAL ACQUISITION LAB');sub.setObjectName('muted');nav.addWidget(sub)
        nav.addSpacing(25);nav.addWidget(QLabel('MISSION WORKSPACE'))
        self.pages=QStackedWidget();self.nav_buttons=[]
        pages=[self._overview_page(),live_scroll,self._scenarios_page(),self._benchmark_page(),self._analysis_page(),self._engineering_page()]
        names=['Overview','Live tracking','Scenarios','Video benchmark','Analysis & reports','Algorithm lab']
        for i,(name,p) in enumerate(zip(names,pages)):
            b=QPushButton(('◈','◎','▦','▤','▥','⌬')[i]+'   '+name.replace('&','&&'))
            b.setStyleSheet('text-align:left;padding:13px 11px')
            b.clicked.connect(lambda checked=False,index=i:self.navigate(index))
            nav.addWidget(b);self.nav_buttons.append(b);self.pages.addWidget(p)
        nav.addStretch();caution=QLabel('LOCAL ENGINE ACTIVE\nSoftware prototype · not flight-certified')
        caution.setWordWrap(True);caution.setObjectName('muted');nav.addWidget(caution)
        outer.addWidget(rail);outer.addWidget(self.pages,1);self.setCentralWidget(root);self.navigate(0)

    def navigate(self,index):
        self.pages.setCurrentIndex(index)
        for i,b in enumerate(self.nav_buttons):
            b.setStyleSheet('text-align:left;padding:13px 11px;'+('background:#174038;color:#80ebc5;border:1px solid #407460' if i==index else ''))
        self.setWindowTitle(['Overview','Live tracking','Scenarios','Video benchmark','Analysis & reports','Algorithm lab'][index]+' · V-CAPAT PRO')

    def _page(self,eyebrow,title,intro):
        area=QScrollArea();area.setWidgetResizable(True);area.setFrameShape(QFrame.NoFrame)
        body=QWidget();area.setWidget(body);layout=QVBoxLayout(body);layout.setContentsMargins(29,24,29,30);layout.setSpacing(17)
        top=QLabel(eyebrow);top.setObjectName('eyebrow');layout.addWidget(top)
        h=QLabel(title);h.setObjectName('heading');layout.addWidget(h)
        p=QLabel(intro);p.setObjectName('muted');p.setWordWrap(True);layout.addWidget(p)
        return area,layout

    def _overview_page(self):
        page,lay=self._page('MISSION OVERVIEW / ACTIVE SESSION','Optical acquisition, under control.',
            'A reproducible laboratory for finding and following a moving FSOC beacon with a virtual pan–tilt focal-plane camera.')
        group=QGroupBox('01 / STATION STATUS');grid=QGridLayout(group);self.overview_values={}
        for i,(k,label) in enumerate([('state','TRACK STATE'),('error','POINTING ERROR'),('fps','PIPELINE FPS'),('scenario','SCENARIO')]):
            caption=QLabel(label);caption.setObjectName('muted');value=QLabel('—');value.setObjectName('large')
            grid.addWidget(caption,i//2*2,i%2);grid.addWidget(value,i//2*2+1,i%2);self.overview_values[k]=value
        lay.addWidget(group)
        flow=QGroupBox('02 / ALIGNMENT CHAIN');v=QVBoxLayout(flow)
        for heading,info in [('01  Observe','Virtual world, local webcam or prerecorded benchmark footage.'),
                             ('02  Identify','CV candidate scoring and subpixel centroiding.'),
                             ('03  Predict','Kalman prediction holds a track through short gaps.'),
                             ('04  Correct','Speed-limited pan–tilt PID recenters the optical spot.')]:
            label=QLabel(heading+'    /    '+info);label.setWordWrap(True);v.addWidget(label)
        lay.addWidget(flow)
        self.overview_checks=QLabel('Awaiting evidence');self.overview_checks.setWordWrap(True);lay.addWidget(self.overview_checks)
        row=QHBoxLayout()
        for name,index in [('Open live tracking  ↗',1),('Design a scenario  ↗',2),('Review evidence  ↗',4)]:
            b=QPushButton(name);b.clicked.connect(lambda checked=False,i=index:self.navigate(i));row.addWidget(b)
        row.addStretch();lay.addLayout(row);lay.addStretch();return page

    def _scenarios_page(self):
        page,lay=self._page('TEST DESIGN / DETERMINISTIC EXPERIMENTS','Scenario library',
            'Select a fixed-seed acquisition environment. Loading a preset resets the run for reproducible comparisons.')
        group=QGroupBox('01 / THIRTEEN PRESET MISSIONS');v=QVBoxLayout(group)
        self.desktop_preset=QComboBox()
        for file in sorted(self.presets.glob('*.json')):
            try:self.desktop_preset.addItem(Scenario.load(file).name,str(file))
            except Exception:pass
        v.addWidget(self.desktop_preset)
        b=QPushButton('Load selected scenario  ↗');b.setObjectName('primary');b.clicked.connect(self.desktop_load_preset);v.addWidget(b);lay.addWidget(group)
        setting=QGroupBox('02 / CONTROLLED CONDITIONS');v=QVBoxLayout(setting)
        info=QLabel('Change trajectory, disturbance, camera FOV, noise, speed, detector and point-ahead in the tabbed settings dialog. Applying settings restarts the run.');info.setWordWrap(True);v.addWidget(info)
        b=QPushButton('Open scenario settings');b.clicked.connect(self.settings);v.addWidget(b);lay.addWidget(setting)
        note=QLabel('LEO and aircraft labels are visual motion presets, not live ephemerides or aeronautics feeds. Failure under extreme conditions remains a recorded failure.');note.setObjectName('muted');note.setWordWrap(True);lay.addWidget(note);lay.addStretch();return page

    def desktop_load_preset(self):
        path=self.desktop_preset.currentData()
        if path:self.replace(Scenario.load(path));self.navigate(1)

    def _benchmark_page(self):
        page,lay=self._page('EXTERNAL EVIDENCE / PRERECORDED FOOTAGE','Video benchmark',
            'External footage goes through the same detector and tracker, with camera actuation bypassed. Matching ground truth enables centroid RMSE.')
        group=QGroupBox('01 / LOAD INPUT DATA');v=QVBoxLayout(group)
        row=QHBoxLayout()
        for text,slot in [('Open MP4 / AVI / MOV',self.open_video),('Load truth CSV',self.open_truth)]:
            b=QPushButton(text);b.clicked.connect(slot);row.addWidget(b)
        row.addStretch();v.addLayout(row)
        self.benchmark_info=QLabel('Source / simulator');self.benchmark_info.setObjectName('muted');v.addWidget(self.benchmark_info);lay.addWidget(group)
        group=QGroupBox('02 / VIDEO TRANSPORT');row=QHBoxLayout(group)
        self.benchmark_seek=QSpinBox();self.benchmark_seek.setRange(0,0);row.addWidget(QLabel('Frame index'));row.addWidget(self.benchmark_seek)
        b=QPushButton('Seek / reset segment');b.clicked.connect(self.desktop_seek);row.addWidget(b)
        b=QPushButton('Step one frame');b.clicked.connect(self.desktop_step);row.addWidget(b);row.addStretch();lay.addWidget(group)
        self.benchmark_metrics=QLabel('Centroid accuracy / N/A until labelled video is processed');self.benchmark_metrics.setWordWrap(True);lay.addWidget(self.benchmark_metrics)
        note=QLabel('CSV header: frame,timestamp_s,gt_x,gt_y,visible. Frames are indexed from zero. Seeking clears metrics for the preceding segment.');note.setObjectName('muted');note.setWordWrap(True);lay.addWidget(note)
        b=QPushButton('Inspect live annotated feed  ↗');b.clicked.connect(lambda:self.navigate(1));lay.addWidget(b);lay.addStretch();return page

    def desktop_seek(self):
        try:self.engine.seek_video(self.benchmark_seek.value());self.running=False;self.engine.step();self.tick()
        except Exception as exc:QMessageBox.warning(self,'Seek video',str(exc))

    def desktop_step(self):
        try:
            if self.engine.source!='video':raise ValueError('Open a benchmark video first')
            self.running=False;self.engine.step();self.tick()
        except Exception as exc:QMessageBox.warning(self,'Step frame',str(exc))

    def _analysis_page(self):
        page,lay=self._page('EVIDENCE / RUN VALIDATION','Analysis & reports',
            'Review measured requirements and export a frozen CSV, JSON, PNG, PDF and SQLite evidence bundle. N/A is not a pass.')
        group=QGroupBox('01 / RUN MEASUREMENTS');v=QVBoxLayout(group)
        self.analysis_metrics=QLabel('Collecting evidence…');self.analysis_metrics.setWordWrap(True);v.addWidget(self.analysis_metrics);lay.addWidget(group)
        group=QGroupBox('02 / REQUIREMENT CHECKS');v=QVBoxLayout(group)
        self.analysis_checks=QLabel('Awaiting first frame…');self.analysis_checks.setWordWrap(True);v.addWidget(self.analysis_checks);lay.addWidget(group)
        row=QHBoxLayout()
        for text,slot in [('Export evidence',self.export),('Compare detectors',lambda:self.show_tool('arena')),
                          ('Stress matrix',lambda:self.show_tool('stress'))]:
            b=QPushButton(text);b.clicked.connect(slot);row.addWidget(b)
        row.addStretch();lay.addLayout(row)
        note=QLabel('The generated certificate.pdf is experimental software evidence, not an official ISRO qualification certificate.');note.setObjectName('muted');note.setWordWrap(True);lay.addWidget(note);lay.addStretch();return page

    def _engineering_page(self):
        page,lay=self._page('ENGINEERING / EXPLAINABLE TRACKING','Algorithm lab',
            'Inspect the image-to-motor pipeline and candidate explanations without changing the shared acquisition run.')
        group=QGroupBox('01 / IMAGE-TO-MOTOR PIPELINE');v=QVBoxLayout(group)
        for msg in ('Image acquisition → ROI and camera disturbances', 'CV detection → candidate intensity, geometry and prediction score',
                    'Subpixel centroid → constant-velocity Kalman association', 'Lock-state transitions → pan/tilt PID feedback'):
            v.addWidget(QLabel(msg))
        lay.addWidget(group)
        group=QGroupBox('02 / LIVE CANDIDATES');v=QVBoxLayout(group)
        self.engineering_candidates=QLabel('Awaiting candidate detections…');self.engineering_candidates.setWordWrap(True)
        v.addWidget(self.engineering_candidates);lay.addWidget(group)
        row=QHBoxLayout()
        for text,slot in [('Toggle X-Ray',self.toggle_xray),('X-Ray detail',lambda:self.show_tool('xray')),
                          ('Open camera feed',lambda:self.navigate(1))]:
            b=QPushButton(text);b.clicked.connect(slot);row.addWidget(b)
        row.addStretch();lay.addLayout(row)
        note=QLabel('The turbulence warp and optical link quality are proxies. No trained YOLO weights or RL controller are bundled.');note.setObjectName('muted');note.setWordWrap(True);lay.addWidget(note);lay.addStretch();return page

    def update_pages(self,s,summary,checks):
        fmt=lambda v,unit='': 'N/A' if v is None else f'{v:.1f}{unit}'
        for key,value in [('state',s['status']),('error',fmt(s['pointing_error'],' px')),
                          ('fps',fmt(s['fps'],' FPS')),('scenario',s['scenario'])]:self.overview_values[key].setText(value)
        text='    ·    '.join(c['label']+': '+c['status'] for c in checks.values())
        self.overview_checks.setText('REQUIREMENT STATUS  /  '+text)
        self.analysis_checks.setText('\n'.join(c['label']+'  /  '+c['status']+'  /  '+fmt(c['value']) for c in checks.values()))
        error=summary.get('pointing_rmse_px') if s['mode']=='simulator' else summary.get('centroid_rmse_px')
        self.analysis_metrics.setText('Acquisition: '+fmt(summary.get('acquisition_s'),' s')+'     ·     Tracking RMSE: '+fmt(error,' px')+
            '\nTarget loss: '+fmt(summary.get('target_loss_pct'),' %')+'     ·     Processing: '+fmt(summary.get('average_processing_fps'),' FPS'))
        self.benchmark_info.setText('Source: '+s['mode'].upper()+'     ·     Frame '+str(s['frame'])+' / '+str(s['video_total'] or '—'))
        self.benchmark_metrics.setText('Centroid RMSE: '+fmt(summary.get('centroid_rmse_px'),' px')+
            '     ·     Lock retention: '+fmt(summary.get('lock_retention_pct'),' %'))
        if s['mode']=='video':self.benchmark_seek.setMaximum(max(0,(s['video_total'] or 1)-1))
        if not self.benchmark_seek.hasFocus():self.benchmark_seek.setValue(min(s['frame'],self.benchmark_seek.maximum()))
        candidates=s['candidates'] or []
        self.engineering_candidates.setText('Detector: '+s['detector'].upper()+'     ·     X-Ray: '+('ON' if s['xray'] else 'OFF')+
            '\n'+('\n'.join(f"#{i+1}  x={c['x']:.1f}  y={c['y']:.1f}  score={c['score']:.2f}  penalty={c['contributions']['prediction_penalty']:.2f}" for i,c in enumerate(candidates[:8])) if candidates else 'No image candidates in the current frame.'))

    def desktop_save_scenario(self):
        path,_=QFileDialog.getSaveFileName(self,'Save acquisition scenario','scenario.json','Scenario JSON (*.json)')
        if path:
            try:self.engine.config.save(path);self.statusBar().showMessage('Saved: '+path,7000)
            except Exception as exc:QMessageBox.warning(self,'Scenario save error',str(exc))

    def desktop_import_scenario(self):
        path,_=QFileDialog.getOpenFileName(self,'Load acquisition scenario','','Scenario JSON (*.json)')
        if path:
            try:self.replace(Scenario.load(path));self.navigate(1)
            except Exception as exc:QMessageBox.warning(self,'Invalid scenario',str(exc))

    def desktop_random_scenario(self):
        from ..io.scenario_manager import perturb_scenario
        import secrets
        seed=secrets.randbelow(1_000_000)
        self.replace(perturb_scenario(self.engine.config,seed));self.navigate(1)
        self.statusBar().showMessage(f'Seed {seed} is stored in your scenario configuration.',8000)

    def desktop_default(self):
        path=Path(self.output)/'default_scenario.json'
        try:path.parent.mkdir(parents=True,exist_ok=True);self.engine.config.save(path);self.statusBar().showMessage('Startup default saved: '+str(path),8000)
        except Exception as exc:QMessageBox.warning(self,'Cannot save defaults',str(exc))

    def desktop_factory(self):
        (Path(self.output)/'default_scenario.json').unlink(missing_ok=True)
        self.replace(Scenario.load(self.presets/'easy_clear_circular.json'));self.navigate(1)

    def desktop_open_reports(self):
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        path=Path(self.output);path.mkdir(parents=True,exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.absolute())))

    def desktop_about(self):
        QMessageBox.information(self,'V-CAPAT PRO · experimental software',
            'V-CAPAT PRO: virtual FSOC beacon coarse acquisition. This is an experimental simulator and benchmark, NOT an ISRO-issued or flight-certified system. Modelled link BER, turbulence, motion and sensor response require independent physical calibration. Optional RL/YOLO assets are not bundled.')

    def replace(self,config):
        self.engine.close();self.engine=Engine(config);self.plot.engine=self.engine;self.map.engine=self.engine;self.running=True;self.play.setText('Ⅱ  Pause');self.timer.setInterval(max(1,round(1000/config.camera.update_hz)));self.setFocus();self.detectors.blockSignals(True);self.detectors.setCurrentText(config.detector);self.detectors.blockSignals(False);self.controllers.blockSignals(True);self.controllers.setCurrentText(config.controller);self.controllers.blockSignals(False)
    def change_scenario(self):
        path=self.scenarios.currentData()
        if path:self.replace(Scenario.load(path))
    def change_detector(self,text):
        if text:
            try:self.engine.change_detector(text)
            except Exception as exc:QMessageBox.warning(self,'Detector plugin',str(exc))
    def change_controller(self,text):
        if text:
            try:self.engine.config.controller=text;self.engine.controller_plugin=self.engine._make_controller(text)
            except Exception as exc:QMessageBox.warning(self,'Controller plugin',str(exc))
    def show_tool(self,kind):
        registry={'xray':lambda:XRayOverlay(),'arena':lambda:MultiAlgoWidget(self.engine.config),'stress':lambda:StressTestWidget(self.engine.config),'sensitivity':lambda:SensitivityWidget(self.engine.config),'achievements':lambda:Achievements(),'tutorial':lambda:Tutorial(),'replay':lambda:ReplayWidget(),'demo':lambda:JudgeDemo(),'compliance':lambda:ComplianceWidget(),'link':lambda:LinkQualityWidget(),'metrics':lambda:MetricsPanel(),'features':lambda:FeatureAudit()}
        widget=registry[kind]();widget.resize(580,400);widget.show();self._tools.append(widget)
        if kind=='achievements':widget.update_session(self.engine.rows,summarize(self.engine.rows,self.engine.tracker))
        return widget
    def settings(self):
        dialog=Settings(self.engine,self)
        if dialog.exec()==QDialog.Accepted:
            try:self.replace(dialog.result_config())
            except Exception as exc:QMessageBox.warning(self,'Invalid configuration',str(exc))
    def tick(self):
        if self.running:
            row=self.engine.step()
            if row is None:self.running=False;self.play.setText('↺  Replay');return
            if self.engine.source=='simulator' and row['timestamp_s']>=self.engine.config.duration_s:self.running=False;self.play.setText('↺  Replay')
        if self.engine.last_annotated is None:return
        im=self.engine.last_annotated;h,w=im.shape[:2];rgb=cv2.cvtColor(im,cv2.COLOR_BGR2RGB)
        q=QImage(rgb.data,w,h,3*w,QImage.Format_RGB888).copy();self.image.setPixmap(QPixmap.fromImage(q).scaled(self.image.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))
        s=self.engine.snapshot();self.status.setText(s['status']);self.status.setStyleSheet('color:'+('#6ee4be' if s['status']=='LOCKED' else '#f3bd72'))
        self.substatus.setText(f"{'VIDEO / NO DESIGNATION' if s['mode']!='simulator' else 'TARGET #'+str(s['designated_id']+1)}    •    {s['handover_count']} HANDOVERS    •    CONFIDENCE {s['confidence']:.0f}%    •    FRAME {s['frame']:06d}    •    {s['elapsed']:.1f} S")
        def fmt(v,d=1):return '—' if v is None else f'{v:.{d}f}'
        for key,val in [('fps',fmt(s['fps'],0)),('processing',fmt(s['processing_ms'])),('error',fmt(s['pointing_error'])+' px'),('centroid',fmt(s['centroid_error'])+' px'),('pan',fmt(s['pan'],2)+' / '+fmt(s['tilt'],2)+'°'),('retention',fmt(s['lock_retention'])+'%')]:self.metrics[key].setText(val)
        self.link.setText(f"{s['link']:.0f}% / {s['throughput_gbps']:.2f} Gbps" + (f"    LEAD {s['lead_px'][0]:.1f} / {s['lead_px'][1]:.1f} px" if s['lead_enabled'] else ''))
        self.source.setText(f"FPA  {w} × {h}     /     {s['mode'].upper()}     /     DETECTOR {s['detector'].upper()}")
        summary=summarize(self.engine.rows,self.engine.tracker)
        checks=compliance(summary);self.update_pages(s,summary,checks);self.checks.setText('SPEC CHECKS     '+ '     '.join(('✓ ' if v['status']=='PASS' else '✕ ' if v['status']=='FAIL' else '— ')+v['label'].split(' ≤ ')[0].split(' < ')[0].split(' ≥ ')[0] for v in checks.values()))
        for tool in self._tools:
            if not tool.isVisible():continue
            if isinstance(tool,XRayOverlay):tool.show_candidates(s['candidates'])
            elif isinstance(tool,MetricsPanel):tool.update_metrics(s)
            elif isinstance(tool,ComplianceWidget):tool.update_summary(summary)
            elif isinstance(tool,LinkQualityWidget):tool.update_quality(s['link'])
        self.plot.update();self.map.update()
    def designate_at(self,x,y):
        if self.engine.last_raw is not None:
            h,w=self.engine.last_raw.shape[:2]
            try:self.engine.designate_candidate(x*w,y*h)
            except ValueError as exc:self.statusBar().showMessage(str(exc),4000)
    def toggle_xray(self):self.engine.xray=not self.engine.xray
    def toggle(self):
        if not self.running:
            if self.engine.source=='simulator' and self.engine.last and self.engine.last['timestamp_s']>=self.engine.config.duration_s:
                self.replace(self.engine.config);return
            if self.engine.source=='video' and self.engine.video is not None and self.engine.video.get(cv2.CAP_PROP_POS_FRAMES)>=self.engine.video.get(cv2.CAP_PROP_FRAME_COUNT)>0:
                self.engine.seek_video(0)
        self.running=not self.running;self.play.setText('Ⅱ  Pause' if self.running else '▶  Resume')
    def reset(self):self.replace(self.engine.config)
    def open_video(self):
        path,_=QFileDialog.getOpenFileName(self,'Open benchmark footage','','Video (*.mp4 *.avi *.mov)')
        if path:
            try:
                self.engine.open_video(path);self.running=True
                self.timer.setInterval(max(1,round(1000/self.engine.video_fps)))
            except Exception as exc:QMessageBox.warning(self,'Video error',str(exc))
    def open_webcam(self):
        index,ok=QInputDialog.getInt(self,'Webcam device','Local camera index',0,0,10)
        if ok:
            try:
                self.engine.open_webcam(index);self.running=True
                self.timer.setInterval(max(1,round(1000/self.engine.video_fps)))
            except Exception as exc:QMessageBox.warning(self,'Webcam error',str(exc))
    def open_truth(self):
        path,_=QFileDialog.getOpenFileName(self,'Open ground-truth CSV','','CSV (*.csv)')
        if path:
            try:
                self.engine.video_gt=load_ground_truth(path)
                if self.engine.source=='video':self.engine.seek_video(0);self.running=True
                QMessageBox.information(self,'Ground truth',f'{len(self.engine.video_gt)} labelled frames loaded.')
            except Exception as exc:QMessageBox.warning(self,'CSV error',str(exc))
    def export(self):
        try:folder=export_session(self.engine,self.output);QMessageBox.information(self,'Report exported',f'Session files saved to:\n{folder}')
        except Exception as exc:QMessageBox.warning(self,'Export error',str(exc))
    def record(self):
        try:
            if self.engine.recorder:
                path=self.engine.stop_recording();self.statusBar().showMessage(f'Recording saved to {path}',8000)
            else:
                path=Path(self.output)/'recordings'/('session_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')+'.mp4')
                self.engine.start_recording(path);self.statusBar().showMessage('MP4 recording active',5000)
        except Exception as exc:QMessageBox.warning(self,'Recording error',str(exc))
    def screenshot(self):
        path,_=QFileDialog.getSaveFileName(self,'Save annotated frame','tracking_frame.png','PNG (*.png)')
        if path and self.engine.last_annotated is not None:cv2.imwrite(path,self.engine.last_annotated)
    def keyPressEvent(self,event):
        k=event.key();speed=self.engine.config.camera.max_pan_speed
        if k==Qt.Key_Space:self.engine.manual=False;self.engine.command=(0,0)
        if k in (Qt.Key_W,Qt.Key_Up,Qt.Key_S,Qt.Key_Down,Qt.Key_A,Qt.Key_Left,Qt.Key_D,Qt.Key_Right):
            self.engine.manual=True;self.engine.command=(speed*(k in (Qt.Key_D,Qt.Key_Right))-speed*(k in (Qt.Key_A,Qt.Key_Left)),speed*(k in (Qt.Key_S,Qt.Key_Down))-speed*(k in (Qt.Key_W,Qt.Key_Up)))
    def keyReleaseEvent(self,event):
        if not event.isAutoRepeat() and self.engine.manual:self.engine.command=(0,0)
    def closeEvent(self,event):self.engine.close();super().closeEvent(event)

def run(engine,presets,output):
    app=QApplication.instance() or QApplication([]);app.setStyleSheet(STYLE)
    splash_path=Path(__file__).resolve().parents[2]/'assets'/'splash.png'
    splash=QSplashScreen(QPixmap(str(splash_path))) if splash_path.is_file() else None
    if splash:splash.show();app.processEvents()
    window=Window(engine,presets,output);window.show()
    if splash:splash.finish(window)
    app.exec()
