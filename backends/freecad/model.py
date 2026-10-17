"""Own public-API model generator, executed only inside independent FreeCAD."""
import os,json,math,traceback
from pathlib import Path
import FreeCAD as App
import Part
req=json.loads(Path(os.environ['CADCRAFT_SOLID_REQUEST']).read_text())
out=Path(req['directory']);dims=req['dimensions'];kind=req['kind']
try:
    doc=App.newDocument('SolidModel')
    params=doc.addObject('App::FeaturePython','Dimensions');params.Label='模型尺寸（毫米）'
    for key,value in dims.items():
        typ='App::PropertyInteger' if key=='balls' else 'App::PropertyLength'
        params.addProperty(typ,key,'Dimensions');setattr(params,key,value)
    parts=[]
    def cylinder(name,radius,height,z=0):
        obj=doc.addObject('Part::Cylinder',name);obj.Radius=radius;obj.Height=height
        obj.Placement.Base=App.Vector(0,0,z);return obj
    def cut(name,base,tool):
        obj=doc.addObject('Part::Cut',name);obj.Base=base;obj.Tool=tool;return obj
    def ring(name,outer,inner,height,z):
        return cut(name,cylinder(name+'Outside',outer,height,z),cylinder(name+'Bore',inner,height+2,z-1))
    if kind=='bearing':
        od,ind,w,n,r,p=(dims[k] for k in ('outerDiameter','innerDiameter','width','balls','ballRadius','pitchRadius'))
        groove=doc.addObject('Part::Torus','RaceGroove');groove.Radius1=p;groove.Radius2=r+.03
        inner=cut('InnerRace',ring('InnerRing',p-r*.6,ind/2,w,-w/2),groove);inner.Label='内圈'
        outer=cut('OuterRace',ring('OuterRing',od/2,p+r*.6,w,-w/2),groove);outer.Label='外圈'
        parts=[inner,outer]
        ballobjs=[];holes=[]
        for i in range(n):
            center=App.Vector(p*math.cos(i*math.tau/n),p*math.sin(i*math.tau/n),0)
            obj=doc.addObject('Part::Sphere',f'Ball{i+1:02}');obj.Label=f'滚珠 {i+1:02}';obj.Radius=r;obj.Placement.Base=center
            ballobjs.append(obj)
            hole=doc.addObject('Part::Sphere',f'CagePocket{i+1:02}');hole.Radius=r+.2;hole.Placement.Base=center;holes.append(hole)
        parts.extend(ballobjs)
        cage=ring('CageRing',p+r*.42,p-r*.42,r*2.05,-r*.63)
        for i,hole in enumerate(holes):cage=cut(f'CageCut{i+1:02}',cage,hole)
        cage.Label='保持架';parts.append(cage)
    elif kind=='box':
        obj=doc.addObject('Part::Box','Box');obj.Length=dims['length'];obj.Width=dims['width'];obj.Height=dims['height'];parts=[obj]
    elif kind=='cylinder':parts=[cylinder('Cylinder',dims['radius'],dims['height'])]
    else:
        obj=doc.addObject('Part::Sphere','Sphere');obj.Radius=dims['radius'];parts=[obj]
    doc.recompute()
    verified=[]
    for obj in parts:
        shape=obj.Shape
        if shape.isNull() or not shape.isValid() or len(shape.Solids)!=1 or not shape.isClosed() or shape.Volume<=0:
            raise RuntimeError(f'{obj.Name} 不是单一有效封闭实体')
        verified.append({'name':obj.Label,'valid':True,'closed':True,'solids':1,'volumeMM3':shape.Volume})
    compound=Part.makeCompound([obj.Shape for obj in parts]);bounds=compound.BoundBox
    step=out/'模型.step';fcstd=out/'模型.FCStd'
    Part.export(parts,str(step))
    restored=Part.Shape();restored.read(str(step))
    if not restored.isValid() or len(restored.Solids)!=len(parts) or any(not s.isClosed() or s.Volume<=0 for s in restored.Solids):
        raise RuntimeError('STEP 回读验证失败')
    expected_volume=sum(x['volumeMM3'] for x in verified)
    if abs(restored.Volume-expected_volume)>max(1e-5,expected_volume*1e-4):raise RuntimeError(f'STEP 回读体积不一致：{expected_volume} -> {restored.Volume}；差值 {abs(restored.Volume-expected_volume)}')
    step_bounds=restored.BoundBox
    if max(abs(a-b) for a,b in zip((bounds.XLength,bounds.YLength,bounds.ZLength),(step_bounds.XLength,step_bounds.YLength,step_bounds.ZLength)))>1e-5:raise RuntimeError('STEP 回读边界尺寸不一致')
    doc.saveAs(str(fcstd))
    result={'ok':True,'result':{'backend':'FreeCAD','kind':kind,'units':'mm','dimensions':dims,'fcstd':str(fcstd),'step':str(step),'solids':len(parts),'volumeMM3':expected_volume,'boundsMM':[bounds.XLength,bounds.YLength,bounds.ZLength],'valid':True,'closed':True,'stepRoundtripValid':True,'stepVolumeRelativeDifference':abs(restored.Volume-expected_volume)/expected_volume,'stepVolumeRelativeTolerance':1e-4,'components':verified,'visibleObjects':[obj.Name for obj in parts]}}
    (out/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    App.closeDocument(doc.Name)
except Exception as e:
    (out/'result.json').write_text(json.dumps({'ok':False,'error':str(e),'traceback':traceback.format_exc()},ensure_ascii=False,indent=2))
