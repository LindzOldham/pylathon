import numpy as np
import pylab as pl
import pyfits as py
from stellarpop import tools, distances
dist = distances.Distance()


def MassK(K,z):
    sed = tools.getSED('BC_Z=1.0_age=7.000gyr')
    kfilt = tools.filterfromfile('Kp_NIRC2')
    K_modrest = tools.ABFM(kfilt,sed,0.0) 
    K_modobs = tools.ABFM(kfilt,sed,z)
    K_rest = K + K_modrest - K_modobs
    mass_K = 0.4*(K_rest - K_modrest)
    K_sun = 5.19
    DL = dist.luminosity_distance(z)
    DM = 5.*np.log10(DL*1e6) - 5.
    K_restabs = K_rest - DM
    lum = -0.4*(K_restabs - K_sun)
    return lum, K_rest

def MassR(R,z):
    sed = tools.getSED('BC_Z=1.0_age=7.000gyr')
    rfilt = tools.filterfromfile('F814W_ACS')  
    R_modrest = tools.ABFM(rfilt,sed,0.0)
    R_modobs = tools.ABFM(rfilt,sed,z)
    R_rest = R + R_modrest - R_modobs
    mass_R = 0.4*(R_rest - R_modrest)
    R_sun = 4.57
    DL = dist.luminosity_distance(z)
    DM = 5.*np.log10(DL*1e6) - 5.
    R_restabs = R_rest - DM
    lum = -0.4*(R_restabs - R_sun)
    return lum, R_rest

def MassB1(B,z):
    sed = tools.getSED('BC_Z=1.0_age=7.000gyr')
    bfilt = tools.filterfromfile('F606W_ACS')
    B_modrest = tools.ABFM(bfilt,sed,0.0) 
    B_modobs = tools.ABFM(bfilt,sed,z)
    B_rest = B + B_modrest - B_modobs
    mass_B = 0.4*(B_rest - B_modrest)
    B_sun = 4.74
    DL = dist.luminosity_distance(z)
    DM = 5.*np.log10(DL*1e6) - 5.
    B_restabs = B_rest - DM
    lum = -0.4*(B_restabs - B_sun)
    return lum, B_rest

def MassB2(B,z):
    sed = tools.getSED('BC_Z=1.0_age=7.000gyr')
    bfilt = tools.filterfromfile('F555W_ACS')
    B_modrest = tools.ABFM(bfilt,sed,0.0) 
    B_modobs = tools.ABFM(bfilt,sed,z)
    B_rest = B + B_modrest - B_modobs
    mass_B = 0.4*(B_rest - B_modrest)
    B_sun = 4.83
    DL = dist.luminosity_distance(z)
    DM = 5.*np.log10(DL*1e6) - 5.
    B_restabs = B_rest - DM
    lum = -0.4*(B_restabs - B_sun)
    return lum, B_rest

## test - Matt's K-band magnitude
K = 17.7
mass_K, K_rest = MassK(K,0.39)
print '%.2f'%mass_K, '%.2f'%K_rest


## J1347 - 606 and 814
B = 23.32 # 606
R = 21.41 # 814
z = 0.63 # scale = 6.915 kpc/"
lum_B, B_rest = MassB1(B,z)
lum_R, R_rest = MassR(R,z)
print 'J1347: source galaxy: B_rest, R_rest, lum_B, lum_R',  '%.2f'%B_rest, '%.2f'%R_rest, '%.2f'%lum_B, '%.2f'%lum_R

## lens galaxy
B_lens, R_lens = 19.83, 18.75
mass_Blens, Blens_rest = MassB1(B_lens,0.39)
mass_Rlens, Rlens_rest = MassR(R_lens,0.39)
print 'J1347: lens galaxy', '%.2f'%Blens_rest, '%.2f'%Rlens_rest, '%.2f'%mass_Blens, '%.2f'%mass_Rlens

## J1605 - 555 and 814
B, R = 21.73, 19.62
z = 0.542 # scale = 6.435 kpc/"
lum_B, B_rest = MassB2(B,z)
lum_R, R_rest = MassR(R,z)
print 'J1605, source galaxy: ',  '%.2f'%B_rest, '%.2f'%R_rest, '%.2f'%lum_B, '%.2f'%lum_R


## J1323 - 555 and 814
B, R = 21.95, 20.08 # emcee53
z = 0.4641 # scale = 5.921 kpc/"
lum_B, B_rest = MassB2(B,z)
lum_R, R_rest = MassR(R,z)
print 'J1323, source galaxy: ',  '%.2f'%B_rest, '%.2f'%R_rest, '%.2f'%lum_B, '%.2f'%lum_R

## J0901 - 606 and 814
B, R = 22.51, 20.93 # intrinsic magnitudes
z=0.586 # scale = 6.687 kpc/"
lum_B, B_rest = MassB1(B,z)
lum_R, R_rest = MassR(R,z)
print 'J0901, source galaxy: ',  '%.2f'%B_rest, '%.2f'%R_rest, '%.2f'%lum_B, '%.2f'%lum_R

## J0913 - 555 and 814
B, R = 21.71,19.79 # intrinsic magnitudes
z=0.539 # scale = 6.687 kpc/"
lum_B, B_rest = MassB2(B,z)
lum_R, R_rest = MassR(R,z)
print 'J0913, source galaxy: ',  '%.2f'%B_rest, '%.2f'%R_rest, '%.2f'%lum_B, '%.2f'%lum_R

# J0837 - want to know its mass to compare with dust lane!
z = 0.528
B=20.75
lum_B, B_rest = MassB1(B,z)
print 'J0837: ', '%.2f'%B_rest,'%.2f'%lum_B



plot=False
if plot == True:
    ## visualise filters
    sed = tools.getSED('BC_Z=1.0_age=7.000gyr')
    bfilt = tools.filterfromfile('F606W_ACS')
    rfilt = tools.filterfromfile('F814W_ACS')
    kfilt = tools.filterfromfile('Kp_NIRC2')
    pl.figure()
    pl.plot(sed[0],sed[1],'k')
    pl.plot(bfilt[0],bfilt[1]*1e-5,'CornflowerBlue',label='F606W')
    pl.plot(rfilt[0],rfilt[1]*1e-5,'Crimson',label='F814W')
    pl.plot(kfilt[0],kfilt[1]*5e-8,'Orange',label='K')
    pl.xscale('log')
    pl.legend(loc='upper right')
    ## plot redshifted filters - say for the source
    z=0.69
    pl.plot(bfilt[0]/(1.+z),bfilt[1]*1e-5,'Blue',label='F606W')
    pl.plot(rfilt[0]/(1.+z),rfilt[1]*1e-5,'DarkRed',label='F814W')
    pl.plot(kfilt[0]/(1.+z),kfilt[1]*5e-8,'DarkOrange',label='K')
