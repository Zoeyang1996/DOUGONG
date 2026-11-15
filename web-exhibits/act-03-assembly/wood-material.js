import * as THREE from 'three';

// Physical-scale grain maps: longitudinal fibres on the sides, growth rings on end cuts.
// A deterministic seed keeps the asset stable between sessions and thumbnails.
function grainMaps(end = false) {
  const size = 512, canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d'), pixels = ctx.createImageData(size, size);
  const height = document.createElement('canvas'); height.width = height.height = size;
  const hctx = height.getContext('2d'), relief = hctx.createImageData(size, size);
  let seed = 1907;
  const random = () => { seed = (1664525 * seed + 1013904223) >>> 0; return seed / 4294967296; };
  const fibres = Array.from({length:512}, () => random());
  for (let y=0; y<size; y++) for (let x=0; x<size; x++) {
    const u=x/size, v=y/size;
    let wave, fine;
    if(end) {
      const r=Math.hypot((u-.43)*1.1,(v-.51)*.9);
      wave=Math.sin(r*140 + Math.sin(u*17+v*11)*.9);
      fine=Math.sin(r*430+Math.sin(u*30)*.4);
    } else {
      const warp=Math.sin(v*Math.PI*2)*.009+Math.sin(v*Math.PI*4+u*6)*.003;
      wave=Math.sin((u+warp)*85 + Math.sin(u*23)*2.1);
      fine=fibres[((Math.floor((u+warp+1)*512))%512)];
    }
    const pore=random(), line=Math.pow(Math.max(0,wave),9);
    const value=.86-line*.19+(fine-.5)*.075+(pore-.5)*.035;
    const i=(y*size+x)*4;
    // Neutral honey-brown base, varied per timber by material tint.
    pixels.data[i]=Math.min(255,182*value);pixels.data[i+1]=Math.min(255,125*value);pixels.data[i+2]=Math.min(255,76*value);pixels.data[i+3]=255;
    const bump=145-line*48+(fine-.5)*26+(pore-.5)*10;
    relief.data[i]=relief.data[i+1]=relief.data[i+2]=bump;relief.data[i+3]=255;
  }
  ctx.putImageData(pixels,0,0);hctx.putImageData(relief,0,0);
  const map=new THREE.CanvasTexture(canvas),bump=new THREE.CanvasTexture(height);
  map.colorSpace=THREE.SRGBColorSpace;
  for(const t of [map,bump]){t.wrapS=t.wrapT=THREE.RepeatWrapping;t.anisotropy=8;}
  return {map,bump};
}
const side=grainMaps(),end=grainMaps(true);
export function timberMesh(geometry,name) {
  const g=geometry.index?geometry.toNonIndexed():geometry;
  const axis=name.startsWith('context_')?new THREE.Vector3(0,1,0):
    name.startsWith('ang_')?new THREE.Vector3(0,.35,-1).normalize():
    /huagong|shuatou/.test(name)?new THREE.Vector3(0,0,-1):new THREE.Vector3(1,0,0);
  const cross=new THREE.Vector3().crossVectors(axis,Math.abs(axis.y)>.95?new THREE.Vector3(1,0,0):new THREE.Vector3(0,1,0)).normalize();
  const other=new THREE.Vector3().crossVectors(axis,cross).normalize();
  const pos=g.getAttribute('position'),uv=new Float32Array(pos.count*2);
  const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3(),normal=new THREE.Vector3();
  const hash=[...name].reduce((s,c)=>s+c.charCodeAt(0),0),offset=(hash%37)/37;
  g.clearGroups();
  for(let i=0;i<pos.count;i+=3){
    a.fromBufferAttribute(pos,i);b.fromBufferAttribute(pos,i+1);c.fromBufferAttribute(pos,i+2);
    normal.crossVectors(b.clone().sub(a),c.clone().sub(a)).normalize();
    const isEnd=Math.abs(normal.dot(axis))>.78;
    const transverse=Math.abs(normal.dot(cross))>.7?other:cross;
    for(let k=0;k<3;k++){
      a.fromBufferAttribute(pos,i+k);
      uv[(i+k)*2]=(isEnd?a.dot(cross)/.5:a.dot(transverse)/.28)+offset;
      uv[(i+k)*2+1]=(isEnd?a.dot(other)/.5:a.dot(axis)/1.6)+offset;
    }
    g.addGroup(i,3,isEnd?1:0);
  }
  // Two batches per timber keep texture detail affordable on touch-screen GPUs.
  const indices=[[],[]];for(const item of g.groups)for(let j=item.start;j<item.start+item.count;j++)indices[item.materialIndex].push(j);
  g.setIndex([...indices[0],...indices[1]]);g.clearGroups();g.addGroup(0,indices[0].length,0);g.addGroup(indices[0].length,indices[1].length,1);
  g.setAttribute('uv',new THREE.BufferAttribute(uv,2));
  const tint=new THREE.Color().setHSL(.075,.10,.79+(hash%9)*.015);
  const materials=[side,end].map((tex,i)=>new THREE.MeshStandardMaterial({
    map:tex.map,bumpMap:tex.bump,bumpScale:i?.001:.0018,
    roughnessMap:tex.bump,roughness:.95,metalness:0,color:tint.clone().multiplyScalar(i?.86:1),
  }));
  return new THREE.Mesh(g,materials);
}
