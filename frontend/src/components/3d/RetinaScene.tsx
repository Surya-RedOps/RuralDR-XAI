import { useRef, useEffect, useMemo } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { PerspectiveCamera, OrbitControls, SpotLight } from '@react-three/drei';
import * as THREE from 'three';

/**
 * Anatomically Realistic Retina Mesh
 * Creates a spherical retina with realistic blood vessel branching, texture, and medical accuracy
 */
function RetinaMesh() {
  const meshRef = useRef<THREE.Mesh>(null);
  const bloodVesselsRef = useRef<THREE.LineSegments>(null);
  const particlesRef = useRef<THREE.Points>(null);
  const lightRef = useRef<THREE.PointLight>(null);
  useFrame((state) => {
    const elapsed = state.clock.getElapsedTime();

    if (meshRef.current) {
      meshRef.current.rotation.x = Math.sin(elapsed * 0.1) * 0.3;
      meshRef.current.rotation.y += 0.001;
      meshRef.current.rotation.z = Math.cos(elapsed * 0.15) * 0.2;
    }

    if (bloodVesselsRef.current) {
      bloodVesselsRef.current.rotation.copy(meshRef.current!.rotation);
    }

    if (particlesRef.current) {
      particlesRef.current.rotation.copy(meshRef.current!.rotation);
      const positions = particlesRef.current.geometry.attributes.position.array as Float32Array;
      for (let i = 0; i < positions.length; i += 3) {
        const originalX = particlesRef.current.userData.originalPositions[i];
        const originalY = particlesRef.current.userData.originalPositions[i + 1];
        const originalZ = particlesRef.current.userData.originalPositions[i + 2];
        
        positions[i] = originalX + Math.sin(elapsed * 2 + i) * 0.02;
        positions[i + 1] = originalY + Math.cos(elapsed * 1.5 + i) * 0.02;
        positions[i + 2] = originalZ + Math.sin(elapsed * 1.8 + i) * 0.015;
      }
      particlesRef.current.geometry.attributes.position.needsUpdate = true;
    }

    // Dynamic lighting
    if (lightRef.current) {
      lightRef.current.intensity = 1.5 + Math.sin(elapsed * 1.5) * 0.5;
    }

  });

  // Create realistic retina texture using canvas
  const textureCanvas = useMemo(() => {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 512;
    const ctx = canvas.getContext('2d')!;

    // Base retinal color (reddish-brown)
    ctx.fillStyle = '#6b3410';
    ctx.fillRect(0, 0, 512, 512);

    // Add blood vessel-like patterns
    ctx.strokeStyle = 'rgba(139, 0, 0, 0.6)';
    ctx.lineWidth = 2;
    for (let i = 0; i < 30; i++) {
      const x = Math.random() * 512;
      const y = Math.random() * 512;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x + Math.random() * 100 - 50, y + Math.random() * 100 - 50);
      ctx.stroke();
    }

    // Add noise texture
    const imageData = ctx.getImageData(0, 0, 512, 512);
    const data = imageData.data;
    for (let i = 0; i < data.length; i += 4) {
      const noise = Math.random() * 30;
      data[i] += noise;
      data[i + 1] += noise * 0.5;
      data[i + 2] += noise * 0.3;
    }
    ctx.putImageData(imageData, 0, 0);

    return new THREE.CanvasTexture(canvas);
  }, []);

  // Create retina geometry
  const geometry = useMemo(() => {
    const geo = new THREE.IcosahedronGeometry(2.5, 64);
    const positionAttribute = geo.getAttribute('position');
    const positionArray = positionAttribute.array as Float32Array;

    // Add Perlin-like noise for realistic surface
    for (let i = 0; i < positionArray.length; i += 3) {
      const x = positionArray[i];
      const y = positionArray[i + 1];
      const z = positionArray[i + 2];

      const noise =
        Math.sin(x * 5) * Math.cos(y * 5) * 0.04 +
        Math.sin(y * 3) * Math.cos(z * 3) * 0.03 +
        Math.sin(z * 7) * 0.02 +
        Math.random() * 0.01;

      const scale = 2.5 + noise;
      const length = Math.sqrt(x * x + y * y + z * z);
      positionArray[i] = (x / length) * scale;
      positionArray[i + 1] = (y / length) * scale;
      positionArray[i + 2] = (z / length) * scale;
    }
    positionAttribute.needsUpdate = true;
    geo.computeVertexNormals();
    return geo;
  }, []);

  // Create realistic branching blood vessels
  const vesselGeometry = useMemo(() => {
    const points: THREE.Vector3[] = [];
    
    // Main arterial branches
    const branchCount = 8;
    for (let b = 0; b < branchCount; b++) {
      const angle = (b / branchCount) * Math.PI * 2;
      const startX = Math.cos(angle) * 2.5;
      const startY = Math.sin(angle) * 2.5;
      const startZ = Math.random() - 0.5;

      // Secondary branches
      for (let s = 0; s < 5; s++) {
        const t = s / 5;
        const subAngle = angle + (Math.random() - 0.5);
        const x = startX + Math.cos(subAngle) * t * 1.5;
        const y = startY + Math.sin(subAngle) * t * 1.5;
        const z = startZ + (Math.random() - 0.5) * 0.5;
        const dist = Math.sqrt(x * x + y * y + z * z);
        points.push(new THREE.Vector3((x / dist) * 2.5, (y / dist) * 2.5, (z / dist) * 2.5));
      }
    }

    return new THREE.BufferGeometry().setFromPoints(points);
  }, []);

  // Create particle system
  const particleGeometry = useMemo(() => {
    const geo = new THREE.BufferGeometry();
    const particleCount = 400;
    const positions = new Float32Array(particleCount * 3);

    for (let i = 0; i < particleCount * 3; i += 3) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.random() * Math.PI;
      const r = 2.4 + Math.random() * 0.8;

      positions[i] = Math.sin(phi) * Math.cos(theta) * r;
      positions[i + 1] = Math.sin(phi) * Math.sin(theta) * r;
      positions[i + 2] = Math.cos(phi) * r;
    }

    geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
    geo.userData.originalPositions = new Float32Array(positions);
    return geo;
  }, []);

  return (
    <>
      {/* Main Retina Mesh */}
      <mesh ref={meshRef} geometry={geometry}>
        <meshStandardMaterial
          map={textureCanvas}
          color={0xc47a2f}
          emissive={0x4a1a0a}
          emissiveIntensity={0.3}
          roughness={0.5}
          metalness={0.05}
          flatShading={false}
          wireframe={false}
        />
      </mesh>

      {/* Blood Vessels - Red arterial branches */}
      <lineSegments ref={bloodVesselsRef} geometry={vesselGeometry}>
        <lineBasicMaterial
          color={0xff4444}
          linewidth={3}
          transparent={true}
          opacity={0.8}
          fog={false}
        />
      </lineSegments>

      {/* Venous branches - Darker red */}
      <lineSegments geometry={vesselGeometry}>
        <lineBasicMaterial
          color={0xaa0000}
          linewidth={1}
          transparent={true}
          opacity={0.5}
          fog={false}
        />
      </lineSegments>

      {/* Glow Particles - Representing blood flow */}
      <points ref={particlesRef} geometry={particleGeometry}>
        <pointsMaterial
          color={0xff6b6b}
          size={0.08}
          sizeAttenuation={true}
          transparent={true}
          opacity={0.9}
          fog={false}
        />
      </points>

      {/* Advanced Lighting Setup */}
      <ambientLight intensity={0.5} color={0xffffff} />
      <directionalLight position={[10, 10, 5]} intensity={0.8} color={0xffffff} />
      <SpotLight ref={lightRef as any} position={[8, 8, 8]} intensity={1.5} color={0x0096ff} distance={20} />
      <pointLight position={[-8, -8, -8]} intensity={0.8} color={0xff6b6b} distance={15} />
      <pointLight position={[0, 0, 12]} intensity={1} color={0x00d9ff} distance={15} decay={2} />
    </>
  );
}

