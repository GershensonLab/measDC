# -*- coding: utf-8 -*-
"""
Created on Mon Sep 10 10:28:59 2018

@author: kalas
"""

import numpy as np
import os
from collections.abc import Iterable

from JJformulas import *


import qcodes as qc
from qcodes.dataset.database import initialise_database
from qcodes.dataset.plotting import plot_by_id, get_data_by_id

def xy_by_id(idx):
    alldata = get_data_by_id(idx)
    
    x = alldata[0][0]['data']
    y = alldata[0][1]['data']
    
    return x,y

def pbi(idx, **kwargs):
    
    if 'marker'  not in kwargs.keys():
        kwargs['marker'] = 'o'
        
    if 'ls' not in kwargs.keys():
        kwargs['ls'] = 'None'
        
    axes, _ = plot_by_id(idx, **kwargs)
    
    return axes[0]


def batch_plot_by_id(ids, ax = None, labels = None, **kw):
    if ax is None:
        fig, ax = plt.subplots()
        
    for i, idx in enumerate(ids):
        if labels is not None:
            label = labels[i]
        else:
            label = ''
            
        plot_by_id(idx, axes = ax, label = label, **kw)
        
    ax.legend()
    return ax

bpbi = batch_plot_by_id




# def avg_group(vA0, vB0):
#     vA0 = np.round(vA0*1e15)/1e15   #remove small deferences
#     vB0 = np.round(vB0*1e15)/1e15
    
#     vA, ind, counts = np.unique(vA0, return_index=True, return_counts=True) # get unique values in vA0
#     vB = vB0[ind]
#     for dup in vB[counts>1]: # store the average (one may change as wished) of original elements in vA0 reference by the unique elements in vB
#         vB[np.where(vA==dup)] = np.average(vB0[np.where(vA0==dup)])
#     return vA, vB


def cut_dxdy(vA0, vB0, dx,dy):
    
    ind1 = np.where(np.abs(vA0) < dx )
    vA1, vB1 = vA0[ind1], vB0[ind1]

    ind2 = np.where(np.abs(vB1) < dy )
    vA, vB = vA1[ind2], vB1[ind2]

    return vA, vB


def offsetRemove(X,Y, offX, offY):
    
    return X - offX, Y - offY 


