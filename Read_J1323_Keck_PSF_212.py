import cPickle,numpy,pyfits as py
import pymc
from pylens import *
from imageSim import SBModels,convolve,SBObjects
import indexTricks as iT
from SampleOpt import AMAOpt
import pylab as pl
import numpy as np
import myEmcee_blobs as myEmcee
from matplotlib.colors import LogNorm
from scipy import optimize
from scipy.interpolate import RectBivariateSpline
import SBBModels, SBBProfiles
'''
X=0 - TO RUN
'''

# plot things
def NotPlicely(image,im,sigma):
    ext = [0,image.shape[0],0,image.shape[1]]
    #vmin,vmax = numpy.amin(image), numpy.amax(image)
    pl.figure()
    pl.subplot(221)
    pl.imshow(image,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',aspect='auto',vmin=0,vmax=560) #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('data')
    pl.subplot(222)
    pl.imshow(im,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',aspect='auto',vmin=0,vmax=560) #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('model')
    pl.subplot(223)
    pl.imshow(image-im,origin='lower',interpolation='nearest',extent=ext,vmin=-50,vmax=50,cmap='afmhot',aspect='auto')
    pl.colorbar()
    pl.title('data-model')
    pl.subplot(224)
    pl.imshow((image-im)/sigma,origin='lower',interpolation='nearest',extent=ext,vmin=-30,vmax=30,cmap='afmhot',aspect='auto')
    pl.title('signal-to-noise residuals')
    pl.colorbar()

def SotPleparately(image,im,sigma,col):
    ext = [0,image.shape[0],0,image.shape[1]]
    pl.figure()
    pl.imshow(image,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',vmin=0,aspect='auto',vmax=800) #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('data - '+str(col))
    pl.figure()
    pl.imshow(im,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',vmin=0,aspect='auto',vmax=800) #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('model - '+str(col))
    pl.figure()
    pl.imshow((image-im)/sigma,origin='lower',interpolation='nearest',extent=ext,vmin=-50,vmax=50,cmap='afmhot',aspect='auto')
    pl.title('signal-to-noise residuals - '+str(col))
    pl.colorbar()


image = py.open('/data/ljo31/Lens/J1323/J1323_nirc2.fits')[0].data.copy()[615:835,855:1090]
sigma = np.ones(image.shape) 
img=image.copy()
sig=sigma.copy()
result = np.load('/data/ljo31/Lens/LensModels/J1323_212')
lp= result[0]
a1,a3 = numpy.unravel_index(lp.argmax(),lp.shape)
trace = result[1]
dic = result[2]

OVRS = 1
yc,xc = iT.overSample(image.shape,OVRS)
yo,xo = iT.overSample(image.shape,1)
xc,xo,yc,yo=xc*0.2,xo*0.2,yc*0.2,yo*0.2
xc,xo,yc,yo = xc+20,xo+20,yc+22,yo+22
mask = np.zeros(image.shape)
tck = RectBivariateSpline(yo[:,0],xo[0],mask)
mask2 = tck.ev(xc,yc)
mask2[mask2<0.5] = 0
mask2[mask2>0.5] = 1
mask2 = mask2==0
mask = mask==0



kresult = np.load('/data/ljo31/Lens/J1323/KeckPSF_final_212')
klp= kresult[0]
ka2=0
ka1,ka3 = numpy.unravel_index(klp[:,0].argmax(),klp[:,0].shape)
ktrace = kresult[1]
kdic = kresult[2]

imgs = [img]
sigs = [sig]

xpsf,ypsf = iT.coords((201,201))-100.
xoffset,yoffset,sig1,q1,pa1,amp1,sig2,q2,pa2,amp2,sig3,q3,pa3,amp3,sig4,q4,pa4,amp4,sig5,q5,pa5,amp5 = ktrace[ka1,ka2,ka3]
amp4=1.-amp1-amp2-amp3
psfObj1 = SBObjects.Gauss('psf 1',{'x':0,'y':0,'sigma':sig1,'q':q1,'pa':pa1,'amp':amp1})
psfObj2 = SBObjects.Gauss('psf 2',{'x':0,'y':0,'sigma':sig2,'q':q2,'pa':pa2,'amp':amp2})
psfObj3 = SBObjects.Gauss('psf 3',{'x':0,'y':0,'sigma':sig3,'q':q3,'pa':pa3,'amp':amp3})
psfObj4 = SBObjects.Gauss('psf 4',{'x':0,'y':0,'sigma':sig4,'q':q4,'pa':pa4,'amp':amp4})
psfObj5 = SBObjects.Gauss('psf 5',{'x':0,'y':0,'sigma':sig5,'q':q5,'pa':pa5,'amp':amp5})

psf1 = psfObj1.pixeval(xpsf,ypsf)  / (np.pi*2.*sig1**2.)
psf2 = psfObj2.pixeval(xpsf,ypsf) / (np.pi*2.*sig2**2.)
psf3 = psfObj3.pixeval(xpsf,ypsf)  / (np.pi*2.*sig3**2.)
psf4 = psfObj4.pixeval(xpsf,ypsf)  / (np.pi*2.*sig4**2.)
psf5 = psfObj5.pixeval(xpsf,ypsf)  / (np.pi*2.*sig5**2.)

psf = psf1 + psf2 + psf3 + psf4 + psf5
#pl.figure()
#pl.imshow(psf1)
#pl.colorbar()
#pl.figure()
#pl.imshow(psf2)
#pl.colorbar()
psf /= psf.sum()
psf = convolve.convolve(img,psf)[1]
PSFs=[psf]

gals = []
for name in ['Galaxy 1', 'Galaxy 2']:
    p = {}
    if name == 'Galaxy 1':
        for key in 'x','y','q','pa','re','n':
            p[key] = dic[name+' '+key][a1,a3]
    elif name == 'Galaxy 2':
        for key in 'q','pa','re','n':
            p[key] = dic[name+' '+key][a1,a3]
        for key in 'x','y':
            p[key] = gals[0].pars[key]
    gals.append(SBModels.Sersic(name,p))

lenses = []
p = {}
for key in 'x','y','q','pa','b','eta':
    p[key] = dic['Lens 1 '+key][a1,a3]
lenses.append(MassModels.PowerLaw('Lens 1',p))
p = {}
p['x'] = lenses[0].pars['x']
p['y'] = lenses[0].pars['y']
p['b'] = dic['extShear'][a1,a3]
p['pa'] = dic['extShear PA'][a1,a3]
lenses.append(MassModels.ExtShear('shear',p))

srcs = []
for name in ['Source 2','Source 1']:
    p = {}
    if name == 'Source 2':
        for key in 'q','re','n','pa':
           p[key] = dic[name+' '+key][a1,a3]
        for key in 'x','y': # subtract lens potition - to be added back on later in each likelihood iteration!
            p[key] = dic[name+' '+key][a1,a3]#+lenses[0].pars[key]
    elif name == 'Source 1':
        for key in 'q','re','n','pa':
           p[key] = dic[name+' '+key][a1,a3]
        for key in 'x','y': # subtract lens potition - to be added back on later in each likelihood iteration!
            #p[key] = dic[name+' '+key][a1,a3]+lenses[0].pars[key]
            p[key] = srcs[0].pars[key]
    srcs.append(SBBModels.Sersic(name,p))


models = []
for i in range(len(imgs)):
    dx = xoffset 
    dy = yoffset 
    xp,yp = xc+dx,yc+dy
    image = imgs[i]
    sigma = sigs[i]
    psf = PSFs[i]
    imin,sigin,xin,yin = image[mask], sigma[mask],xp[mask2],yp[mask2]
    n = 0
    model = np.empty(((len(gals) + len(srcs)+1),imin.size))
    for gal in gals:
        gal.setPars()
        tmp = xc*0.
        tmp[mask2] = gal.pixeval(xin,yin,0.2,csub=11) # evaulate on the oversampled grid. OVRS = number of new pixels per old pixel.
        tmp = iT.resamp(tmp,OVRS,True) # convert it back to original size
        tmp = convolve.convolve(tmp,psf,False)[0]
        model[n] = tmp[mask].ravel()
        n +=1
    for lens in lenses:
        lens.setPars()
    x0,y0 = pylens.lens_images(lenses,srcs,[xin,yin],1./OVRS,getPix=True)
    for src in srcs:
        src.setPars()
        tmp = xc*0.
        tmp[mask2] = src.pixeval(x0,y0,0.2,csub=11)
        tmp = iT.resamp(tmp,OVRS,True)
        tmp = convolve.convolve(tmp,psf,False)[0]
        model[n] = tmp[mask].ravel()
        n +=1
    model[n] = np.ones(model[n-1].size)
    n+=1
    rhs = (imin/sigin) # data
    op = (model/sigin).T # model matrix
    fit, chi = optimize.nnls(op,rhs)
    components = (model.T*fit).T.reshape((n,image.shape[0],image.shape[1]))
    model = components.sum(0)
    SotPleparately(image,model,sigma,'K')
    #for i in range(4):
    #    pl.figure()
    #    pl.imshow(components[i],interpolation='nearest',origin='lower')
    #    pl.colorbar()
    print fit



print r'$\sigma$ & $q$ & $pa$ & amp \\'
print '%.2f'%sig1, '&', '%.2f'%q1,'&','%.2f'%pa1,'&','%.2f'%amp1, r'\\'
print '%.2f'%sig2,'&','%.2f'%q2,'&','%.2f'%pa2,'&','%.2f'%amp2, r'\\'
print '%.2f'%sig3,'&','%.2f'%q3,'&','%.2f'%pa3,'&','%.2f'%amp3, r'\\'
print '%.2f'%sig4,'&','%.2f'%q4,'&', '%.2f'%pa4,'&','%.2f'%amp4, r'\\\hline'

pl.figure()
pl.plot(klp[:,0])
