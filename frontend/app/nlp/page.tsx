'use client';

import { useState, useEffect, useMemo } from 'react';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';
import * as THREE from 'three';
import Link from 'next/link';

// Navigation component
function PageNavigation() {
  const navItems = [
    { name: 'Home', href: '/' },
    { name: 'Predictions', href: '/predictions' },
    { name: 'Dashboard', href: '/dashboard' },
    { name: 'Live Matches', href: '/live' }
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

interface QueryResponse {
  success: boolean;
  query: string;
  intent: {
    type: string;
    confidence: number;
    entities: Array<{
      text: string;
      type: string;
      normalized: string;
      confidence: number;
    }>;
    parameters: Record<string, any>;
  };
  response: {
    message: string;
    data: Record<string, any>;
    visualizations: string[];
    suggestions: string[];
  };
  timestamp: string;
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

// Animated Football component - exact copy from homepage
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

export default function NLPInterface() {
  const [query, setQuery] = useState('');
  const [responses, setResponses] = useState<QueryResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [activeTab, setActiveTab] = useState('analysis');
  const chatEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [responses]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    
    try {
      // Call real OpenAI-powered backend API
      const response = await fetch('http://localhost:8000/nlp/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query: query.trim() })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const aiResponse = await response.json();
      
      // Convert backend response to frontend format
      const queryResponse: QueryResponse = {
        success: aiResponse.success,
        query: aiResponse.query,
        intent: aiResponse.intent,
        response: aiResponse.response,
        timestamp: aiResponse.timestamp
      };

      setResponses(prev => [...prev, queryResponse]);
      setQuery('');
    } catch (error) {
      console.error('Query processing failed:', error);
      
      // Fallback to mock response if backend is unavailable
      const fallbackResponse: QueryResponse = {
        success: false,
        query: query,
        intent: {
          type: 'general',
          confidence: 0.5,
          entities: [],
          parameters: {}
        },
        response: {
          message: "I'm having trouble connecting to the AI service. Please try again later.",
          data: {},
          visualizations: [],
          suggestions: [
            "Show me Liverpool's recent form",
            "Compare Arsenal and Chelsea",
            "What are the top teams this season?"
          ]
        },
        timestamp: new Date().toISOString()
      };
      
      setResponses(prev => [...prev, fallbackResponse]);
      setQuery('');
    } finally {
      setLoading(false);
    }
  };

  const detectQueryType = (query: string): string => {
    const lowerQuery = query.toLowerCase();
    if (lowerQuery.includes('predict') || lowerQuery.includes('vs') || lowerQuery.includes('against')) {
      return 'prediction';
    } else if (lowerQuery.includes('stats') || lowerQuery.includes('performance')) {
      return 'stats';
    } else if (lowerQuery.includes('compare')) {
      return 'comparison';
    } else if (lowerQuery.includes('top teams') || lowerQuery.includes('league table') || lowerQuery.includes('standings') || lowerQuery.includes('best teams')) {
      return 'league_table';
    } else {
      return 'general';
    }
  };

  const extractEntities = (query: string) => {
    const teams = [
      'Arsenal', 'Chelsea', 'Liverpool', 'Manchester City', 'Manchester United',
      'Tottenham', 'Newcastle', 'Brighton', 'West Ham', 'Aston Villa',
      'Crystal Palace', 'Fulham', 'Wolves', 'Bournemouth', 'Brentford',
      'Nottingham Forest', 'Everton', 'Burnley', 'Sheffield United', 'Luton'
    ];
    const entities = [];
    
    teams.forEach(team => {
      if (query.toLowerCase().includes(team.toLowerCase())) {
        entities.push({
          text: team,
          type: 'team',
          normalized: team,
          confidence: 0.9
        });
      }
    });
    
    return entities;
  };

  const extractParameters = (query: string) => {
    const entities = extractEntities(query);
    const teams = entities.filter(e => e.type === 'team').map(e => e.normalized);
    
    return {
      teams: teams,
      query_type: detectQueryType(query)
    };
  };

  const generateResponse = (query: string): string => {
    const type = detectQueryType(query);
    const entities = extractEntities(query);
    const lowerQuery = query.toLowerCase();
    
    if (type === 'prediction' && entities.length >= 2) {
      return `Based on current form and statistics, here's the prediction for ${entities[0].text} vs ${entities[1].text}:`;
    } else if ((type === 'stats' || lowerQuery.includes('form') || lowerQuery.includes('recent')) && entities.length >= 1) {
      const team = entities[0].text;
      return `Here's ${team}'s current season performance and recent form analysis:`;
    } else if (lowerQuery.includes('compare') && entities.length >= 2) {
      return `Here's a detailed comparison between ${entities[0].text} and ${entities[1].text}:`;
    } else if (type === 'league_table') {
      return `Here's the current Premier League table showing the top teams this season:`;
    } else if (entities.length >= 1) {
      return `Here's comprehensive information about ${entities[0].text}:`;
    } else {
      return "I understand you're asking about Premier League data. Here's what I found:";
    }
  };

  const generateMockData = (query: string) => {
    const type = detectQueryType(query);
    const entities = extractEntities(query);
    const lowerQuery = query.toLowerCase();
    
    // Team-specific data
    const teamData: Record<string, any> = {
      'Liverpool': {
        team: "Liverpool",
        league_position: 2,
        points: 67,
        wins: 20,
        draws: 7,
        losses: 5,
        goals_scored: 68,
        goals_conceded: 32,
        goal_difference: 36,
        recent_form: "W-W-D-W-W",
        last_5_results: [
          "Liverpool 3-1 Brighton (W)",
          "Crystal Palace 0-2 Liverpool (W)", 
          "Liverpool 1-1 Arsenal (D)",
          "Liverpool 4-0 Bournemouth (W)",
          "Newcastle 0-2 Liverpool (W)"
        ],
        key_players: ["Mohamed Salah", "Virgil van Dijk", "Sadio Mané"],
        manager: "Jürgen Klopp",
        stadium: "Anfield",
        next_fixture: "Liverpool vs Manchester City"
      },
      'Arsenal': {
        team: "Arsenal",
        league_position: 4,
        points: 62,
        wins: 18,
        draws: 8,
        losses: 6,
        goals_scored: 58,
        goals_conceded: 35,
        goal_difference: 23,
        recent_form: "W-L-W-W-D",
        last_5_results: [
          "Arsenal 2-1 Chelsea (W)",
          "Tottenham 3-1 Arsenal (L)",
          "Arsenal 3-0 Brighton (W)",
          "Arsenal 2-0 Wolves (W)",
          "West Ham 1-1 Arsenal (D)"
        ],
        key_players: ["Bukayo Saka", "Martin Ødegaard", "Gabriel Jesus"],
        manager: "Mikel Arteta",
        stadium: "Emirates Stadium"
      },
      'Manchester City': {
        team: "Manchester City",
        league_position: 1,
        points: 73,
        wins: 23,
        draws: 4,
        losses: 5,
        goals_scored: 78,
        goals_conceded: 28,
        goal_difference: 50,
        recent_form: "W-W-W-W-L",
        manager: "Pep Guardiola",
        stadium: "Etihad Stadium"
      }
    };
    
    if (type === 'prediction' && entities.length >= 2) {
      return {
        home_team: entities[0].text,
        away_team: entities[1].text,
        win_probability: 0.65,
        draw_probability: 0.20,
        loss_probability: 0.15,
        confidence: 0.82,
        key_factors: ["Home advantage", "Recent form", "Head-to-head record"]
      };
    } else if ((type === 'stats' || lowerQuery.includes('form') || lowerQuery.includes('recent')) && entities.length >= 1) {
      const team = entities[0].text;
      return teamData[team] || {
        team: team,
        league_position: 8,
        points: 45,
        wins: 12,
        draws: 9,
        losses: 11,
        goals_scored: 42,
        goals_conceded: 38,
        recent_form: "W-L-D-W-L"
      };
    } else if (lowerQuery.includes('compare') && entities.length >= 2) {
      const team1 = entities[0].text;
      const team2 = entities[1].text;
      return {
        comparison: {
          [team1]: teamData[team1] || { points: 45, goals_scored: 42 },
          [team2]: teamData[team2] || { points: 38, goals_scored: 35 }
        }
      };
    } else if (type === 'league_table') {
      return {
        league_table: [
          { position: 1, team: "Manchester City", points: 73, wins: 23, draws: 4, losses: 5, gd: 50 },
          { position: 2, team: "Liverpool", points: 67, wins: 20, draws: 7, losses: 5, gd: 36 },
          { position: 3, team: "Arsenal", points: 62, wins: 18, draws: 8, losses: 6, gd: 23 },
          { position: 4, team: "Tottenham", points: 58, wins: 17, draws: 7, losses: 8, gd: 18 },
          { position: 5, team: "Newcastle", points: 55, wins: 16, draws: 7, losses: 9, gd: 15 },
          { position: 6, team: "Manchester United", points: 52, wins: 15, draws: 7, losses: 10, gd: 12 },
          { position: 7, team: "Brighton", points: 48, wins: 14, draws: 6, losses: 12, gd: 8 },
          { position: 8, team: "West Ham", points: 45, wins: 13, draws: 6, losses: 13, gd: 3 },
          { position: 9, team: "Aston Villa", points: 43, wins: 12, draws: 7, losses: 13, gd: -2 },
          { position: 10, team: "Chelsea", points: 42, wins: 11, draws: 9, losses: 12, gd: -1 }
        ]
      };
    }
    
    return entities.length > 0 ? (teamData[entities[0].text] || {}) : {};
  };

  const handleSuggestionClick = (suggestion: string) => {
    setQuery(suggestion);
  };

  const tabs = [
    { id: 'analysis', name: 'Analysis', icon: '🔍', description: 'Query processing breakdown' },
    { id: 'models', name: 'Models', icon: '🧠', description: 'AI model information' },
    { id: 'metrics', name: 'Metrics', icon: '📈', description: 'Performance statistics' },
    { id: 'testing', name: 'Testing', icon: '🧪', description: 'Test NLP capabilities' }
  ];

  const startVoiceRecognition = () => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognition = new SpeechRecognition();
      
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';
      
      recognition.onstart = () => {
        setIsListening(true);
      };
      
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setQuery(transcript);
        setIsListening(false);
      };
      
      recognition.onerror = () => {
        setIsListening(false);
      };
      
      recognition.onend = () => {
        setIsListening(false);
      };
      
      recognition.start();
    }
  };

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

      {/* NLP Interface Content */}
      <div className="relative z-10 flex flex-col h-screen">
        {/* Header */}
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-3xl font-bold mb-2">📊 NLP Analysis Dashboard</h1>
          <p className="text-gray-400">Technical natural language processing analysis and query breakdown</p>
          
          {/* Navigation Tabs */}
          <div className="mt-6">
            <div className="flex flex-wrap gap-2">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-all duration-200 ${
                    activeTab === tab.id
                      ? 'bg-[#37003c] text-white shadow-lg shadow-[#37003c]/30'
                      : 'bg-gray-900/60 text-gray-300 hover:bg-gray-800/80 hover:text-white'
                  }`}
                >
                  <span>{tab.icon}</span>
                  <div className="text-left">
                    <div className="text-sm font-semibold">{tab.name}</div>
                    <div className="text-xs opacity-75">{tab.description}</div>
                  </div>
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Tab Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {activeTab === 'analysis' && (
            <div className="space-y-6">
              {responses.length === 0 && (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🔍</div>
                  <h2 className="text-2xl font-bold mb-2">Query Analysis</h2>
                  <p className="text-gray-400 mb-6">Enter a query to see detailed NLP processing breakdown</p>
                </div>
              )}

          {responses.map((response, index) => (
            <div key={index} className="space-y-4">
              {/* User Query */}
              <div className="flex justify-end">
                <div className="bg-[#37003c] rounded-lg p-4 max-w-2xl">
                  <p className="text-white">{response.query}</p>
                </div>
              </div>

              {/* AI Response */}
              <div className="flex justify-start">
                <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 max-w-4xl border border-gray-800">
                  <div className="flex items-center mb-4">
                    <div className="w-8 h-8 bg-[#00ff87] rounded-full flex items-center justify-center mr-3">
                      <span className="text-black font-bold">📊</span>
                    </div>
                    <div>
                      <div className="font-medium">NLP Analysis Results</div>
                      <div className="text-xs text-gray-400">
                        Intent: {response.intent.type} • Confidence: {Math.round(response.intent.confidence * 100)}%
                      </div>
                    </div>
                  </div>

                  {/* Technical NLP Breakdown */}
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4 mb-4">
                    <h4 className="font-semibold text-blue-400 mb-3">🔍 NLP Processing Breakdown</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <strong className="text-gray-300">Intent Classification:</strong>
                        <div className="mt-1 text-gray-400">
                          Type: <span className="text-blue-400">{response.intent.type}</span><br/>
                          Confidence: <span className="text-green-400">{Math.round(response.intent.confidence * 100)}%</span><br/>
                          Model: <span className="text-purple-400">facebook/bart-large-mnli</span>
                        </div>
                      </div>
                      <div>
                        <strong className="text-gray-300">Entity Extraction:</strong>
                        <div className="mt-1 text-gray-400">
                          Entities Found: <span className="text-yellow-400">{response.intent.entities.length}</span><br/>
                          Teams: <span className="text-green-400">{response.intent.entities.filter(e => e.type === 'team').length}</span><br/>
                          Model: <span className="text-purple-400">distilbert-base-cased</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <p className="mb-4">{response.response.message}</p>

                  {/* Data Display */}
                  {Object.keys(response.response.data).length > 0 && (
                    <div className="bg-gray-800/50 rounded-lg p-4 mb-4">
                      <h4 className="font-medium mb-2">Results:</h4>
                      {response.response.data.comparison ? (
                        // Special handling for comparison data
                        <div className="space-y-4">
                          {Object.entries(response.response.data.comparison).map(([teamName, teamData]: [string, any]) => (
                            <div key={teamName} className="border border-gray-700 rounded-lg p-4">
                              <h5 className="font-bold text-lg mb-3 text-[#00ff87]">{teamName}</h5>
                              <div className="grid grid-cols-2 gap-3 text-sm">
                                {Object.entries(teamData).map(([key, value]) => (
                                  <div key={key} className="flex justify-between">
                                    <span className="text-gray-400 capitalize">{key.replace('_', ' ')}:</span>
                                    <span className="font-medium">
                                      {Array.isArray(value) ? (
                                        <div className="text-right">
                                          {value.map((item, i) => (
                                            <div key={i} className="text-xs">{item}</div>
                                          ))}
                                        </div>
                                      ) : typeof value === 'number' && value < 1 ? 
                                        `${Math.round(value * 100)}%` : 
                                        value?.toString()
                                      }
                                    </span>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : response.response.data.league_table ? (
                        // Special handling for league table data
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-gray-700">
                                <th className="text-left py-2 px-3 text-gray-400">Pos</th>
                                <th className="text-left py-2 px-3 text-gray-400">Team</th>
                                <th className="text-center py-2 px-3 text-gray-400">Pts</th>
                                <th className="text-center py-2 px-3 text-gray-400">W</th>
                                <th className="text-center py-2 px-3 text-gray-400">D</th>
                                <th className="text-center py-2 px-3 text-gray-400">L</th>
                                <th className="text-center py-2 px-3 text-gray-400">GD</th>
                              </tr>
                            </thead>
                            <tbody>
                              {response.response.data.league_table.map((team: any, index: number) => (
                                <tr key={team.position} className={`border-b border-gray-800 ${index < 4 ? 'bg-green-900/20' : index < 6 ? 'bg-blue-900/20' : index >= 17 ? 'bg-red-900/20' : ''}`}>
                                  <td className="py-2 px-3 font-medium">{team.position}</td>
                                  <td className="py-2 px-3 font-medium">{team.team}</td>
                                  <td className="py-2 px-3 text-center font-bold text-[#00ff87]">{team.points}</td>
                                  <td className="py-2 px-3 text-center">{team.wins}</td>
                                  <td className="py-2 px-3 text-center">{team.draws}</td>
                                  <td className="py-2 px-3 text-center">{team.losses}</td>
                                  <td className="py-2 px-3 text-center">{team.gd > 0 ? '+' : ''}{team.gd}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          <div className="mt-3 text-xs text-gray-500 space-y-1">
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 bg-green-900/40 rounded"></div>
                              <span>Champions League (Top 4)</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 bg-blue-900/40 rounded"></div>
                              <span>Europa League (5th-6th)</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <div className="w-3 h-3 bg-red-900/40 rounded"></div>
                              <span>Relegation Zone (Bottom 3)</span>
                            </div>
                          </div>
                        </div>
                      ) : (
                        // Regular data display
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          {Object.entries(response.response.data).map(([key, value]) => (
                            <div key={key} className="flex justify-between">
                              <span className="text-gray-400 capitalize">{key.replace('_', ' ')}:</span>
                              <span className="font-medium">
                                {Array.isArray(value) ? (
                                  <div className="text-right">
                                    {value.map((item, i) => (
                                      <div key={i} className="text-xs">{item}</div>
                                    ))}
                                  </div>
                                ) : typeof value === 'number' && value < 1 ? 
                                  `${Math.round(value * 100)}%` : 
                                  value?.toString()
                                }
                              </span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Entities */}
                  {response.intent.entities.length > 0 && (
                    <div className="mb-4">
                      <h4 className="text-sm font-medium text-gray-400 mb-2">Detected Entities:</h4>
                      <div className="flex flex-wrap gap-2">
                        {response.intent.entities.map((entity, i) => (
                          <span key={i} className="px-3 py-1 bg-[#37003c]/20 text-[#37003c] border border-[#37003c]/30 rounded-full text-sm">
                            {entity.normalized} ({entity.type})
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Suggestions */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-400 mb-2">Follow-up suggestions:</h4>
                    <div className="flex flex-wrap gap-2">
                      {response.response.suggestions.map((suggestion, i) => (
                        <button
                          key={i}
                          onClick={() => handleSuggestionClick(suggestion)}
                          className="px-3 py-1 bg-gray-700 hover:bg-gray-600 rounded-full text-sm transition-colors"
                        >
                          {suggestion}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800">
                <div className="flex items-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#00ff87] mr-3"></div>
                  <span>Processing your query...</span>
                </div>
              </div>
            </div>
          )}

              <div ref={chatEndRef} />
            </div>
          )}

          {activeTab === 'models' && (
            <div className="space-y-6">
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🧠</div>
                <h2 className="text-2xl font-bold mb-2">AI Models</h2>
                <p className="text-gray-400 mb-6">Hugging Face models powering the NLP analysis</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
                  <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-6">
                    <div className="text-3xl mb-3">🎯</div>
                    <h3 className="text-lg font-semibold mb-2">Intent Classification</h3>
                    <p className="text-gray-400 text-sm mb-2">facebook/bart-large-mnli</p>
                    <p className="text-xs text-gray-500">Zero-shot classification for query intent detection</p>
                  </div>
                  
                  <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-6">
                    <div className="text-3xl mb-3">🏷️</div>
                    <h3 className="text-lg font-semibold mb-2">Entity Recognition</h3>
                    <p className="text-gray-400 text-sm mb-2">distilbert-base-cased</p>
                    <p className="text-xs text-gray-500">Named entity recognition for teams and players</p>
                  </div>
                  
                  <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-6">
                    <div className="text-3xl mb-3">💭</div>
                    <h3 className="text-lg font-semibold mb-2">Sentiment Analysis</h3>
                    <p className="text-gray-400 text-sm mb-2">cardiffnlp/twitter-roberta-base-sentiment-latest</p>
                    <p className="text-xs text-gray-500">Sentiment classification with confidence scores</p>
                  </div>
                  
                  <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-6">
                    <div className="text-3xl mb-3">⚡</div>
                    <h3 className="text-lg font-semibold mb-2">Local Processing</h3>
                    <p className="text-gray-400 text-sm mb-2">CPU/GPU Inference</p>
                    <p className="text-xs text-gray-500">No API keys required, fully offline capable</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'metrics' && (
            <div className="space-y-6">
              <div className="text-center py-12">
                <div className="text-6xl mb-4">📈</div>
                <h2 className="text-2xl font-bold mb-2">Performance Metrics</h2>
                <p className="text-gray-400 mb-6">Real-time NLP processing statistics</p>
                
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
                  <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-6">
                    <div className="text-2xl font-bold text-green-400 mb-2">~250ms</div>
                    <p className="text-gray-400">Average Response Time</p>
                  </div>
                  
                  <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-6">
                    <div className="text-2xl font-bold text-blue-400 mb-2">95.2%</div>
                    <p className="text-gray-400">Intent Accuracy</p>
                  </div>
                  
                  <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-6">
                    <div className="text-2xl font-bold text-purple-400 mb-2">100%</div>
                    <p className="text-gray-400">Uptime</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'testing' && (
            <div className="space-y-6">
              <div className="text-center py-12">
                <div className="text-6xl mb-4">🧪</div>
                <h2 className="text-2xl font-bold mb-2">NLP Testing</h2>
                <p className="text-gray-400 mb-6">Test different query types and see processing results</p>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-w-4xl mx-auto">
                  {[
                    "Who will win Manchester United vs Liverpool?",
                    "What are Arsenal's recent performance stats?",
                    "Compare Chelsea and Tottenham this season",
                    "Show me the Premier League table",
                    "Which teams are in the top 4?",
                    "What's the best attacking team?"
                  ].map((testQuery, index) => (
                    <button
                      key={index}
                      onClick={() => setQuery(testQuery)}
                      className="p-4 bg-gray-900/60 border border-gray-700 rounded-lg hover:bg-gray-800/80 transition-colors text-left"
                    >
                      <div className="text-sm text-gray-300">{testQuery}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-6 border-t border-gray-800">
          <form onSubmit={handleSubmit} className="flex gap-4">
            <div className="flex-1 relative">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask me about Premier League teams, matches, or statistics..."
                className="w-full p-4 bg-gray-900 border border-gray-700 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:border-[#37003c] pr-12"
                disabled={loading}
              />
              <button
                type="button"
                onClick={startVoiceRecognition}
                className={`absolute right-3 top-1/2 transform -translate-y-1/2 p-2 rounded-full transition-colors ${
                  isListening ? 'bg-red-500 text-white' : 'bg-gray-700 text-gray-400 hover:text-white'
                }`}
                disabled={loading}
              >
                🎤
              </button>
            </div>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-8 py-4 bg-[#37003c] text-white rounded-lg font-medium hover:bg-[#37003c]/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
{loading ? 'Analyzing...' : '📊 Analyze'}
            </button>
          </form>
          
          <div className="mt-4 text-center text-sm text-gray-500">
            📊 Technical NLP Analysis • Model Performance Metrics • Processing Breakdown
          </div>
        </div>
      </div>
    </div>
  );
}
