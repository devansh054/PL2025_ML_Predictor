'use client';

import { useState, useEffect } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';
import * as THREE from 'three';
import Link from 'next/link';
import { getTeamLogo } from '../../utils/teamLogos';
import Image from 'next/image';

// Navigation component
function PageNavigation() {
  const navItems = [
    { name: 'Home', href: '/' },
    { name: 'Predictions', href: '/predictions' },
    { name: 'Dashboard', href: '/dashboard' },
    { name: 'Live Matches', href: '/live' }
  ];

  return (
    <nav className="bg-black/20 backdrop-blur-sm border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold text-white">
              PL Predictor
            </Link>
          </div>
          <div className="flex space-x-8">
            {navItems.map((item) => (
              <Link
                key={item.name}
                href={item.href}
                className="text-gray-300 hover:text-white px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                {item.name}
              </Link>
            ))}
          </div>
        </div>
      </div>
    </nav>
  );
}

// 3D Background Component
function AnimatedBackground() {
  const meshRef = useRef<THREE.Mesh>(null);
  
  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.1;
      meshRef.current.rotation.y += delta * 0.05;
    }
  });

  return (
    <mesh ref={meshRef} position={[0, 0, -5]}>
      <boxGeometry args={[2, 2, 2]} />
      <meshStandardMaterial color="#37003c" wireframe />
    </mesh>
  );
}

// Premier League teams data
const premierLeagueTeams = [
  { name: 'Arsenal', stadium: 'Emirates Stadium', founded: 1886, league: 'Premier League' },
  { name: 'Aston Villa', stadium: 'Villa Park', founded: 1874, league: 'Premier League' },
  { name: 'Bournemouth', stadium: 'Vitality Stadium', founded: 1899, league: 'Premier League' },
  { name: 'Brentford', stadium: 'Brentford Community Stadium', founded: 1889, league: 'Premier League' },
  { name: 'Brighton', stadium: 'American Express Community Stadium', founded: 1901, league: 'Premier League' },
  { name: 'Burnley', stadium: 'Turf Moor', founded: 1882, league: 'Premier League' },
  { name: 'Chelsea', stadium: 'Stamford Bridge', founded: 1905, league: 'Premier League' },
  { name: 'Crystal Palace', stadium: 'Selhurst Park', founded: 1905, league: 'Premier League' },
  { name: 'Everton', stadium: 'Goodison Park', founded: 1878, league: 'Premier League' },
  { name: 'Fulham', stadium: 'Craven Cottage', founded: 1879, league: 'Premier League' },
  { name: 'Liverpool', stadium: 'Anfield', founded: 1892, league: 'Premier League' },
  { name: 'Luton', stadium: 'Kenilworth Road', founded: 1885, league: 'Premier League' },
  { name: 'Manchester City', stadium: 'Etihad Stadium', founded: 1880, league: 'Premier League' },
  { name: 'Manchester United', stadium: 'Old Trafford', founded: 1878, league: 'Premier League' },
  { name: 'Newcastle', stadium: 'St. James\' Park', founded: 1892, league: 'Premier League' },
  { name: 'Nottingham Forest', stadium: 'City Ground', founded: 1865, league: 'Premier League' },
  { name: 'Sheffield United', stadium: 'Bramall Lane', founded: 1889, league: 'Premier League' },
  { name: 'Tottenham', stadium: 'Tottenham Hotspur Stadium', founded: 1882, league: 'Premier League' },
  { name: 'West Ham', stadium: 'London Stadium', founded: 1895, league: 'Premier League' },
  { name: 'Wolves', stadium: 'Molineux Stadium', founded: 1877, league: 'Premier League' }
];

export default function TeamsPage() {
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredTeams, setFilteredTeams] = useState(premierLeagueTeams);

  useEffect(() => {
    const filtered = premierLeagueTeams.filter(team =>
      team.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      team.stadium.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredTeams(filtered);
  }, [searchTerm]);

  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden">
      {/* 3D Background */}
      <div className="fixed inset-0 z-0">
        <Canvas camera={{ position: [0, 0, 5], fov: 75 }}>
          <ambientLight intensity={0.5} />
          <pointLight position={[10, 10, 10]} />
          <AnimatedBackground />
          <OrbitControls enableZoom={false} enablePan={false} />
        </Canvas>
      </div>

      {/* Content */}
      <div className="relative z-10">
        <PageNavigation />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="text-4xl md:text-6xl font-bold mb-4">
              Premier League Teams
            </h1>
            <p className="text-xl text-gray-300 max-w-3xl mx-auto">
              Explore all 20 Premier League teams with detailed information about their stadiums, history, and current form.
            </p>
          </div>

          {/* Search Bar */}
          <div className="mb-8">
            <div className="max-w-md mx-auto">
              <input
                type="text"
                placeholder="Search teams or stadiums..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full px-4 py-3 bg-gray-900/80 backdrop-blur-sm border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#37003c] focus:border-transparent"
              />
            </div>
          </div>

          {/* Teams Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
            {filteredTeams.map((team) => (
              <div
                key={team.name}
                className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800 hover:border-[#37003c] transition-all duration-300 hover:transform hover:scale-105"
              >
                {/* Team Logo */}
                <div className="flex justify-center mb-4">
                  <Image 
                    src={getTeamLogo(team.name)} 
                    alt={team.name} 
                    width={64} 
                    height={64} 
                    className="rounded-full"
                  />
                </div>

                {/* Team Info */}
                <div className="text-center">
                  <h3 className="text-xl font-bold mb-2">{team.name}</h3>
                  <p className="text-gray-400 text-sm mb-2">{team.stadium}</p>
                  <p className="text-gray-500 text-xs mb-4">Founded: {team.founded}</p>
                  
                  {/* Stats */}
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">League Position:</span>
                      <span className="text-white">#{Math.floor(Math.random() * 20) + 1}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Points:</span>
                      <span className="text-white">{Math.floor(Math.random() * 80) + 10}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-400">Form:</span>
                      <span className="text-green-400">W-W-D-L-W</span>
                    </div>
                  </div>

                  {/* Action Button */}
                  <button className="mt-4 w-full bg-[#37003c] hover:bg-[#37003c]/80 text-white py-2 px-4 rounded-lg transition-colors">
                    View Details
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* No Results */}
          {filteredTeams.length === 0 && (
            <div className="text-center py-12">
              <p className="text-gray-400 text-lg">No teams found matching your search.</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="mt-16 text-center text-gray-500 pb-8">
          <p>Premier League Teams • Season 2023-24 • Official Data</p>
        </div>
      </div>
    </div>
  );
}
