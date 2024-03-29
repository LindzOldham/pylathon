import cPickle,numpy,pyfits as py
import pymc
from pylens import *
from imageSim import SBModels,convolve
import indexTricks as iT
from SampleOpt import AMAOpt
import pylab as pl
import numpy as np
import myEmcee_blobs as myEmcee
#import myEmcee
from matplotlib.colors import LogNorm
from scipy import optimize
from scipy.interpolate import RectBivariateSpline

''' This code now also calculates the source position relative to the lens rather than relative to the origin. This means that when the lens moves, the source moves with it! I have tested this in so far as it seems to produce the same results on the final inference as before. Should maybe test it on an earlier model incarnation though.'''

'''
X = 0 - an extremely simple model with one of everything. I spent about 5 minutes on it.
X = 1 - with less restriction on the PAs.
X = 2 - model5. This is X=0 put back into the gui and iterated a little bit. Still doesn't look great but we are still only working with single-component models so we can always add a second galaxy if need be!
X = 3 - still model5, but with tighter covariances on everything. We were keeping them big before.
X = 4 - trying to find the other solution from X=0!
X = 5 - model9
X = 6 - mode15
X = 7 - model12 - 2 gals, 1 src
X = 8 - model13 - 2 gals, 1 src
X = 9 - model16. This is emcee0, iterated slightly
X = 10 - model17, with two sources and one galaxy. See what happens...!
X = 11 - model17, but without concentricity conditions
X = 12 - gui_emcee10a. This is emcee10, put back into the gui and iterated a bit, and without requiring the sources to be concentric!
X = 15 - model19uniforms - done with eta = 1, so may want to redo these in NX
X = 16 - model23 - nonconcentric sources, concentric galaxies
X = 17 - model23, concentric sources AND galaxies
X = 18, 19 - singleband
X = 20 - with the new mask of the central blob. We could also just mask one band. Ie. apply different masks to each band. But implement rhis later - see if it makes any difference! Concentric sources and galaxies.
X = 21 - as 20, but with a slightly more extensive mask (mask_edges.fits)
X = 29 - gui7. THis is x=7 put back into the gui and used for both sbands. Using the thorough mask. OVRS = 2 for good measure. RUNNING
X = 30 - model12 again, with OVRS = 2 RUNNING
X = 31 - emcee7, with OVRS = 2. TO RUN
X = 32 - gui7_c with OVRS=2 and masking. RUNNING
X = 33 - gui7_d with OVRS=2 and masking. THe runs in this group all have the two galaxy components moving separately from each other. RUNNING
X = 34 - exactly the same as X=33, only with mask_middler instead of mask_middle. This is a more restrained central mask (made from the noise map rather than the image. Note that the line of noisy pixels exists in BOTH filters.) And masking BOTH filters as a result of this observation. RUBBISH.
### readboth :
X=37 - emcee30 (best model so far!) but using a noisemap4 for the F814W band. This has reduced the noise on the source blob. RUNNING
X=38 - as above, but with a flat noisemap in both bands. RUNNING
X - 39 - as 30, but with noisemapedited3. This has less noise on source and more noise on bad pixels in galaxy.
###
X = 40 - gui30buniforms. Not masking the central gal as this always leads to badness. But OVRS=2.
X = 41 - gui30euniforms. OVRS=2. Most promise.
X = 42 - gui30cuniforms.
X = 42 - gui_7c with no masking and with OVRS=2.
X = 43 - gui_7d with no masking and with OVRS=2.
X = 44 - gui38d. Putting two sources in. This may not go too well... OVRS=2, no extraneous masking. Letting the sources move independently for now.
X = 45 - GUI38b. The second source has almost zero flux, so I'm not sure if this is going to help or not!
X = 46 - gui383. One source again - basically, 38 iterated.
X = 47 - gui38good. Two sources, trying to make the second one smaller than the first (with questonable success)!
X = 48 - gui38good4. Both sources do seem to be contributing atm!
X = 49 - gui38good5
X = 50 - gui38good5, with concentric sources. Trying to force a solution with a smaller second source!!!!
X = 51 - gui38good4, with concentric sources. OVRS = 3.
X = 52 - gui38_5. With small and large sources which aren't very well fitted. Use more walkers (80?). OVRS=3. Concentric sources.
X = 53 - gui38_7. As above.
X = 55 - gui38_3galsuniform. Added a third intermediate-size galaxy as a last-ditch attempt to improve les resids.
X = 56 - another 3gals attempt. See if they return the same solution or not - I tried a different thing in the gui so they could be different.
'''

