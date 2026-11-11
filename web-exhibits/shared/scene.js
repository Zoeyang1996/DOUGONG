import * as THREE from 'three';
import {OrbitControls} from './vendor/OrbitControls.js';
import {GLTFLoader} from './vendor/GLTFLoader.js';
export {THREE,OrbitControls};
export function stage(host,{dark=false,orbit=true}={}){
 const scene=new THREE.Scene(),camera=new THREE.PerspectiveCamera(35,1,.01,300);camera.position.set(4,3,6);
 const renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});renderer.setPixelRatio(Math.min(devicePixelRatio,2));renderer.outputColorSpace=THREE.SRGBColorSpace;renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;host.append(renderer.domElement);
 scene.add(new THREE.HemisphereLight(dark?0xaacddd:0xfff3da,dark?0x183545:0x736856,2.5));const sun=new THREE.DirectionalLight(0xffe3bb,4);sun.position.set(4,6,5);scene.add(sun);const rim=new THREE.DirectionalLight(0xffffff,2);rim.position.set(-4,3,-2);scene.add(rim);
 const controls=orbit?new OrbitControls(camera,renderer.domElement):null;if(controls){controls.enableDamping=true;controls.enablePan=false;controls.minDistance=2;controls.maxDistance=12;}
 new ResizeObserver(()=>{const w=host.clientWidth,h=host.clientHeight;if(!w||!h)return;renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix()}).observe(host);
 const updates=[];renderer.setAnimationLoop(t=>{controls?.update();updates.forEach(fn=>fn(t));renderer.render(scene,camera)});
 return {scene,camera,renderer,controls,updates};
}
export async function model(file){return (await new GLTFLoader().loadAsync('../shared/models/'+file)).scene;}
export function normalize(root,size=3){const box=new THREE.Box3().setFromObject(root),center=box.getCenter(new THREE.Vector3()),extent=box.getSize(new THREE.Vector3());const s=size/Math.max(extent.x,extent.y,extent.z);root.position.sub(center);const group=new THREE.Group();group.add(root);group.scale.setScalar(s);return group;}
export function fail(host,error){console.error(error);const el=document.createElement('p');el.className='error';el.textContent='三维素材暂未载入，请从本地预览地址打开页面。';host.append(el)}
export function pick(event,host,camera,objects){const r=host.getBoundingClientRect(),p=new THREE.Vector2((event.clientX-r.left)/r.width*2-1,-(event.clientY-r.top)/r.height*2+1),ray=new THREE.Raycaster();ray.setFromCamera(p,camera);return ray.intersectObjects(objects,true)[0];}