/**
 * Interactive Controls Component
 */
function SceneControls() {
  const { camera } = useThree();

  useEffect(() => {
    camera.position.z = 5;
  }, [camera]);

  return <OrbitControls autoRotate autoRotateSpeed={2} enableZoom={true} enablePan={true} />;
}

/**
 * Main Retina Scene Component
 * Immersive 3D visualization of a retina with interactive controls
 */
export function RetinaScene() {
  return (
    <div className="relative w-full h-full bg-gradient-to-br from-slate-900 via-blue-900 to-slate-900 overflow-hidden">
      {/* Canvas */}
      <Canvas>
        <PerspectiveCamera makeDefault position={[0, 0, 5]} fov={50} />
        <RetinaMesh />
        <SceneControls />
      </Canvas>

      {/* Overlay Info */}
      <div className="absolute bottom-8 left-8 pointer-events-none">
        <div className="text-cyan-300 text-sm font-mono opacity-80">
          <p>// RETINAL IMAGING SYSTEM</p>
          <p>// Interactive 3D Visualization</p>
          <p className="text-blue-400 mt-2">👁️ Rotate • Zoom • Pan</p>
        </div>
      </div>

      {/* Status Badge */}
      <div className="absolute top-8 right-8 bg-blue-900 bg-opacity-80 px-4 py-2 rounded-lg border border-cyan-300 pointer-events-none">
        <span className="text-cyan-300 text-sm font-semibold">LIVE</span>
      </div>
    </div>
  );
}
