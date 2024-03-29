import cPickle,numpy,pyfits as py
import pymc
from pylens import *
from imageSim import SBModels,convolve,SBObjects
import indexTricks as iT
from SampleOpt import AMAOpt
import pylab as pl
import numpy as np
import myEmcee_blobs as myEmcee
#import myEmcee
from matplotlib.colors import LogNorm
from scipy import optimize
from scipy.interpolate import RectBivariateSpline

'''
X=0 - alles.
X=1 - q2 fixed.
X=2 - good. q2,pa2 fixed; allowing sig2 to go smaller
X=3 - adding a third component to X=2 which we hope to be much bigger. Not using a huge stamp for the psf because for that, we'd need to make the image stamp bigger as well. This can be our next step.
'''
X = 3

# plot things
def NotPlicely(image,im,sigma):
    ext = [0,image.shape[0],0,image.shape[1]]
    #vmin,vmax = numpy.amin(image), numpy.amax(image)
    pl.figure()
    pl.subplot(221)
    pl.imshow(image,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',aspect='auto',vmin=0) #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('data')
    pl.subplot(222)
    pl.imshow(im,origin='lower',interpolation='nearest',extent=ext,cmap='afmhot',aspect='auto',vmin=0) #,vmin=vmin,vmax=vmax)
    pl.colorbar()
    pl.title('model')
    pl.subplot(223)
    pl.imshow(image-im,origin='lower',interpolation='nearest',extent=ext,vmin=-0.25,vmax=0.25,cmap='afmhot',aspect='auto')
    pl.colorbar()
    pl.title('data-model')
    pl.subplot(224)
    pl.imshow((image-im)/sigma,origin='lower',interpolation='nearest',extent=ext,vmin=-5,vmax=5,cmap='afmhot',aspect='auto')
    pl.title('signal-to-noise residuals')
    pl.colorbar()
    #pl.suptitle(str(V))
    #pl.savefig('/data/ljo31/Lens/TeXstuff/plotrun'+str(X)+'.png')

image = py.open('/data/ljo31/Lens/J1144/J1144_Kp_narrow_cutout.fits')[0].data.copy()
sigma = np.ones(image.shape)
guiFile = '/data/ljo31/Lens/J1144/FINAL_1src_30'

OVRS = 1
yc,xc = iT.overSample(image.shape,OVRS)
yo,xo = iT.overSample(image.shape,1)
xc,xo,yc,yo=xc*0.2,xo*0.2,yc*0.2,yo*0.2
xc,xo = xc+12 , xo+12 
yc,yo = yc+20 , yo+20 
mask = np.zeros(image.shape)
tck = RectBivariateSpline(yo[:,0],xo[0],mask)
mask2 = tck.ev(xc,yc)
mask2[mask2<0.5] = 0
mask2[mask2>0.5] = 1
mask2 = mask2==0
mask = mask==0


G,L,S,offsets,shear = numpy.load(guiFile)
pars = []
cov = []
### first parameters need to be the offsets
pars.append(pymc.Uniform('xoffset',-5.,5.,value=0))
pars.append(pymc.Uniform('yoffset',-5.,5.,value=0))
cov += [0.4,0.4]
pars.append(pymc.Uniform('sigma 1',0,8,value=4))
cov += [5]
pars.append(pymc.Uniform('q 1',0,1,value=0.7))
cov += [1]
pars.append(pymc.Uniform('pa 1',-180,180,value= 90 ))
cov += [50]
pars.append(pymc.Uniform('amp 1',0,1,value=0.7))
cov += [4]
pars.append(pymc.Uniform('sigma 2',10,400,value= 100 )) 
cov += [40]
pars.append(pymc.Uniform('amp 2',0,1,value=0.3))
cov += [4]
pars.append(pymc.Uniform('sigma 3',10,600,value= 400 )) 
cov += [40]


#xpsf,ypsf = iT.coords((310,310))-165
xpsf,ypsf = iT.coords((340,340))-170

# now define two psfs, one huge and one small

gals = []
for name in G.keys():
    s = G[name]
    p = {}
    if name == 'Galaxy 1':
        for key in 'x','y','q','pa','re','n':
            p[key] =s[key]['value']
    elif name == 'Galaxy 2':
        for key in 'q','pa','re','n':
            p[key] =s[key]['value']
        for key in 'x','y':
            p[key]=gals[0].pars[key]
    gals.append(SBModels.Sersic(name,p))


lenses = []
for name in L.keys():
    s = L[name]
    p = {}
    for key in 'x','y','q','pa','b','eta':
        p[key] =s[key]['value']
    lenses.append(MassModels.PowerLaw(name,p))
p = {}
p['x'] = lenses[0].pars['x']
p['y'] = lenses[0].pars['y']
p['b'] = shear[0]['b']['value']
p['pa'] = shear[0]['pa']['value']
lenses.append(MassModels.ExtShear('shear',p))


srcs = []
for name in S.keys():
    s = S[name]
    p = {}
    if name == 'Source 1':
        print name
        for key in 'q','re','n','pa':
            p[key] =s[key]['value']
        for key in 'x','y':
            p[key] = s[key]['value']
    srcs.append(SBModels.Sersic(name,p))

npars = []
for i in range(len(npars)):
    pars[i].value = npars[i]



@pymc.deterministic
def logP(value=0.,p=pars):
    lp = 0.
    models = []
    dx = pars[0].value
    dy = pars[1].value 
    xp,yp = xc+dx,yc+dy
    sig1 = pars[2].value.item()
    q1 = pars[3].value.item()
    pa1 = pars[4].value.item()
    amp1 = pars[5].value.item()
    sig2 = pars[6].value.item()
    q2 = 1.#pars[7].value.item()
    pa2 = 0#pars[7].value.item()
    amp2 = pars[7].value.item()
    sig3 = pars[8].value.item()
    q3,pa3 = 1.,0.
    amp3 = 1.-amp1-amp2
    psfObj1 = SBObjects.Gauss('psf 1',{'x':0,'y':0,'sigma':sig1,'q':q1,'pa':pa1,'amp':10})
    psfObj2 = SBObjects.Gauss('psf 2',{'x':0,'y':0,'sigma':sig2,'q':q2,'pa':pa2,'amp':10})
    psfObj3 = SBObjects.Gauss('psf 3',{'x':0,'y':0,'sigma':sig3,'q':q3,'pa':pa3,'amp':10})
    psf1 = psfObj1.pixeval(xpsf,ypsf) * amp1 / (np.pi*2.*sig1**2.)
    psf2 = psfObj2.pixeval(xpsf,ypsf) * amp2 / (np.pi*2.*sig2**2.)
    psf3 = psfObj3.pixeval(xpsf,ypsf) * amp3 / (np.pi*2.*sig3**2.)
    psf = psf1 + psf2 + psf3
    psf /= psf.sum()
    psf = convolve.convolve(image,psf)[1]
    imin,sigin,xin,yin = image[mask], sigma[mask],xp[mask2],yp[mask2]
    n = 0
    model = np.empty(((len(gals) + len(srcs)+1),imin.size))
    for gal in gals:
        gal.setPars()
        tmp = xc*0.
        tmp[mask2] = gal.pixeval(xin,yin,1./OVRS,csub=1) # evaulate on the oversampled grid. OVRS = number of new pixels per old pixel.
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
        tmp[mask2] = src.pixeval(x0,y0,1./OVRS,csub=1)
        tmp = iT.resamp(tmp,OVRS,True)
        tmp = convolve.convolve(tmp,psf,False)[0]
        model[n] = tmp[mask].ravel()
        n +=1
    model[n] = np.ones(model[n-1].shape)
    rhs = (imin/sigin) # data
    op = (model/sigin).T # model matrix
    fit, chi = optimize.nnls(op,rhs)
    model = (model.T*fit).sum(1)
    resid = (model-imin)/sigin
    lp = -0.5*(resid**2.).sum()
    return lp 
 
  
@pymc.observed
def likelihood(value=0.,lp=logP):
    return lp #[0]

def resid(p):
    lp = -2*logP.value
    return self.imgs[0].ravel()*0 + lp

optCov = None
if optCov is None:
    optCov = numpy.array(cov)

print len(cov), len(pars)


S = myEmcee.PTEmcee(pars+[likelihood],cov=optCov,nwalkers=50,nthreads=5,ntemps=3)
S.sample(500)

outFile = '/data/ljo31/Lens/J1144/KeckPSF_'+str(X)
f = open(outFile,'wb')
cPickle.dump(S.result(),f,2)
f.close()

result = S.result()
lp = result[0]
trace = numpy.array(result[1])
a2=0
a1,a3 = numpy.unravel_index(lp[:,0].argmax(),lp[:,0].shape)
for i in range(len(pars)):
    pars[i].value = trace[a1,a2,a3,i]
    print "%18s  %8.3f"%(pars[i].__name__,pars[i].value)

jj=0
for jj in range(10):
    S = myEmcee.PTEmcee(pars+[likelihood],cov=optCov,nthreads=5,nwalkers=50,ntemps=3,initialPars=trace[-1])
    S.sample(500)

    outFile = '/data/ljo31/Lens/J1144/KeckPSF_'+str(X)
    f = open(outFile,'wb')
    cPickle.dump(S.result(),f,2)
    f.close()

    result = S.result()
    lp = result[0]

    trace = numpy.array(result[1])
    a1,a3 = numpy.unravel_index(lp[:,0].argmax(),lp[:,0].shape)
    for i in range(len(pars)):
        pars[i].value = trace[a1,a2,a3,i]
    print jj
    jj+=1