### non-concentric sources!

X = 56
print X

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

img1 = py.open('/data/ljo31/Lens/J0901/F606W_sci_cutout.fits')[0].data.copy()
sig1 = py.open('/data/ljo31/Lens/J0901/F606W_noisemap.fits')[0].data.copy()
psf1 = py.open('/data/ljo31/Lens/J0901/F606W_psf2.fits')[0].data.copy()
psf1 = psf1[5:-6,5:-6]
psf1 = psf1/np.sum(psf1)

img2 = py.open('/data/ljo31/Lens/J0901/F814W_sci_cutout.fits')[0].data.copy()
sig2 = py.open('/data/ljo31/Lens/J0901/F814W_noisemap.fits')[0].data.copy()
psf2 = py.open('/data/ljo31/Lens/J0901/F814W_psf2.fits')[0].data.copy()
psf2 = psf2[4:-6,3:-6]
psf2 = psf2/np.sum(psf2)

guiFile = '/data/ljo31/Lens/J0901/gui38_3galsuniformb'

print guiFile

imgs = [img1,img2]
sigs = [sig1,sig2]
psfs = [psf1,psf2]

PSFs = []
OVRS = 2
yc,xc = iT.overSample(img1.shape,OVRS)
yo,xo = iT.overSample(img1.shape,1)
#mask = np.ones(img1.shape)
mask = py.open('/data/ljo31/Lens/J0901/mask.fits')[0].data.copy()
tck = RectBivariateSpline(xo[0],yo[:,0],mask)
mask2 = tck.ev(xc,yc)
mask2[mask2<0.5] = 0
mask2[mask2>0.5] = 1
mask2 = mask2.T
mask2 = mask2==1
mask = mask==1


for i in range(len(imgs)):
    psf = psfs[i]
    image = imgs[i]
    psf /= psf.sum()
    psf = convolve.convolve(image,psf)[1]
    PSFs.append(psf)

G,L,S,offsets,shear = numpy.load(guiFile)

pars = []
cov = []
### first parameters need to be the offsets
xoffset =  offsets[0][3]
yoffset = offsets[1][3]
pars.append(pymc.Uniform('xoffset',-5.,5.,value=xoffset))
pars.append(pymc.Uniform('yoffset',-5.,5.,value=yoffset))
cov += [0.4,0.4]

gals = []
for name in G.keys():
    s = G[name]
    p = {}
    if name == 'Galaxy 1':
        for key in 'x','y','q','pa','re','n':
            lo,hi,val = s[key]['lower'],s[key]['upper'],s[key]['value']
            pars.append(pymc.Uniform('%s %s'%(name,key),lo,hi,value=val))
            p[key] = pars[-1]
            cov.append(s[key]['sdev']*10)
    elif name == 'Galaxy 2':
        for key in 'x','y','q','pa','re','n':
            if s[key]['type']=='constant':
                p[key] = s[key]['value']
            else:
                lo,hi,val = s[key]['lower'],s[key]['upper'],s[key]['value']
                if key == 're':
                    pars.append(pymc.Uniform('%s %s'%(name,key),lo,hi,value=val))
                else:
                    pars.append(pymc.Uniform('%s %s'%(name,key),lo,hi,value=val))
                p[key] = pars[-1]
                cov.append(s[key]['sdev']*1)
    elif name == 'Galaxy 3':
        for key in 'x','y','q','pa','re','n':
            if s[key]['type']=='constant':
                p[key] = s[key]['value']
            else:
                lo,hi,val = s[key]['lower'],s[key]['upper'],s[key]['value']
                pars.append(pymc.Uniform('%s %s'%(name,key),lo,hi,value=val))
                p[key] = pars[-1]
                cov.append(s[key]['sdev']*1)
        #for key in 'x','y':
        #    p[key] = gals[0].pars[key]
    gals.append(SBModels.Sersic(name,p))


