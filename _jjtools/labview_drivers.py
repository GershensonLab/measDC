import time
from si_prefix import si_format
# to use labview program, open all relevant labview before running python
import win32com.client  # Python ActiveX Client
LabVIEW = win32com.client.Dispatch('LabVIEW.Application') 
dir_ = r'\\JOSH-PC\Gersh_Labview\DC measurement'

class labView(object):
    def __init__(self):
        self.VI =None    
    def initialize(self,VIpath):
        print("initialization %s" % VIpath)
        self.VI= LabVIEW.getvireference(VIpath)  # Path to LabVIEW VI
        self.VI._FlagAsMethod("Call")  # Flag "Call" as Method  
        
class LS370htr(labView):
    
    def __init__(self):
        VIpath = dir_+"\LSCI 370 PYTHON_conf.vi"
        super(LS370htr,self).initialize(VIpath)
       
    def Tget(self):
        self.VI.Call()
        return 'Current Setpoint = {}K'.format(si_format(float(self.VI.getcontrolvalue('Setpoint'))))

    def Tset(self, setpt):
        paras =  ['Setpoint (K)', 'Setpoint change']
        values = [ setpt        ,  True            ]
        self.VI.Call(paras,values)
        time.sleep(0.2)
        return 'setpoint changed to {}K'.format(si_format(setpt))

    def PIDget(self):
        self.VI.Call()
        return 'Current PID = {}'.format(self.VI.getcontrolvalue('PID'))

    def PIDset(self, P, I, D):
        paras =  ['P','I','D', 'PID change']
        values = [ P , I , D ,  True       ]
        self.VI.Call(paras,values)
        time.sleep(0.2)
        return 'PID changed to {},{},{}'.format(P,I,D)

    def HTRget(self):
        self.VI.Call()
        htrdic = {0: 'off'   , 1: '31.6uA',
                  2: '100uA' , 3: '316uA' ,
                  4: '1mA'   , 5: '3.16mA',
                  6: '10mA'  , 7: '31.6mA',
                  8: '100mA' }
        htrset = self.VI.getcontrolvalue('Heater Range').split('\n\r')
        return 'Current heater = {}'.format(htrdic[int(htrset[0])])

    def HTRset(self, HTRrange):
        
        htrdic = {'off'    :0, '31.6uA' :1,
                  '100uA'  :2, '316uA'  :3,
                  '1mA'    :4, '3.16mA' :5,
                  '10mA'   :6, '31.6mA' :7,
                  '100mA'  :8}        
        paras =  ['HTR change'      ]
        values = [ htrdic[HTRrange] ]
        self.VI.Call(paras,values)
        time.sleep(0.2)
        
        return 'Heater changed = {}'.format(HTRrange)
    
    def PWRget(self):
        self.VI.Call()
        return 'Heater level (%) = {}'.format(self.VI.getcontrolvalue('Heater'))