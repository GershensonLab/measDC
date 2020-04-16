import qcodes as qc
from qcodes import Station, load_by_run_spec, load_by_guid
from qcodes.instrument.base import Instrument
from qcodes.dataset.experiment_container import (Experiment,
                                                 load_last_experiment,
                                                 new_experiment)
from qcodes.dataset.database import initialise_database
from qcodes.dataset.measurements import Measurement
from qcodes.dataset.plotting import plot_by_id, get_data_by_id, plot_dataset
# from qcodes.dataset.data_export import get_shaped_data_by_runidb


from tqdm import tqdm, tqdm_notebook
import numpy as np



def set_meas(dep, fast_indep, slow_indep = None, setup =  None, cleanup =  None):
    """
       Regestration of the parameters and setting up before/after run procedure
        
       args:
            dep: InstParameter to be regestered as dependent var 
            fast_indep: InstParameter to be regestered as fast independent var 
            slow_indep: InstParameter to be regestered as second independent var (if any) 
            setup: Procedure to be done before run
            cleanup: Procedure to be done after run
            
        returns:
        meas: Measurement() object
           
    """    
    meas = Measurement()
    meas.register_parameter( fast_indep )  # register the fast independent parameter
    
    if slow_indep is not None:
        meas.register_parameter( slow_indep )  # register the first independent parameter
        meas.register_parameter( dep , setpoints = ( slow_indep,  fast_indep ) ) 
    else:
        meas.register_parameter( dep, setpoints = ( fast_indep , ))
        
    meas.add_before_run(setup, args=())    
    meas.add_after_run(cleanup, args=())    
    meas.write_period = 2
    
    return meas


def name_exp(sample, exp_type = '', **kwargs):
    """
        Set name of the experiment
        args:
            ext_type[str]:   any label for experiment
            **kwars[eg Bfield = 50e-6]    Dict of the parameter name and its value to add 
        returns:
            new_experimenrt object
    
    """
    name = '{:s}_'.format(exp_type)
    for var , val in kwargs.items():
        name += '__{}= {}'.format( var,  eng(val) )

    sample_name = "{}".format(sample)
#     if not res:
#         sample_name += '__{:1.3f}'.format( res/1e9 )
                
    return new_experiment( name = name,
                           sample_name = sample_name )

# def ud_list(amp, stp):
    
#     n  =  np.round(amp/stp)
    
#     u1 = np.linspace (0, amp, n + 1)
#     d = np.linspace (amp, 0, n +1)
    
    
#     return np.concatenate ([u1, d])

def udu_list(amp, stp):
    
    n  =  np.round(amp/stp)
    
    u1 = np.linspace (0, amp, n + 1)
    d = np.linspace (amp, -amp, 2*n +1)
    u2 = np.linspace (-amp, 0, n + 1)
    
    return np.concatenate ([u1, d, u2]) 


def uduFF_list(amp1=240e-12, amp2=2000e-12, stp1=2e-12, stp2=80e-12):

    i_list_uf = np.linspace(0, amp1, round (amp1/stp1) + 1)
    i_list_uc = np.linspace(amp1, amp2, round ((amp2-amp1)/stp2) + 1)
    i_list = np.append(i_list_uf, i_list_uc)

    i_list_d = [np.linspace(amp2, amp1, round ((amp2-amp1)/stp2) + 1),
                np.linspace(amp1, 0, round (amp1/stp1) + 1),
                np.linspace(0, -1*amp1, round (amp1/stp1) + 1),
                np.linspace(-1*amp1, -1*amp2, round ((amp2-amp1)/stp2) + 1)]
    for lst in i_list_d:
        i_list = np.append(i_list, lst)

    i_list_ucn = np.linspace(-1*amp2, -1*amp1, round ((amp2-amp1)/stp2) + 1)
    i_list_ufn = np.linspace(-1*amp1, 0, round (amp1/stp1) + 1)
    i_list = np.append(i_list, i_list_ucn)
    i_list = np.append(i_list, i_list_ufn)

    return i_list


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