lenses = []
for name in L.keys():
    s = L[name]
    p = {}
    for key in 'x','y','q','pa','b','eta':
        lo,hi,val = s[key]['lower'],s[key]['upper'],s[key]['value']
        pars.append(pymc.Uniform('%s %s'%(name,key),lo,hi,value=val))
        cov.append(s[key]['sdev']*1)
        p[key] = pars[-1]
    lenses.append(MassModels.PowerLaw(name,p))
p = {}
p['x'] = lenses[0].pars['x']
p['y'] = lenses[0].pars['y']
pars.append(pymc.Uniform('extShear',-0.3,0.3,value=shear[0]['b']['value']))
cov.append(1)
p['b'] = pars[-1]
pars.append(pymc.Uniform('extShear PA',-180.,180,value=shear[0]['pa']['value']))
cov.append(100.)
p['pa'] = pars[-1]
lenses.append(MassModels.ExtShear('shear',p))

srcs = []
for name in S.keys():
    s = S[name]
    p = {}
    if name == 'Source 1':
        print name
        for key in 'q','re','n','pa':
           lo,hi,val = s[key]['lower'],s[key]['upper'],s[key]['value']
           if key == 're':
               pars.append(pymc.Uniform('%s %s'%(name,key),0.1,hi,value=val))
           elif key == 'n':
               pars.append(pymc.Uniform('%s %s'%(name,key),0.1,hi,value=val))
           elif key == 'pa':
               pars.append(pymc.Uniform('%s %s'%(name,key),lo,hi,value=val))
           else:
               pars.append(pymc.Uniform('%s %s'%(name,key),lo,hi,value=val))
           p[key] = pars[-1]
           if key == 'pa':
               cov.append(s[key]['sdev']*100) 
           elif key == 're':
               cov.append(s[key]['sdev']*10) 
           else:
               cov.append(s[key]['sdev']*10)
        for key in 'x','y': # subtract lens potition - to be added back on later in each likelihood iteration!
            lo,hi,val = s[key]['lower'],s[key]['upper'],s[key]['value']
            #print key, '= ', val
            lo,hi = lo - lenses[0].pars[key].value.item(), hi - lenses[0].pars[key].value.item()
            val = val - lenses[0].pars[key].value.item()
            pars.append(pymc.Uniform('%s %s'%(name,key),lo-1 ,hi+1,value=val ))   # the parameter is the offset between the source centre and the lens (in source plane obvs)
            p[key] = pars[-1] + lenses[0].pars[key] # the source is positioned at the sum of the lens position and the source offset, both of which have uniformly distributed priors.
            #print p[key]
            cov.append(s[key]['sdev'])
    elif name == 'Source 2':
        print name
        for key in 'q','re','n','pa':
            lo,hi,val = s[key]['lower'],s[key]['upper'],s[key]['value']
            if key == 're':
                pars.append(pymc.Uniform('%s %s'%(name,key),0.1,hi,value=val))
            elif key == 'n':
               pars.append(pymc.Uniform('%s %s'%(name,key),0.1,hi,value=val))
            else:
                pars.append(pymc.Uniform('%s %s'%(name,key),lo,hi,value=val))
            p[key] = pars[-1]
            if key == 'pa':
                cov.append(s[key]['sdev']*100) 
            else:
                cov.append(s[key]['sdev']*10)
        for key in 'x','y':
            p[key] = srcs[0].pars[key]
    srcs.append(SBModels.Sersic(name,p))

npars = []
for i in range(len(npars)):
    pars[i].value = npars[i]

