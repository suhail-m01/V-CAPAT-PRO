"""Settings Dialog for the desktop control room."""
from PySide6.QtCore import Qt,QTimer,QPointF,Signal
from PySide6.QtGui import QImage,QPixmap,QPainter,QPen,QColor,QFont,QIcon
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QLabel,QPushButton,QComboBox,QGroupBox,QFileDialog,QMessageBox,QDialog,QTabWidget,QFormLayout,QSpinBox,QDoubleSpinBox,QCheckBox,QScrollArea,QFrame)
from ..config.settings import Scenario

class Settings(QDialog):
    """Tabbed editor for validated simulator parameters; no hidden truth controls."""
    def __init__(self,engine,parent=None):
        super().__init__(parent);self.engine=engine;self.setWindowTitle('Mission configuration');self.resize(600,590)
        outer=QVBoxLayout(self);tabs=QTabWidget();outer.addWidget(tabs);self.widgets={}
        fields={
            'Target':[('trajectory','choice',['circular','straight','figure8','random','spiral','sinusoidal','leo','uav','haps','aircraft','star']),('shape','choice',['gaussian','square','circle','airy']),('speed_pps','float',5,200),('size_px','int',5,20),('width_px','int',5,20),('height_px','int',5,20),('count','int',1,5),('auto_handover','choice',['off','on']),('brightness','int',30,255),('blink_hz','float',0,12),('initial_x','int',0,4000),('initial_y','int',0,4000),('initial_mode','choice',['manual','center','random']),('boundary','choice',['bounce','wrap']),('color_r','int',0,255),('color_g','int',0,255),('color_b','int',0,255)],
            'Camera':[('max_pan_speed','float',5,10),('max_tilt_speed','float',5,10),('update_hz','int',30,60),('fov_x','float',.5,30),('fov_y','float',.5,30),('resolution_w','int',320,1920),('resolution_h','int',240,1080),('initial_pan_deg','float',-20,20),('initial_tilt_deg','float',-20,20),('acceleration_deg_s2','float',0,100),('digital_zoom','float',1,4),('color','choice',['off','on'])],
            'Environment':[('atmosphere','choice',['clear','haze','fog','rain','low_light','turbulence']),('noise_types','choice',['none','gaussian','poisson','salt_pepper','gaussian,poisson','gaussian,salt_pepper','gaussian,poisson,salt_pepper']),('noise_std','float',0,20),('salt_pepper_pct','float',0,.1),('camera_jitter_px','float',0,20),('platform_motion','choice',['none','linear','circular','sinusoidal','random','figure8']),('platform_amplitude_px','float',0,20),('platform_max_step_px','float',0,20),('contrast_scale','float',.1,1.5),('brightness_offset','float',-100,100),('turbulence_r0','float',.03,1),('occlusion_start_s','float',-1,120),('occlusion_duration_s','float',0,30)],
            'Link':[('point_ahead','choice',['off','on']),('distance_km','float',10,40000),('round_trip','choice',['one_way','round_trip'])],
            'World':[('width','int',2000,4000),('height','int',2000,4000),('background','choice',['deep_space','sky','solid']),('star_density','float',0,.001),('seed','int',0,999999),('solid_gray','int',0,255)],
            'Control':[('kp','float',0,100),('ki','float',0,100),('kd','float',0,100),('deadband_deg','float',0,1),('search_pattern','choice',['spiral','raster','random']),('assist_fraction','float',0,1)],
            'Tracking':[('process_noise','float',0,100),('measurement_noise','float',.01,100),('hits_to_lock','int',1,20),('coast_after','int',1,100),('reacquire_after','int',2,200)],
            'Sensor / security':[('sensor_enabled','choice',['off','on']),('sensor_qe','float',.01,1),('sensor_read_noise_e','float',0,30),('sensor_dark_current_e_s','float',0,500),('sensor_exposure_s','float',.0001,2),('sensor_bit_depth','choice',['8','12','14','16']),('hot_pixel_pct','float',0,.01),('thermal_enabled','choice',['off','on']),('temperature_c','float',-50,100),('thermal_coefficient_px_c','float',0,2),('spoof_enabled','choice',['off','on']),('spoof_offset_px','float',5,300)]}
        section={'Target':'target','Camera':'camera','Environment':'disturbance','Link':'link','World':'world','Control':'control','Tracking':'tracking','Sensor / security':'disturbance'}
        for tabname,entries in fields.items():
            page=QWidget();form=QFormLayout(page);form.setSpacing(11)
            area=QScrollArea();area.setWidgetResizable(True);area.setFrameShape(QFrame.NoFrame);area.setWidget(page);tabs.addTab(area,tabname)
            obj=getattr(engine.config,section[tabname])
            for name,kind,*args in entries:
                if name=='initial_x':value=obj.initial_position[0]
                elif name=='initial_y':value=obj.initial_position[1]
                elif name in ('fov_x','fov_y'):value=obj.fov_deg[0 if name=='fov_x' else 1]
                elif name in ('resolution_w','resolution_h'):value=obj.resolution[0 if name=='resolution_w' else 1]
                elif name=='noise_types':value=','.join(obj.noise_types) or 'none'
                elif name=='auto_handover':value='on' if obj.auto_handover else 'off'
                elif name=='point_ahead':value='on' if obj.point_ahead else 'off'
                elif name=='round_trip':value='round_trip' if obj.round_trip else 'one_way'
                elif name in ('color','sensor_enabled','thermal_enabled','spoof_enabled'):value='on' if getattr(obj,name) else 'off'
                elif name.startswith('color_'):value=obj.color_rgb['rgb'.index(name[-1])]
                else:value=getattr(obj,name)
                if name=='sensor_bit_depth':value=str(value)
                if kind=='choice':
                    widget=QComboBox();widget.addItems(args[0]);widget.setCurrentText(str(value))
                else:
                    widget=QSpinBox() if kind=='int' else QDoubleSpinBox();widget.setRange(args[0],args[1])
                    if kind!='int':widget.setDecimals(7 if name in ('star_density','hot_pixel_pct','deadband_deg') else 4)
                    widget.setValue(value)
                widget.setToolTip(name.replace('_',' ').title()+' · applying changes restarts the deterministic session.')
                form.addRow(name.replace('_',' ').title(),widget);self.widgets[(section[tabname],name)]=widget
        info=QLabel('Camera frame size and FOV determine the pixel-to-angle conversion. Apply restarts the seeded run.');info.setWordWrap(True);outer.addWidget(info)
        row=QHBoxLayout();row.addStretch();cancel=QPushButton('Cancel');cancel.clicked.connect(self.reject);apply=QPushButton('Apply & restart');apply.setObjectName('primary');apply.clicked.connect(self.accept);row.addWidget(cancel);row.addWidget(apply);outer.addLayout(row)
    def result_config(self):
        data=self.engine.config.to_dict()
        for (section,name),widget in self.widgets.items():
            value=widget.currentText() if isinstance(widget,QComboBox) else widget.value()
            if name in ('initial_x','initial_y'):data['target']['initial_position'][0 if name=='initial_x' else 1]=value
            elif name in ('fov_x','fov_y'):data['camera']['fov_deg'][0 if name=='fov_x' else 1]=value
            elif name in ('resolution_w','resolution_h'):data['camera']['resolution'][0 if name=='resolution_w' else 1]=value
            elif name=='noise_types':data['disturbance']['noise_types']=[] if value=='none' else value.split(',')
            elif name=='auto_handover':data['target'][name]=value=='on'
            elif name=='point_ahead':data['link'][name]=value=='on'
            elif name=='round_trip':data['link'][name]=value=='round_trip'
            elif name in ('color','sensor_enabled','thermal_enabled','spoof_enabled'):data[section][name]=value=='on'
            elif name=='sensor_bit_depth':data[section][name]=int(value)
            elif name.startswith('color_'):data['target']['color_rgb']['rgb'.index(name[-1])]=int(value)
            else:data[section][name]=value
        return Scenario.from_dict(data)

