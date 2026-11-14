"""Local shape candidate ranking against KanjiVG; not a linguistic/handwriting OCR model."""
import math
import numpy as np
from scipy.ndimage import distance_transform_edt
from PIL import Image, ImageDraw
from scipy.optimize import linear_sum_assignment
from .common import ROOT,read_json

SIZE=64


def validate_strokes(strokes):
    if not isinstance(strokes,list) or not 1<=len(strokes)<=64:
        raise ValueError('Mỗi ô cần từ 1 đến 64 nét viết.')
    for stroke in strokes:
        if not isinstance(stroke,list) or not 1<=len(stroke)<=1024:
            raise ValueError('Nét viết không hợp lệ hoặc quá dài.')
        for point in stroke:
            if (not isinstance(point,list) or len(point)!=2
                or any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not 0<=v<=256 for v in point)):
                raise ValueError('Tọa độ nét viết không hợp lệ.')
    return strokes


def normalized_paths(strokes):
    all_points=np.array([p for stroke in strokes for p in stroke],dtype=float)
    lo=all_points.min(axis=0);hi=all_points.max(axis=0)
    scale=48/max(float((hi-lo).max()),1)
    offset=(np.array([SIZE-1,SIZE-1])-(hi-lo)*scale)/2
    paths=[]
    for stroke in strokes:
        points=(np.array(stroke,dtype=float)-lo)*scale+offset
        arc=np.concatenate([[0],np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))])
        if arc[-1]<1e-6:paths.append(np.repeat(points[:1],16,axis=0));continue
        grid=np.linspace(0,arc[-1],16)
        paths.append(np.stack([np.interp(grid,arc,points[:,i]) for i in range(2)],axis=1))
    return np.stack(paths)


def raster(strokes):
    points=np.array([p for stroke in strokes for p in stroke],dtype=float)
    lo=points.min(axis=0);hi=points.max(axis=0)
    span=float((hi-lo).max())
    if span<1:raise ValueError('Hãy viết rõ hơn một dấu chấm trước khi nhận dạng.')
    scale=48/span
    offset=(np.array([SIZE-1,SIZE-1])-(hi-lo)*scale)/2
    image=Image.new('1',(SIZE,SIZE),0)
    draw=ImageDraw.Draw(image)
    for stroke in strokes:
        xy=[tuple(p) for p in ((np.array(stroke)-lo)*scale+offset)]
        if len(xy)==1:
            x,y=xy[0];draw.ellipse((x-1,y-1,x+1,y+1),fill=1)
        else:draw.line(xy,fill=1,width=2,joint='curve')
    return np.asarray(image,dtype=bool)


class HandwritingMatcher:
    def __init__(self,path=None):
        self.data=read_json(path or ROOT/'data/handwriting/templates.json')
        self.references=self.data['characters']
        self.masks=np.stack([raster(r['strokes']) for r in self.references])
        self.distances=np.stack([distance_transform_edt(~m) for m in self.masks])
        self.counts=np.array([len(r['strokes']) for r in self.references])
        self.paths=[normalized_paths(r['strokes']) for r in self.references]
        self.ink=self.masks.sum(axis=(1,2))
        self.xprojections=self.masks.mean(axis=1)
        self.yprojections=self.masks.mean(axis=2)

    def recognize(self,strokes,limit=8,allowed=None):
        validate_strokes(strokes)
        mask=raster(strokes)
        observed_distance=distance_transform_edt(~mask)
        # Symmetric chamfer: tolerant of small drift, added/missing strokes and stroke order.
        forward=self.distances[:,mask].mean(axis=1)
        backward=(self.masks*observed_distance).sum(axis=(1,2))/self.ink
        count_loss=np.abs(self.counts-len(strokes))/np.maximum(self.counts,len(strokes))
        projection=(np.abs(self.xprojections-mask.mean(axis=0)[None,:]).mean(axis=1)
                    +np.abs(self.yprojections-mask.mean(axis=1)[None,:]).mean(axis=1))
        # Axis projections are weak evidence; geometry dominates, count is a soft tie-breaker.
        observed_paths=normalized_paths(strokes)
        stroke_losses=[]
        for reference in self.paths:
            delta=observed_paths[:,None,:,:]-reference[None,:,:,:]
            reversed_delta=observed_paths[:,None,:,:]-reference[None,:,::-1,:]
            cost=np.minimum(np.linalg.norm(delta,axis=-1).mean(axis=-1),
                            np.linalg.norm(reversed_delta,axis=-1).mean(axis=-1))
            row,col=linear_sum_assignment(cost)
            stroke_losses.append(float(cost[row,col].mean()))
        losses=0.55*(forward+backward)/2 + 0.45*np.array(stroke_losses) + 4.0*count_loss + 0.25*projection
        ranked=np.argsort(losses)
        if allowed is not None:ranked=[i for i in ranked if self.references[i]['kanji'] in allowed]
        out=[{'kanji':self.references[i]['kanji'],'shape_distance':round(float(losses[i]),4),
              'reference_strokes':int(self.counts[i])} for i in list(ranked)[:limit]]
        return {'candidates':out,'input_strokes':len(strokes),
                'uncertain':not out or out[0]['shape_distance']>2.4,
                'method':'KanjiVG geometric similarity; candidates, not an assertion of correctness.'}
