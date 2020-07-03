import qcodes as qc
from qcodes.dataset.experiment_container import (Experiment,
                                                 load_last_experiment,
                                                 new_experiment)
from qcodes.dataset.database import initialise_database
from qcodes.dataset.measurements import Measurement


import numpy as np
from QCmeasurement import *
from meas_util import *
from tqdm import tqdm, tqdm_notebook

from Exps import *

class JJmeas(QCmeas):
    
    def __init__(self, sample, tools = [] ,  folder = r'..\_expdata'): 
        
        
        super().__init__(sample, tools ,  folder)
        
        self.exps = Exps(sample, folder)
        
    
    
    def set_param(self, **kwparams):
        
        
        for k, v in kwparams:
            self.k = v
            self.exps.k = v
        
        
        
    def meas_Voffset(self, i):
    
        V_off = 0
        N = 10
        
        

        I = self.tools['I']
        V = self.tools['V']

        I.set(i)

        for j in range(N):
            time.sleep(.5)
            V_off += V.get()
        
        V.Voff = V_off/N
        return V.Voff
    
    
    def stabilize_I(self, amp):
        
        
        I = self.tools['I']
            
        x = np.arange(100)
        i_s = amp*np.exp(- x/20 )* np.cos(x/3)
        
        for i in i_s:
            I.set(i)
            time.sleep(0.1)


    
            
            
    def IVC_cust (self, i_list, Ioff = 0, Vthr = 1, dt = 0.1, N_avg = 1, label = ''):

        I = self.tools['I']
        V = self.tools['V']
        
        
        
        self.meas_Voffset(Ioff)
        Voff =  V.Voff

        meas = self.set_meas(V, I)

        
        ti_list = tqdm_notebook(i_list, leave = False)
        
        if label == '':
            label = self.make_label()


        self.name_exp( exp_type = label )
        with meas.run() as datasaver:
            for i in ti_list:

                I.set(i+Ioff)
                
                
                time.sleep(dt)

                is_vs = [[I.get(),V.get()] for _ in range( N_avg)]
                ir, v = np.mean(is_vs, axis = 0)

                
                
                    
                res = [( I, ir - Ioff  ), ( V, v - Voff  )]
                

                
                ti_list.set_description('I = {}A'.format( SI(ir) ))
                
                if abs( v - Voff) > Vthr:
                    datasaver.add_result(( I, np.nan  ), ( V, np.nan  ))
                    break
                
                datasaver.add_result(*res)
                
                
        
        self.stabilize_I(amp = i)
        
        run_id = datasaver.run_id
        
        self.last_runid = run_id
        
#         if self.isexp:
            
#             self.exps[datasaver.run_id] = self.make_exp_line()
#             self.isexp = False

        return run_id 
    
    
    def IVC_udu (self, amp, stp, **kwargs):

        i_list = udu_list(amp, stp)
        run_id = self.IVC_cust ( i_list, **kwargs)
        

        return run_id 
    
    def IVC_fwd (self, amp, stp,  **kwargs):

        i_list = np.concatenate( [np.linspace(0,  amp, int(amp/stp)),
                            np.linspace(amp,  0, int(amp/stp/10)+1),
                            np.linspace(0, -amp, int(amp/stp)),
                            np.linspace(-amp, 0, int(amp/stp/10)+1)])
                                        
        run_id = self.IVC_cust ( i_list, **kwargs)
        
        

        return run_id 

    def cos_to_B(self, cos):
        
        
        for frust in ['ZF', 'FF']:
              if not hasattr(self, frust):
                     raise Exception(f'Please indicate value of {frust}!')
        
        ZF = self.ZF
        FF = self.FF

        return np.arccos(cos)*(2* (FF - ZF)/np.pi + ZF  )
    
    
    def Bscan(self,  B_list = None, cos_list = None):

#         self.isexp = True
        
        runids = []
        
        exps = dict()
        
        B = self.tools['B']
        T = self.tools['T']
        
        if B_list is None and cos_list is None:
            raise Exception('Please specify either B or cos list!')
                
        elif B_list is not None and cos_list is not None:
            raise Exception('Please choose either B or cos list!')
                
        elif cos_list is not None:
            B_list = self.cos_to_B(cos_list)
            

        tB_list = tqdm_notebook(B_list)

        for b in tB_list:
            
            B.set(b)
            tB_list.set_description('B = {}A'.format( SI(b) ))

            yield self
            
            runids.append(self.last_runid)
            #             exps[self.last_runid] = self.tool_status()
        
        
        
        B.set(0)    
#         print("{" + 
#             " 'ids' : range({},{}+1),".format(runids[0], runids[-1]) +
#             " 'B' : np.linspace({:1.2e},{:1.2e}, {}),".format(B_list[0], B_list[-1], len(B_list)) +
#             " 'T' : {:1.3f},".format(np.round(T.get()*200)/200) + 
#             " 'comm : '' }"
#              )

            
            
            
            
    def Tscan(self,  T_list):        
        
        htr = self.tools['htr']
        T8 = self.tools['T']
        
        tolerT8 = 0.02
        chkrepeat = 20
        chkperiod_sec = 2
        
        tT_list =  tqdm_notebook(T_list)
        for t in tT_list:
        
            htr.set(t)
            print('ramping T8 to {}K...'.format(SI(t)))
            time.sleep(30)

            count_T = 0
            while count_T < chkrepeat:
                T_now = T8.get()
                if (1-tolerT8)* t <= T_now <= (1+tolerT8) * t :
                    count_T +=1
                    
                    time.sleep(chkperiod_sec)
                    print('{}'.format(SI(T_now), end = " ") )
                elif count_T >= 1 :
                    count_T -=1
            
            print('T is set')              
            tT_list.set_description('T = {}K'.format( SI(t) ))

            yield self

            
        

