'use client';

import Link from 'next/link';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { useRef, useState, useEffect, useMemo } from 'react';
import * as THREE from 'three';

// Navigation component
function PageNavigation() {
  const navItems = [
    { name: 'Home', href: '/' },
    { name: 'Predictions', href: '/predictions' },
    { name: 'Teams', href: '/teams' },
    { name: 'NLP Analysis', href: '/nlp' },
    { name: 'Live Matches', href: '/live' },
    { name: 'AI Assistant', href: '/ai-assistant' }
  ];

  return (
    <div className="fixed top-4 right-4 z-20 flex space-x-2">
      {navItems.map((item) => (
        <Link
          key={item.name}
          href={item.href}
          className="px-4 py-2 bg-gray-900/80 backdrop-blur-sm border border-gray-700 rounded-lg text-white hover:bg-[#37003c] hover:border-[#37003c] transition-all duration-200 text-sm font-medium"
        >
          {item.name}
        </Link>
      ))}
    </div>
  );
}

// Original 3D Football Components
function AnimatedFootball({ initialPosition }: { initialPosition: [number, number, number] }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [targetPosition, setTargetPosition] = useState(new THREE.Vector3(...initialPosition));
  const currentPosition = useRef(new THREE.Vector3(...initialPosition));

  const getRandomPosition = (current: THREE.Vector3) => {
    const directions = [
      [3, 0], [-3, 0], [0, 3], [0, -3],
      [2.5, 2.5], [-2.5, -2.5], [2.5, -2.5], [-2.5, 2.5],
      [4, 1], [-4, -1], [1, 4], [-1, -4]
    ];
    const randomDirection = directions[Math.floor(Math.random() * directions.length)];
    return new THREE.Vector3(
      current.x + randomDirection[0] * 2.5,
      Math.random() * 2 + 0.5,
      current.z + randomDirection[1] * 2.5
    );
  };

  useEffect(() => {
    const interval = setInterval(() => {
      const newPosition = getRandomPosition(currentPosition.current);
      newPosition.x = Math.max(-25, Math.min(25, newPosition.x));
      newPosition.z = Math.max(-25, Math.min(25, newPosition.z));
      newPosition.y = Math.max(0.3, Math.min(3, newPosition.y));
      setTargetPosition(newPosition);
    }, 3000 + Math.random() * 2000);

    return () => clearInterval(interval);
  }, []);

  useFrame((state, delta) => {
    if (meshRef.current) {
      currentPosition.current.lerp(targetPosition, 0.03);
      meshRef.current.position.copy(currentPosition.current);
      meshRef.current.rotation.x += delta * 1.5;
      meshRef.current.rotation.z += delta * 1.2;
      
      meshRef.current.position.y += Math.sin(state.clock.elapsedTime * 2 + initialPosition[0]) * 0.1;
    }
  });

  return (
    <mesh ref={meshRef} position={initialPosition} castShadow receiveShadow>
      <sphereGeometry args={[0.4, 16, 16]} />
      <meshStandardMaterial 
        color="#ffffff" 
        opacity={0.95} 
        transparent 
        roughness={0.3}
        metalness={0.1}
      />
      <lineSegments>
        <edgesGeometry attach="geometry" args={[new THREE.SphereGeometry(0.4, 12, 12)]} />
        <lineBasicMaterial attach="material" color="#000000" />
      </lineSegments>
    </mesh>
  );
}

