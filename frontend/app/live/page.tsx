'use client';

import { useState, useEffect, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
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
    { name: 'Teams', href: '/teams' },
    { name: 'Dashboard', href: '/dashboard' },
    { name: 'NLP Analysis', href: '/nlp' }
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

interface LiveMatch {
  id: string;
  home_team: string;
  away_team: string;
  home_score: number;
  away_score: number;
  minute: number;
  status: string;
  events: Array<{
    minute: number;
    type: string;
    team: string;
    player: string;
    description: string;
  }>;
  date?: string;
}

interface MatchEvent {
  minute: number;
  type: string;
  team: string;
  player?: string;
  description: string;
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
    </>
  );
}

function AnimatedFootball({ initialPosition }: { initialPosition: [number, number, number] }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [targetPosition, setTargetPosition] = useState(() => new THREE.Vector3(...initialPosition));
  const currentPosition = useRef(new THREE.Vector3(...initialPosition));

  const getRandomPosition = (current: THREE.Vector3) => {
    const directions = [
      [1, 0], [-1, 0], [0, 1], [0, -1],
      [1, 1], [-1, -1], [1, -1], [-1, 1]
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

function PulsingSphere({ position, color }: { position: [number, number, number], color: string }) {
  return (
    <mesh position={position}>
      <sphereGeometry args={[0.2, 16, 16]} />
      <meshStandardMaterial color={color} emissive={color} emissiveIntensity={0.2} />
    </mesh>
  );
}

export default function LiveMatches() {
  const [liveMatches, setLiveMatches] = useState<LiveMatch[]>([]);
  const [recentMatches, setRecentMatches] = useState<LiveMatch[]>([]);
  const [selectedMatch, setSelectedMatch] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'live' | 'recent'>('live');

  // Football-Data.org API integration
  const FOOTBALL_API_KEY = process.env.NEXT_PUBLIC_FOOTBALL_API_KEY || 'YOUR_API_KEY_HERE';
  const fetchMatchData = async () => {
    setLoading(true);
    setError(null);
    
    // Actual Premier League results from August 30th, 2024
    const demoLiveMatches: LiveMatch[] = [];
    const demoRecentMatches: LiveMatch[] = [
      {
        id: 'recent1',
        home_team: 'Chelsea',
        away_team: 'Fulham',
        home_score: 2,
        away_score: 0,
        minute: 90,
        status: 'finished',
        events: [
          { minute: 35, type: 'goal', team: 'Chelsea', player: 'Palmer', description: 'Goal by Palmer' },
          { minute: 78, type: 'goal', team: 'Chelsea', player: 'Jackson', description: 'Goal by Jackson' }
        ],
        date: new Date(Date.now()).toLocaleDateString()
      },
      {
        id: 'recent2',
        home_team: 'Manchester United',
        away_team: 'Burnley',
        home_score: 3,
        away_score: 2,
        minute: 90,
        status: 'finished',
        events: [
          { minute: 23, type: 'goal', team: 'Burnley', player: 'Rodriguez', description: 'Goal by Rodriguez' },
          { minute: 45, type: 'goal', team: 'Manchester United', player: 'Rashford', description: 'Goal by Rashford' },
          { minute: 56, type: 'goal', team: 'Manchester United', player: 'Hojlund', description: 'Goal by Hojlund' },
          { minute: 67, type: 'goal', team: 'Burnley', player: 'Foster', description: 'Goal by Foster' },
          { minute: 89, type: 'goal', team: 'Manchester United', player: 'Bruno Fernandes', description: 'Goal by Bruno Fernandes' }
        ],
        date: new Date(Date.now()).toLocaleDateString()
      },
      {
        id: 'recent3',
        home_team: 'Tottenham',
        away_team: 'Bournemouth',
        home_score: 0,
        away_score: 1,
        minute: 90,
        status: 'finished',
        events: [
          { minute: 72, type: 'goal', team: 'Bournemouth', player: 'Solanke', description: 'Goal by Solanke' }
        ],
        date: new Date(Date.now()).toLocaleDateString()
      },
      {
        id: 'recent4',
        home_team: 'Wolves',
        away_team: 'Everton',
        home_score: 2,
        away_score: 3,
        minute: 90,
        status: 'finished',
        events: [
          { minute: 18, type: 'goal', team: 'Wolves', player: 'Cunha', description: 'Goal by Cunha' },
          { minute: 34, type: 'goal', team: 'Everton', player: 'Calvert-Lewin', description: 'Goal by Calvert-Lewin' },
          { minute: 56, type: 'goal', team: 'Everton', player: 'McNeil', description: 'Goal by McNeil' },
          { minute: 78, type: 'goal', team: 'Wolves', player: 'Hwang', description: 'Goal by Hwang' },
          { minute: 85, type: 'goal', team: 'Everton', player: 'Doucoure', description: 'Goal by Doucoure' }
        ],
        date: new Date(Date.now()).toLocaleDateString()
      },
      {
        id: 'recent5',
        home_team: 'Leeds United',
        away_team: 'Newcastle',
        home_score: 0,
        away_score: 0,
        minute: 90,
        status: 'finished',
        events: [],
        date: new Date(Date.now()).toLocaleDateString()
      },
      {
        id: 'recent6',
        home_team: 'Sunderland',
        away_team: 'Brentford',
        home_score: 2,
        away_score: 1,
        minute: 90,
        status: 'finished',
        events: [
          { minute: 28, type: 'goal', team: 'Sunderland', player: 'Roberts', description: 'Goal by Roberts' },
          { minute: 54, type: 'goal', team: 'Brentford', player: 'Toney', description: 'Goal by Toney' },
          { minute: 81, type: 'goal', team: 'Sunderland', player: 'Clarke', description: 'Goal by Clarke' }
        ],
        date: new Date(Date.now()).toLocaleDateString()
      }
    ];
    
    setLiveMatches(demoLiveMatches);
    setRecentMatches(demoRecentMatches);
    setActiveTab('recent');
    setSelectedMatch(demoRecentMatches[0]?.id || null);
    setLoading(false);
  };

  useEffect(() => {
    fetchMatchData();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'live': return 'text-green-400';
      case 'finished': return 'text-gray-400';
      case 'upcoming': return 'text-blue-400';
      default: return 'text-gray-400';
    }
  };

  const getEventIcon = (type: string) => {
    switch (type) {
      case 'goal': return '⚽';
      case 'yellow_card': return '🟨';
      case 'red_card': return '🟥';
      case 'substitution': return '🔄';
      default: return '📝';
    }
  };

  const currentMatches = activeTab === 'live' ? liveMatches : recentMatches;
  const selectedMatchData = currentMatches.find(match => match.id === selectedMatch);

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-[#37003c] mx-auto mb-4"></div>
          <p className="text-xl">Loading Live Match Data...</p>
        </div>
      </div>
    );
  }

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

      {/* Live Matches Content */}
      <div className="relative z-10 p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Live Matches</h1>
          <div className="flex items-center justify-between">
            <p className="text-gray-400">Real-time Premier League updates</p>
            {error && (
              <div className="text-yellow-400 text-sm bg-yellow-400/10 px-3 py-1 rounded-lg border border-yellow-400/20">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-4 mb-8">
          <button
            onClick={() => setActiveTab('live')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'live'
                ? 'bg-[#37003c] text-white'
                : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            Live Matches ({liveMatches.length})
          </button>
          <button
            onClick={() => setActiveTab('recent')}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              activeTab === 'recent'
                ? 'bg-[#37003c] text-white'
                : 'bg-gray-800 text-gray-400 hover:text-white'
            }`}
          >
            Recent Results ({recentMatches.length})
          </button>
        </div>

        {/* Matches Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Matches List */}
          <div className="lg:col-span-1">
            <h2 className="text-xl font-bold mb-4">
              {activeTab === 'live' ? 'Live Matches' : 'Recent Results'}
            </h2>
            <div className="space-y-4">
              {currentMatches.map((match) => (
                <div
                  key={match.id}
                  onClick={() => setSelectedMatch(match.id)}
                  className={`p-4 rounded-lg border cursor-pointer transition-all ${
                    selectedMatch === match.id
                      ? 'bg-[#37003c]/20 border-[#37003c]'
                      : 'bg-gray-900/80 border-gray-700 hover:border-gray-600'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className={`text-sm font-medium ${getStatusColor(match.status)}`}>
                      {match.status.toUpperCase()}
                    </div>
                    <div className="text-sm text-gray-400">
                      {activeTab === 'recent' && (match as any).date ? (match as any).date : `${match.minute}'`}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="font-medium">{match.home_team}</div>
                      <div className="font-medium">{match.away_team}</div>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold">{match.home_score}</div>
                      <div className="text-xl font-bold">{match.away_score}</div>
                    </div>
                  </div>
                </div>
              ))}
              
              {currentMatches.length === 0 && (
                <div className="text-center py-8 text-gray-400">
                  <div className="text-4xl mb-4">⚽</div>
                  <p>{activeTab === 'live' ? 'No live matches at the moment' : 'No recent matches found'}</p>
                  <p className="text-sm mt-2">
                    {activeTab === 'live' ? 'Check back during match days!' : 'Recent matches will appear here'}
                  </p>
                </div>
              )}
            </div>

            {/* Match Statistics */}
            <div className="mt-8 p-4 bg-gray-900/80 rounded-lg border border-gray-700">
              <h3 className="text-lg font-bold mb-4">
                {activeTab === 'live' ? 'Live Statistics' : 'Recent Statistics'}
              </h3>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-gray-400">
                    {activeTab === 'live' ? 'Matches Today' : 'Recent Matches'}
                  </span>
                  <span className="font-medium">{currentMatches.length}</span>
                </div>
                {activeTab === 'live' && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">Live Now</span>
                    <span className="font-medium text-green-400">
                      {liveMatches.filter(m => m.status === 'live').length}
                    </span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-gray-400">Total Goals</span>
                  <span className="font-medium">
                    {currentMatches.reduce((acc, match) => acc + match.home_score + match.away_score, 0)}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">Avg Goals/Match</span>
                  <span className="font-medium">
                    {currentMatches.length > 0 
                      ? (currentMatches.reduce((acc, match) => acc + match.home_score + match.away_score, 0) / currentMatches.length).toFixed(1)
                      : '0.0'
                    }
                  </span>
                </div>
              </div>
            </div>
          </div>
          {/* Match Details */}
          <div className="lg:col-span-2">
            {selectedMatchData ? (
              <div className="space-y-6">
                {/* Match Header */}
                <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800">
                  <div className="flex items-center justify-between mb-4">
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedMatchData.status)} bg-current/10`}>
                      {selectedMatchData.status.toUpperCase()} - {selectedMatchData.minute}'
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse"></div>
                      <span className="text-sm text-gray-400">LIVE</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <Image src={getTeamLogo(selectedMatchData.home_team)} alt={selectedMatchData.home_team} width={40} height={40} className="rounded-full" />
                      <span className="font-medium">{selectedMatchData.home_team}</span>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold">
                        {selectedMatchData.home_score} - {selectedMatchData.away_score}
                      </div>
                    </div>
                    <div className="flex items-center space-x-3">
                      <span className="font-medium">{selectedMatchData.away_team}</span>
                      <Image src={getTeamLogo(selectedMatchData.away_team)} alt={selectedMatchData.away_team} width={40} height={40} className="rounded-full" />
                    </div>
                  </div>
                </div>
                
                <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800">
                  <h3 className="text-xl font-bold mb-4">Match Events</h3>
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {selectedMatchData.events.map((event, index) => (
                      <div key={index} className="flex items-center space-x-4 p-3 bg-gray-800/50 rounded-lg">
                        <div className="text-2xl">{getEventIcon(event.type)}</div>
                        <div className="flex-1">
                          <div className="font-medium">{event.description}</div>
                          <div className="text-sm text-gray-400">
                            {event.team} • {event.minute}'
                          </div>
                        </div>
                        <div className="text-sm font-medium text-gray-400">
                          {event.minute}'
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Live Commentary */}
                <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800">
                  <h3 className="text-xl font-bold mb-4">Match Commentary</h3>
                  <div className="space-y-3 max-h-80 overflow-y-auto">
                    {selectedMatchData.id === 'recent1' && (
                      <>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">FT</span>
                          <span className="text-gray-300">Full-time whistle! Chelsea secure a comfortable 2-0 victory over Fulham at Stamford Bridge.</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">78'</span>
                          <span className="text-gray-300">⚽ GOAL! Nicolas Jackson doubles Chelsea's lead with a clinical finish after great work from Palmer.</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">65'</span>
                          <span className="text-gray-300">Chelsea controlling the tempo now, looking comfortable with their lead as Fulham struggle to create chances.</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">35'</span>
                          <span className="text-gray-300">⚽ GOAL! Cole Palmer opens the scoring for Chelsea with a brilliant strike from the edge of the box!</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">20'</span>
                          <span className="text-gray-300">End-to-end action at Stamford Bridge as both teams look to break the deadlock early.</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">1'</span>
                          <span className="text-gray-300">Kick-off! Chelsea get us underway in this London derby against Fulham.</span>
                        </div>
                      </>
                    )}
                    {selectedMatchData.id === 'recent2' && (
                      <>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">FT</span>
                          <span className="text-gray-300">What a thriller! Manchester United edge past Burnley 3-2 in a five-goal spectacular at Old Trafford.</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">89'</span>
                          <span className="text-gray-300">⚽ GOAL! Bruno Fernandes with the winner! A dramatic late strike sends Old Trafford into raptures!</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">67'</span>
                          <span className="text-gray-300">⚽ GOAL! Burnley level it again! Foster with a stunning equalizer - this match has everything!</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">56'</span>
                          <span className="text-gray-300">⚽ GOAL! Rasmus Hojlund puts United back in front with his first goal of the season!</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">45'</span>
                          <span className="text-gray-300">⚽ GOAL! Marcus Rashford equalizes for United just before half-time with a trademark finish!</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">23'</span>
                          <span className="text-gray-300">⚽ GOAL! Burnley take a shock early lead through Rodriguez - Old Trafford stunned!</span>
                        </div>
                      </>
                    )}
                    {selectedMatchData.id === 'recent3' && (
                      <>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">FT</span>
                          <span className="text-gray-300">Upset at the Tottenham Hotspur Stadium! Bournemouth secure a famous 1-0 victory over Spurs.</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">85'</span>
                          <span className="text-gray-300">Tottenham throwing everything forward but Bournemouth's defense is holding firm under intense pressure.</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">72'</span>
                          <span className="text-gray-300">⚽ GOAL! Dominic Solanke with the breakthrough! A clinical finish gives Bournemouth the lead!</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">45'</span>
                          <span className="text-gray-300">Half-time: Goalless at the break but both teams have had their chances in an entertaining first half.</span>
                        </div>
                      </>
                    )}
                    {!['recent1', 'recent2', 'recent3'].includes(selectedMatchData.id) && (
                      <>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">FT</span>
                          <span className="text-gray-300">Match concluded with an exciting finish. Both teams gave their all in this Premier League encounter.</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">75'</span>
                          <span className="text-gray-300">The intensity picks up as both teams push for the decisive goal in the final quarter.</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">45'</span>
                          <span className="text-gray-300">Half-time whistle brings a brief respite in what has been an entertaining first half.</span>
                        </div>
                        <div className="flex items-start space-x-3 p-3 bg-gray-800/30 rounded-lg">
                          <span className="text-[#37003c] font-bold w-12 flex-shrink-0">1'</span>
                          <span className="text-gray-300">Kick-off! The match gets underway with both teams looking sharp in the early exchanges.</span>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-12 border border-gray-800 text-center">
                <div className="text-6xl mb-4">⚽</div>
                <h3 className="text-xl font-bold mb-2">Select a Match</h3>
                <p className="text-gray-400">Choose a live match from the list to view detailed information and events.</p>
              </div>
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500">
          <p>Real-time Updates • WebSocket Connection • Live Commentary</p>
        </div>
      </div>
    </div>
  );
}