def eng_string( x, sig_figs=3, si=True):
    x = float(x)
    sign = ''
    if x < 0:
        x = -x
        sign = '-'
    if x == 0:
        exp = 0
        exp3 = 0
        x3 = 0
    else:
        exp = int(math.floor(math.log10( x )))
        exp3 = exp - ( exp % 3)
        x3 = x / ( 10 ** exp3)
        x3 = round( x3, -int( math.floor(math.log10( x3 )) - (sig_figs-1)) )
        if x3 == int(x3): # prevent from displaying .0
            x3 = int(x3)

    if si and exp3 >= -24 and exp3 <= 24 and exp3 != 0:
        exp3_text = 'yzafpnum kMGTPEZY'[ exp3 // 3 + 8]
    elif exp3 == 0:
        exp3_text = ''
    else:
        exp3_text = 'e%s' % exp3

    return ( '%s%s%s') % ( sign, x3, exp3_text)



def load_IVC_B(file):

    IVC = []
    
    data = np.genfromtxt(file, skip_header = 22 ) [1:,:] 
    Ts    = data[:,5]
    Iraw = data[:,7]
    Vraw = data[:,8]
    IG   = data[:,6]

    

    index_sets = [np.argwhere(i == IG) for i in np.unique(IG)]

    Iss = []
    Igs = []

    for sll in index_sets:
        sl = sll.flatten()

#         I, V = avg_group(Iraw[sl], Vraw[sl])
        I, V = Iraw[sl], Vraw[sl]
        
        T = np.mean(Ts[sl])
        B = np.mean(IG[sl])
        
        IVC_i = {'I' : I, 'V' : V, 'T' : T, 'B' : B }
        
        IVC.append(IVC_i)

    return IVC





    for i in exp['ids']:

        I, V = xy_by_id(i)
        
        Tb = exp['T']
        I, V = offsetRemove(I,V, offX = 25.5e-12, offY = 35e-6)

        
        I, V = cut_dxdy(I, V, dx = 1e-9 ,dy = 0.1e-3)

        I = I - Iqp(  V, T = Tb, G1 = 1/20.06e3, G2 = 1/120e3, V0 = 0.35e-3 ) 
        
        ax.plot(I,V, 'o')


       

        
    exp ['Is' ] =  Is
    exp ['Vs' ] =  Vs

        

    



def load_exp_B(file, ZF, FF, VERBOSE = False):
    
    exp  = {}
   
    Isws = []
    R0s  = []
    Is   = []
    Vs   = []
    Bs   = []
    
    data  = np.genfromtxt(file, skip_header = 22 ) [1:,:] 
    Ts    = data[:,5]
    Iraw  = data[:,7]
    Vraw  = data[:,8]
    IG    = data[:,6]
    
    T = np.mean(Ts)

    index_sets = [np.argwhere(i == IG) for i in np.unique(IG)]

    Iss = []
    Igs = []

    for sll in index_sets:
        sl = sll.flatten()

        I, V = Iraw[sl], Vraw[sl]
        
        n = len(I)
        n_up, n_down = np.int(n/4), np.int(3*n/4)
        
        I = np.append(I[: n_up], I[ n_down:])
        V = np.append(V[: n_up], V[ n_down:])
    
        I, V = cut_dxdy(I, V, dx = 5e-8 ,dy = 2e-5)
        
        Is.append(I)
        Vs.append(V)
        
        Isw, R0 = extract_Isw_R0 (I,V)
        Isws.append(Isw)
        R0s.append(R0)
        
        Bs.append(np.mean(IG[sl]))
        

        
    exp = {'Is' : Is, 'Vs' : Vs, 'T' : T, 'B' : np.array(Bs) }
    
    exp ['Isws'] =  np.array(Isws)
    exp ['R0s' ] =  np.array(R0s )
    exp ['cos' ] =  np.array( abs(np.cos(np.pi*(exp['B'] - ZF )/(ZF + 2* FF)) ) )

        
    if VERBOSE:
        fig, ax = plt.subplots()
        for i, cos in enumerate (exp ['cos' ]):

            ax.plot(exp ['Is'][i],exp ['Vs'][i], 'o', label = 'cos = {:1.2f}'.format(cos))
            
            ax.set_title('T = {:3.0f} mK'.format(exp['T'] / 1e-3))
#         ax.legend()
        
    return exp




def get_Isw_R0 (Is,Vs, VERBOSE = False):
    
        if len( Is )== 0 or len( Vs )== 0 :
            Isw, R0 = np.nan, np.nan
            return Isw, R0

        try:
            Isw = (np.max(Is) - np.min(Is))/2  
        except ValueError:
            Isw = np.nan
        
        order = Is.argsort()
        
        Is, Vs = Is[order], Vs[order]

        n_sl =  np.where (Is < 300e-12)
        
        if len( Vs[n_sl] )== 0 :
            R0 = np.nan
            return Isw, R0
        
        R0, b = np.polyfit (  Is[n_sl] , Vs[n_sl], 1 )
        
        if R0 < 0:
            R0 = np.nan
            
            
            
        if VERBOSE:
            fig, ax = plt.subplots()
            
            ax.plot(Is, Vs, marker = 'o', ls = 'None')
            
            ax.plot(Is, R0*Is+b)
            
            
        
        return Isw, R0


def get_Isw_R0_by_id (idx, dx = 10e-9, dy = 50e-6, Voff = 0, VERBOSE = False):
    
    Isws, R0s = [], []
    
    
    if not isinstance(idx, Iterable):
        SINGLE_VAL = True
        idx = [idx]
    else:
        SINGLE_VAL = False
        
    for id_ in idx:
        
        I,V = xy_by_id(id_)

        V -= Voff

        Is,Vs = cut_dxdy(I, V, dx,dy)


        Isw, R0 = get_Isw_R0 (Is,Vs, VERBOSE = VERBOSE )
    
        Isws.append(Isw)
        R0s.append(R0)
        
    if SINGLE_VAL:
        return Isws[0], R0s[0]
    else:
        return np.array(Isws), np.array(R0s) 
    
    
    
    
def load_by_key(exp, key, val):
        
    ind =   np.argmin ( np.abs( exp[key] - val ))
    return ind
    
def plot_by_key(exp, key, val, ax = None,**kw):
   
    ind =   np.argmin ( np.abs( exp[key] - val ))
    
    I, V = exp['Is'][ind], exp['Vs'][ind]
    
#     I = I - V/1.3e9

    if ax == None:
        fig, ax = plt.subplots()
        
    ax.plot( I, V, 'o', label = 'T = {:2.0f} mK, {} = {:1.2f} '.format( exp['T']/1e-3, key, exp[key][ind] ) , **kw)
    ax.legend()   
    
    return I, V
    
    
    
    
    
    
    
    
def find_exp_R0(I, V):
    
        dI_max = np.max (np.diff (I) )
        I, V =  np.sort(I), np.sort(V)
        if dI_max ==0:
            dI_max = 1e-11
        I, V =  XYEqSp(I, V, step = dI_max)
        
        R0 = np.mean (np.diff (V) )/np.mean (np.diff (I) )

#         R0 = Rdiff_TVReg(V, Istep = dI_max )

        return R0
    
    

def plot_IVC(ax, IVC, cut = False, plotRd = False):
    
    I = IVC['I']
    V = IVC['V']
    B = IVC['B']
    
    

    
    cosφ =  np.abs( np.cos(np.pi/2*B/8.85e-4))
    
    IVC['cosφ'] = cosφ
    
    if cut:
        I, V = cut_dxdy(I, V, dx = 5e-9 ,dy = 3.85e-5)
        I, V = IVC_symmer(I,V)

#         dI_max = np.max (np.diff (I) )
#         I, V =  XYEqSp(I, V, step = dI_max)
        
#         R0 = Rdiff_TVReg(V, Istep = dI_max )
#         ax.plot (I, I*np.min(  np.abs(R0) ))
    
    ax.plot(I ,V, 'o-',  label = 'cos = {:1.2f}'.format(cosφ))

    
    
    if plotRd:
        Rds = Rdiff_TVReg(V, Istep = 1e-10)
        ax2 = ax.twinx()
        ax2.plot(I, Rds)
        





def V_func(I,V, val):
    out = []
    for x in np.nditer(val):
        out = np.append (out,  V[np.argmin(abs(I-x))])
    return out




def XYEqSp(Xarr, Yarr, step):
    outX = []
    outY = []

    if len(Xarr) == 0 :
        outX, outY = 0, 0
    else:    
        n = int((np.max(Xarr) - np.min(Xarr)) // step)    

        for i in range(n):
            outX = np.append( outX, V_func(Xarr, Xarr, np.min(Xarr) + i*step)  )
            outY = np.append( outY, V_func(Xarr, Yarr, np.min(Xarr) + i*step)  )

    return outX, outY





def IVC_symmer(I,V):
    
    I_off = ( np.max(I) + np.min(I) )/2
    V_off = ( np.max(V) + np.min(V) )/2
    V_off = 0
    return I - I_off, V - V_off 








    