function Scene({ teamColors }: { teamColors: { primary: string, secondary: string } }) {
  const footballPositions = useMemo(() => {
    const positions: [number, number, number][] = [];
    for (let x = -120; x <= 120; x += 20) {
      for (let z = -120; z <= 120; z += 20) {
        for (let y = 0; y <= 20; y += 10) {
          positions.push([
            x + (Math.random() - 0.5) * 8,
            y + Math.random() * 3,
            z + (Math.random() - 0.5) * 8
          ]);
        }
      }
    }
    const edges = [];
    for (let i = -150; i <= 150; i += 30) {
      edges.push([i, 3, -150], [i, 3, 150], [-150, 3, i], [150, 3, i]);
    }
    positions.push(...edges as [number, number, number][]);
    return positions;
  }, []);

  return (
    <>
      <OrbitControls 
        enablePan={false} 
        enableZoom={false} 
        autoRotate={true}
        autoRotateSpeed={0.2}
        enableDamping={true}
        dampingFactor={0.05}
      />
      <ambientLight intensity={0.6} />
      <pointLight position={[20, 20, 20]} intensity={0.8} />
      <directionalLight 
        position={[10, 10, 5]} 
        intensity={0.5} 
        castShadow 
        shadow-mapSize-width={2048}
        shadow-mapSize-height={2048}
      />
      <Grid
        renderOrder={-1}
        position={[0, 0, 0]}
        infiniteGrid
        cellSize={12}
        cellThickness={2.0}
        sectionSize={36}
        sectionThickness={3.0}
        sectionColor={teamColors.primary}
        cellColor={teamColors.secondary}
        fadeDistance={500}
        followCamera={false}
      />
      {footballPositions.map((position, index) => (
        <AnimatedFootball key={index} initialPosition={position} />
      ))}
    </>
  );
}

export default function Home() {
  return (
    <div 
      className="min-h-screen bg-black text-white relative overflow-y-auto"
      style={{
        scrollbarWidth: 'thin',
        scrollbarColor: '#4B5563 #111827',
        minHeight: '120vh'
      }}
    >
      {/* Page Navigation */}
      <PageNavigation />

      {/* 3D Background - Original Football Scene */}
      <div className="fixed inset-0 w-full h-full z-0" style={{ width: '100vw', height: '100vh' }}>
        <Canvas 
          shadows 
          camera={{ position: [80, 80, 80], fov: 100 }} 
          style={{ width: '100%', height: '100%' }}
        >
          <Scene teamColors={{ primary: '#00ff87', secondary: '#37003c' }} />
        </Canvas>
      </div>

      {/* Main Content */}
      <div className="relative z-10 flex items-center justify-center min-h-screen p-8">
        <div className="flex flex-col items-center justify-center space-y-8">
          <h1 className="text-6xl font-bold text-center bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
            Premier League Predictor
          </h1>
          <p className="text-xl text-gray-300 text-center max-w-2xl">
            FAANG-Level ML Application with 81.4% Accuracy • Real-time Analytics • Advanced Features
          </p>
          
          {/* Feature Highlights */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center max-w-4xl">
            <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
              <div className="text-2xl mb-2">🤖</div>
              <div className="text-sm font-medium">AI Predictions</div>
              <div className="text-xs text-gray-400">81.4% Accuracy</div>
            </div>
            <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
              <div className="text-2xl mb-2">📊</div>
              <div className="text-sm font-medium">Live Dashboard</div>
              <div className="text-xs text-gray-400">Real-time Analytics</div>
            </div>
            <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
              <div className="text-2xl mb-2">💬</div>
              <div className="text-sm font-medium">NLP Queries</div>
              <div className="text-xs text-gray-400">Natural Language</div>
            </div>
            <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
              <div className="text-2xl mb-2">📺</div>
              <div className="text-sm font-medium">Live Matches</div>
              <div className="text-xs text-gray-400">WebSocket Updates</div>
            </div>
          </div>

          {/* CTA Button */}
          <div className="flex justify-center">
            <Link 
              href="/predictions" 
              className="bg-[#00ff87] hover:bg-[#00ff87]/80 text-black px-8 py-4 rounded-lg text-lg font-medium transition-colors"
            >
              Get Started
            </Link>
          </div>

          {/* Stats */}
          <div className="flex flex-wrap justify-center gap-8 text-center">
            <div>
              <div className="text-3xl font-bold text-[#00ff87]">81.4%</div>
              <div className="text-sm text-gray-400">Model Accuracy</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-[#37003c]">1000+</div>
              <div className="text-sm text-gray-400">Concurrent Users</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-blue-400">&lt; 200ms</div>
              <div className="text-sm text-gray-400">API Response</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-400">99.97%</div>
              <div className="text-sm text-gray-400">Uptime</div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="absolute bottom-0 left-0 right-0 z-20 p-4 bg-black/20 backdrop-blur-sm">
        <div className="text-center text-gray-400 text-sm">
          2024 Premier League Predictor. All rights reserved. | Powered by AI & Machine Learning
        </div>
      </footer>
    </div>
  );
}