@pymc.deterministic
def logP(value=0.,p=pars):
    lp = 0.
    models = []
    for i in range(len(imgs)):
        if i == 0:
            dx,dy = 0,0
        else:
            dx = pars[0].value 
            dy = pars[1].value 
        xp,yp = xc+dx,yc+dy
        image = imgs[i]
        sigma = sigs[i]
        psf = PSFs[i]
        imin,sigin,xin,yin = image[mask], sigma[mask],xp[mask2],yp[mask2]
        n = 0
        model = np.empty(((len(gals) + len(srcs)),imin.size))
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
        rhs = (imin/sigin) # data
        op = (model/sigin).T # model matrix
        fit, chi = optimize.nnls(op,rhs)
        model = (model.T*fit).sum(1)
        resid = (model-imin)/sigin
        lp += -0.5*(resid**2.).sum()
        models.append(model)
    return lp #,models
 
  
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

S = myEmcee.PTEmcee(pars+[likelihood],cov=optCov,nthreads=10,nwalkers=80,ntemps=4)
S.sample(1000)
outFile = '/data/ljo31/Lens/J0901/emcee'+str(X)
f = open(outFile,'wb')
cPickle.dump(S.result(),f,2)
f.close()
result = S.result()
lp = result[0]
trace = numpy.array(result[1])
a1,a2,a3 = numpy.unravel_index(lp.argmax(),lp.shape)
for i in range(len(pars)):
    pars[i].value = trace[a1,a2,a3,i]
    print "%18s  %8.3f"%(pars[i].__name__,pars[i].value)

jj=0
for jj in range(12):
    S = myEmcee.PTEmcee(pars+[likelihood],cov=optCov,nthreads=10,nwalkers=80,ntemps=4,initialPars=trace[a1])
    S.sample(1000)

    outFile = '/data/ljo31/Lens/J0901/emcee'+str(X)
    f = open(outFile,'wb')
    cPickle.dump(S.result(),f,2)
    f.close()

    result = S.result()
    lp = result[0]

    trace = numpy.array(result[1])
    a1,a2,a3 = numpy.unravel_index(lp.argmax(),lp.shape)
    for i in range(len(pars)):
        pars[i].value = trace[a1,a2,a3,i]
    print jj
    jj+=1




## now we need to interpret these resultaeten
logp,coeffs,dic,vals = result
ii = np.where(logp==np.amax(logp))
#coeff = coeffs[ii][0]

colours = ['F555W', 'F814W']
#mods = S.blobs
models = []
for i in range(len(imgs)):
    #mod = mods[i]
    #models.append(mod[a1,a2,a3])
    if i == 0:
        dx,dy = 0,0
    else:
        dx = pars[0].value 
        dy = pars[1].value 
    xp,yp = xc+dx,yc+dy
    xop,yop = xo+dy,yo+dy
    image = imgs[i]
    sigma = sigs[i]
    psf = PSFs[i]
    imin,sigin,xin,yin = image.flatten(), sigma.flatten(),xp.flatten(),yp.flatten()
    n = 0
    model = np.empty(((len(gals) + len(srcs)),imin.size))
    for gal in gals:
        gal.setPars()
        tmp = xc*0.
        tmp = gal.pixeval(xp,yp,1./OVRS,csub=1) # evaulate on the oversampled grid. OVRS = number of new pixels per old pixel.
        tmp = iT.resamp(tmp,OVRS,True) # convert it back to original size
        tmp = convolve.convolve(tmp,psf,False)[0]
        model[n] = tmp.ravel()
        n +=1
    for lens in lenses:
        lens.setPars()
    x0,y0 = pylens.lens_images(lenses,srcs,[xp,yp],1./OVRS,getPix=True)
    for src in srcs:
        src.setPars()
        tmp = xc*0.
        tmp = src.pixeval(x0,y0,1./OVRS,csub=1)
        tmp = iT.resamp(tmp,OVRS,True)
        tmp = convolve.convolve(tmp,psf,False)[0]
        model[n] = tmp.ravel()
        n +=1
    rhs = (imin/sigin) # data
    op = (model/sigin).T # model matrix
    fit, chi = optimize.nnls(op,rhs)
    components = (model.T*fit).T.reshape((n,image.shape[0],image.shape[1]))
    model = components.sum(0)
    models.append(model)
    NotPlicely(image,model,sigma)
    pl.suptitle(str(colours[i]))
    pl.show()

pl.figure()
for i in range(4):
    pl.plot(lp[:,i,:])
pl.show()
