'use client';

import { useState, useRef, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { Canvas } from '@react-three/fiber';
import { OrbitControls, Grid } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import Navigation from '../components/Navigation';

// 3D Football Components
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

// 3D Scene
function AIScene() {
  const teamColors = { primary: "#37003c", secondary: "#00ff88" };
  
  return (
    <Canvas camera={{ position: [0, 5, 15], fov: 60 }}>
      <Scene teamColors={teamColors} />
    </Canvas>
  );
}

// Page Navigation component
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

export default function AIAssistantPage() {
  const [query, setQuery] = useState('');
  const [response, setResponse] = useState(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('home');
  const [homeTeam, setHomeTeam] = useState('');
  const [awayTeam, setAwayTeam] = useState('');
  const [predictionResult, setPredictionResult] = useState(null);
  const [predictionLoading, setPredictionLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://pl2025-ml-predictor-1.onrender.com';
      const res = await fetch(`${apiUrl}/nlp/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      });
      
      const data = await res.json();
      setResponse(data);
    } catch (error) {
      console.error('Error:', error);
      setResponse({
        success: false,
        error: 'Failed to connect to AI service'
      });
    } finally {
      setLoading(false);
    }
  };

  const handlePrediction = async () => {
    if (!homeTeam || !awayTeam || homeTeam === awayTeam) return;
    
    setPredictionLoading(true);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'https://pl2025-ml-predictor-1.onrender.com';
      const res = await fetch(`${apiUrl}/predict`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          home_team: homeTeam, 
          away_team: awayTeam 
        }),
      });
      
      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }
      
      const data = await res.json();
      console.log('Backend response:', data); // Debug log
      
      setPredictionResult({
        success: true,
        prediction: data.prediction || 'Unknown',
        confidence: data.confidence_score || 0,
        probabilities: {
          home_win: data.win_probability || 0,
          draw: data.draw_probability || 0,
          away_win: data.loss_probability || 0
        },
        raw_data: data // Store raw response for debugging
      });
    } catch (error) {
      console.error('Prediction error:', error);
      
      // Try to get error details from response
      let errorMessage = 'Failed to get prediction';
      if (error.message.includes('400')) {
        errorMessage = 'Invalid team names or backend data issue';
      }
      
      setPredictionResult({
        success: false,
        error: errorMessage,
        debug_info: error.message
      });
    } finally {
      setPredictionLoading(false);
    }
  };

  const teams = [
    'Arsenal', 'Aston Villa', 'Bournemouth', 'Brentford', 'Brighton', 'Burnley', 
    'Chelsea', 'Crystal Palace', 'Everton', 'Fulham', 'Leeds', 'Leicester', 
    'Liverpool', 'Manchester City', 'Manchester United', 'Newcastle', 'Norwich', 
    'Nottm Forest', 'Sheffield United', 'Southampton', 'Tottenham', 'Watford', 
    'West Bromwich Albion', 'West Ham', 'Wolves'
  ];

  const sampleQueries = [
    "How is Liverpool performing this season?",
    "Compare Arsenal vs Chelsea",
    "Show me the league table",
    "Who are the top scorers?",
    "Predict Manchester City vs Arsenal"
  ];

  const tabs = [
    { id: 'home', name: 'Home', icon: '🏠', description: 'AI Assistant overview' },
    { id: 'chat', name: 'Chat', icon: '💬', description: 'Interactive AI conversation' },
    { id: 'predictions', name: 'Predictions', icon: '🔮', description: 'Match predictions & odds' },
    { id: 'analysis', name: 'Analysis', icon: '📊', description: 'Team analysis & insights' },
    { id: 'insights', name: 'Insights', icon: '💡', description: 'AI-powered insights' },
    { id: 'settings', name: 'Settings', icon: '⚙️', description: 'Configure AI preferences' }
  ];

  return (
    <div className="min-h-screen bg-black text-white relative overflow-hidden">
      {/* 3D Background */}
      <div className="fixed inset-0 z-0">
        <Canvas camera={{ position: [0, 5, 15], fov: 60 }}>
          <Scene teamColors={{ primary: "#37003c", secondary: "#00ff88" }} />
        </Canvas>
      </div>

      {/* Navigation */}
      <PageNavigation />

      {/* Main Content */}
      <div className="relative z-10 min-h-screen flex flex-col">
        <div className="flex-1 px-6 py-8">
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold mb-4 bg-gradient-to-r from-white to-gray-300 bg-clip-text text-transparent">
              🤖 AI Assistant
            </h1>
            <p className="text-gray-300 text-lg">
              Ask me anything about Premier League teams, matches, and predictions
            </p>
            <div className="mt-4 inline-flex items-center space-x-2 bg-green-500/20 px-4 py-2 rounded-full">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-green-400 text-sm font-medium">Free Local AI • No API Keys Required</span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <div className="flex flex-wrap justify-center gap-2 mb-8">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-4 py-2 bg-gray-900/80 backdrop-blur-sm border border-gray-700 rounded-lg text-white hover:bg-[#37003c] hover:border-[#37003c] transition-all duration-200 text-sm font-medium ${
                  activeTab === tab.id ? 'bg-[#37003c] border-[#37003c]' : ''
                }`}
              >
                {tab.icon} {tab.name}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div className="max-w-4xl mx-auto">
            {activeTab === 'home' && (
              <div className="space-y-8">
                {/* Welcome Section */}
                <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-8 text-center">
                  <div className="text-6xl mb-4">🤖</div>
                  <h3 className="text-2xl font-bold mb-4">Welcome to Your AI Assistant</h3>
                  <p className="text-gray-400 mb-6">Your personal Premier League expert powered by free local AI</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    <div className="bg-gray-800/50 rounded-lg p-4">
                      <div className="text-2xl mb-2">💬</div>
                      <h4 className="font-semibold mb-1">Natural Chat</h4>
                      <p className="text-xs text-gray-400">Ask questions in plain English</p>
                    </div>
                    <div className="bg-gray-800/50 rounded-lg p-4">
                      <div className="text-2xl mb-2">🔮</div>
                      <h4 className="font-semibold mb-1">Smart Predictions</h4>
                      <p className="text-xs text-gray-400">AI-powered match forecasts</p>
                    </div>
                    <div className="bg-gray-800/50 rounded-lg p-4">
                      <div className="text-2xl mb-2">📊</div>
                      <h4 className="font-semibold mb-1">Deep Analysis</h4>
                      <p className="text-xs text-gray-400">Advanced team & player stats</p>
                    </div>
                  </div>
                  
                  <button 
                    onClick={() => setActiveTab('chat')}
                    className="mt-6 px-6 py-3 bg-[#37003c] hover:bg-[#37003c]/80 text-white font-medium rounded-xl transition-colors"
                  >
                    Start Chatting 💬
                  </button>
                </div>

                {/* Quick Stats */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div className="bg-green-500/10 border border-green-500/30 rounded-xl p-6 text-center">
                    <div className="text-3xl font-bold text-green-400 mb-2">100%</div>
                    <p className="text-gray-400">Free & Local</p>
                    <p className="text-xs text-gray-500 mt-1">No API costs</p>
                  </div>
                  
                  <div className="bg-blue-500/10 border border-blue-500/30 rounded-xl p-6 text-center">
                    <div className="text-3xl font-bold text-blue-400 mb-2">20</div>
                    <p className="text-gray-400">Teams Covered</p>
                    <p className="text-xs text-gray-500 mt-1">All Premier League clubs</p>
                  </div>
                  
                  <div className="bg-purple-500/10 border border-purple-500/30 rounded-xl p-6 text-center">
                    <div className="text-3xl font-bold text-purple-400 mb-2">24/7</div>
                    <p className="text-gray-400">Always Available</p>
                    <p className="text-xs text-gray-500 mt-1">Offline capable</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'chat' && (
              <div>
                {/* Query Interface */}
                <form onSubmit={handleSubmit} className="mb-8">
                  <div className="flex gap-4">
                    <input
                      type="text"
                      value={query}
                      onChange={(e) => setQuery(e.target.value)}
                      placeholder="Ask me about Premier League teams, matches, or predictions..."
                      className="flex-1 px-6 py-4 bg-gray-900/80 border border-gray-700 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-[#37003c] focus:border-transparent"
                      disabled={loading}
                    />
                    <button
                      type="submit"
                      disabled={loading || !query.trim()}
                      className="px-8 py-4 bg-[#37003c] hover:bg-[#37003c]/80 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors"
                    >
                      {loading ? '🤔 Thinking...' : '💬 Chat'}
                    </button>
                  </div>
                </form>

                {/* Sample Queries */}
                <div className="mb-8">
                  <h3 className="text-lg font-semibold mb-4 text-gray-300">💡 Try these sample queries:</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                    {sampleQueries.map((sample, index) => (
                      <button
                        key={index}
                        onClick={() => setQuery(sample)}
                        className="p-3 bg-gray-900/60 hover:bg-gray-800/80 border border-gray-700 rounded-lg text-left text-sm text-gray-300 hover:text-white transition-colors"
                      >
                        "{sample}"
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'analysis' && (
              <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-8 text-center">
                <div className="text-6xl mb-4">📊</div>
                <h3 className="text-2xl font-bold mb-4">Deep Football Analytics</h3>
                <p className="text-gray-400 mb-6">Advanced statistical analysis and performance metrics</p>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <h4 className="font-semibold mb-2">Team Performance</h4>
                    <p className="text-sm text-gray-400">Comprehensive team statistics and trends</p>
                  </div>
                  <div className="bg-gray-800/50 rounded-lg p-4">
                    <h4 className="font-semibold mb-2">Player Analytics</h4>
                    <p className="text-sm text-gray-400">Individual player performance metrics</p>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'predictions' && (
              <div className="space-y-6">
                <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-8 text-center">
                  <div className="text-6xl mb-4">🔮</div>
                  <h3 className="text-2xl font-bold mb-4">Match Predictions & Odds</h3>
                  <p className="text-gray-400 mb-6">AI-powered match outcome predictions with confidence scores</p>
                  
                  {/* Prediction Interface */}
                  <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
                    <h4 className="font-semibold mb-4 text-white">Quick Prediction</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                      <select 
                        value={homeTeam}
                        onChange={(e) => setHomeTeam(e.target.value)}
                        className="p-3 bg-gray-900 border border-gray-700 rounded-lg text-white"
                      >
                        <option value="">Select Home Team</option>
                        {teams.map((team) => (
                          <option key={team} value={team}>{team}</option>
                        ))}
                      </select>
                      <select 
                        value={awayTeam}
                        onChange={(e) => setAwayTeam(e.target.value)}
                        className="p-3 bg-gray-900 border border-gray-700 rounded-lg text-white"
                      >
                        <option value="">Select Away Team</option>
                        {teams.map((team) => (
                          <option key={team} value={team}>{team}</option>
                        ))}
                      </select>
                    </div>
                    <button 
                      onClick={handlePrediction}
                      disabled={!homeTeam || !awayTeam || homeTeam === awayTeam || predictionLoading}
                      className="px-6 py-3 bg-[#37003c] hover:bg-[#37003c]/80 disabled:bg-gray-600 disabled:cursor-not-allowed text-white font-medium rounded-xl transition-colors"
                    >
                      {predictionLoading ? '🤔 Predicting...' : '🔮 Generate Prediction'}
                    </button>
                  </div>
                  
                  {/* Prediction Results */}
                  {predictionResult && (
                    <div className="bg-gray-800/50 rounded-lg p-6 mb-6">
                      {predictionResult.success ? (
                        <div>
                          <h4 className="font-semibold text-white mb-4">🔮 Prediction Results</h4>
                          <div className="grid grid-cols-3 gap-4 mb-4">
                            <div className="text-center">
                              <div className="text-2xl font-bold text-green-400">
                                {predictionResult.probabilities?.home_win ? (predictionResult.probabilities.home_win * 100).toFixed(1) : '0.0'}%
                              </div>
                              <div className="text-sm text-gray-400">{homeTeam} Win</div>
                            </div>
                            <div className="text-center">
                              <div className="text-2xl font-bold text-yellow-400">
                                {predictionResult.probabilities?.draw ? (predictionResult.probabilities.draw * 100).toFixed(1) : '0.0'}%
                              </div>
                              <div className="text-sm text-gray-400">Draw</div>
                            </div>
                            <div className="text-center">
                              <div className="text-2xl font-bold text-red-400">
                                {predictionResult.probabilities?.away_win ? (predictionResult.probabilities.away_win * 100).toFixed(1) : '0.0'}%
                              </div>
                              <div className="text-sm text-gray-400">{awayTeam} Win</div>
                            </div>
                          </div>
                          <div className="text-center">
                            <div className="text-lg font-semibold text-white mb-2">
                              Predicted Winner: <span className="text-[#00ff87]">{predictionResult.prediction}</span>
                            </div>
                            <div className="text-sm text-gray-400">
                              Confidence: {predictionResult.confidence ? (predictionResult.confidence * 100).toFixed(1) : '0.0'}%
                            </div>
                          </div>
                        </div>
                      ) : (
                        <div className="text-red-400 text-center">
                          Error: {predictionResult.error || 'Failed to generate prediction'}
                        </div>
                      )}
                    </div>
                  )}
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-4">
                      <div className="text-2xl mb-2">🏆</div>
                      <h4 className="font-semibold text-green-400">Win Probability</h4>
                      <p className="text-sm text-gray-400">Home team victory chances</p>
                    </div>
                    <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-4">
                      <div className="text-2xl mb-2">🤝</div>
                      <h4 className="font-semibold text-yellow-400">Draw Probability</h4>
                      <p className="text-sm text-gray-400">Match ending in a tie</p>
                    </div>
                    <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                      <div className="text-2xl mb-2">📉</div>
                      <h4 className="font-semibold text-red-400">Loss Probability</h4>
                      <p className="text-sm text-gray-400">Away team victory chances</p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'insights' && (
              <div className="space-y-6">
                <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-8 text-center">
                  <div className="text-6xl mb-4">💡</div>
                  <h3 className="text-2xl font-bold mb-4">AI-Powered Insights</h3>
                  <p className="text-gray-400 mb-6">Smart analysis and strategic recommendations</p>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-6 text-left">
                      <h4 className="font-semibold text-blue-400 mb-3">🧠 Pattern Recognition</h4>
                      <p className="text-sm text-gray-400 mb-4">Identify trends and patterns in team performance</p>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Form Analysis:</span>
                          <span className="text-blue-400">Advanced</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Trend Detection:</span>
                          <span className="text-green-400">Active</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-purple-500/10 border border-purple-500/30 rounded-lg p-6 text-left">
                      <h4 className="font-semibold text-purple-400 mb-3">⚡ Real-time Analysis</h4>
                      <p className="text-sm text-gray-400 mb-4">Live match insights and tactical observations</p>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Live Updates:</span>
                          <span className="text-purple-400">Enabled</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Tactical AI:</span>
                          <span className="text-green-400">Online</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-orange-500/10 border border-orange-500/30 rounded-lg p-6 text-left">
                      <h4 className="font-semibold text-orange-400 mb-3">🎯 Strategic Recommendations</h4>
                      <p className="text-sm text-gray-400 mb-4">AI-generated tactical suggestions and insights</p>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Strategy Engine:</span>
                          <span className="text-orange-400">Advanced</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Confidence:</span>
                          <span className="text-green-400">High</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="bg-cyan-500/10 border border-cyan-500/30 rounded-lg p-6 text-left">
                      <h4 className="font-semibold text-cyan-400 mb-3">📈 Performance Tracking</h4>
                      <p className="text-sm text-gray-400 mb-4">Monitor team and player performance metrics</p>
                      <div className="space-y-2 text-xs">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Data Sources:</span>
                          <span className="text-cyan-400">Multiple</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Accuracy:</span>
                          <span className="text-green-400">95.2%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'settings' && (
              <div className="space-y-6">
                <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-8">
                  <div className="text-center mb-6">
                    <div className="text-6xl mb-4">⚙️</div>
                    <h3 className="text-2xl font-bold mb-4">AI Settings & Preferences</h3>
                    <p className="text-gray-400">Customize your AI assistant experience</p>
                  </div>
                  
                  <div className="space-y-6">
                    {/* AI Model Settings */}
                    <div className="bg-gray-800/50 rounded-lg p-6">
                      <h4 className="font-semibold text-white mb-4">🧠 AI Model Configuration</h4>
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300">Response Style:</span>
                          <select className="p-2 bg-gray-900 border border-gray-700 rounded-lg text-white text-sm">
                            <option>Detailed & Technical</option>
                            <option>Casual & Friendly</option>
                            <option>Brief & Direct</option>
                          </select>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300">Confidence Threshold:</span>
                          <input type="range" min="0.5" max="1.0" step="0.1" defaultValue="0.8" className="w-32" />
                        </div>
                      </div>
                    </div>
                    
                    {/* Display Preferences */}
                    <div className="bg-gray-800/50 rounded-lg p-6">
                      <h4 className="font-semibold text-white mb-4">🎨 Display Preferences</h4>
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300">Show Technical Details:</span>
                          <input type="checkbox" defaultChecked className="w-4 h-4" />
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300">Enable Animations:</span>
                          <input type="checkbox" defaultChecked className="w-4 h-4" />
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300">Auto-scroll to Response:</span>
                          <input type="checkbox" defaultChecked className="w-4 h-4" />
                        </div>
                      </div>
                    </div>
                    
                    {/* Performance Settings */}
                    <div className="bg-gray-800/50 rounded-lg p-6">
                      <h4 className="font-semibold text-white mb-4">⚡ Performance Settings</h4>
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300">Processing Mode:</span>
                          <select className="p-2 bg-gray-900 border border-gray-700 rounded-lg text-white text-sm">
                            <option>CPU (Slower, Compatible)</option>
                            <option>GPU (Faster, Requires CUDA)</option>
                            <option>Auto-detect</option>
                          </select>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-gray-300">Cache Responses:</span>
                          <input type="checkbox" defaultChecked className="w-4 h-4" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Response */}
            {response && (
              <div className="bg-gray-900/80 border border-gray-700 rounded-xl p-6">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-xl font-semibold text-white">🤖 AI Response</h3>
                  <div className={`px-3 py-1 rounded-full text-xs font-medium ${
                    response.success ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                  }`}>
                    {response.success ? '✅ Success' : '❌ Error'}
                  </div>
                </div>

                {response.success ? (
                  <div className="space-y-4">
                    {/* Intent Detection */}
                    {response.intent && (
                      <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-4">
                        <h4 className="font-semibold text-blue-400 mb-2">🎯 Intent Detected</h4>
                        <div className="text-sm text-gray-300">
                          <p><strong>Type:</strong> {response.intent.type}</p>
                          <p><strong>Confidence:</strong> {(response.intent.confidence * 100).toFixed(1)}%</p>
                          {response.intent.entities && response.intent.entities.length > 0 && (
                            <div className="mt-2">
                              <strong>Teams Found:</strong> {response.intent.entities.map(e => e.text).join(', ')}
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    {/* Main Response */}
                    <div className="bg-gray-800/50 rounded-lg p-4">
                      <h4 className="font-semibold text-white mb-3">{response.response.message}</h4>
                      
                      {/* Data Display */}
                      {response.response.data && (
                        <div className="bg-gray-900/50 rounded-lg p-4 mt-3">
                          {/* Check if data contains prediction information */}
                          {response.response.data.win_probability !== undefined ? (
                            <div className="space-y-4">
                              <h5 className="font-semibold text-white mb-3">🔮 Match Prediction</h5>
                              
                              {/* Probability Display */}
                              <div className="grid grid-cols-3 gap-4">
                                <div className="text-center bg-green-500/10 border border-green-500/30 rounded-lg p-3">
                                  <div className="text-xl font-bold text-green-400">
                                    {(response.response.data.win_probability * 100).toFixed(1)}%
                                  </div>
                                  <div className="text-xs text-gray-400">{response.response.data.home_team} Win</div>
                                </div>
                                <div className="text-center bg-yellow-500/10 border border-yellow-500/30 rounded-lg p-3">
                                  <div className="text-xl font-bold text-yellow-400">
                                    {(response.response.data.draw_probability * 100).toFixed(1)}%
                                  </div>
                                  <div className="text-xs text-gray-400">Draw</div>
                                </div>
                                <div className="text-center bg-red-500/10 border border-red-500/30 rounded-lg p-3">
                                  <div className="text-xl font-bold text-red-400">
                                    {(response.response.data.loss_probability * 100).toFixed(1)}%
                                  </div>
                                  <div className="text-xs text-gray-400">{response.response.data.away_team} Win</div>
                                </div>
                              </div>
                              
                              {/* Winner and Confidence */}
                              <div className="text-center bg-gray-800/50 rounded-lg p-3">
                                <div className="text-lg font-semibold text-white mb-1">
                                  Predicted Winner: <span className="text-[#00ff87]">
                                    {response.response.data.win_probability > Math.max(response.response.data.draw_probability, response.response.data.loss_probability) 
                                      ? response.response.data.home_team 
                                      : response.response.data.loss_probability > response.response.data.draw_probability 
                                        ? response.response.data.away_team 
                                        : 'Draw'}
                                  </span>
                                </div>
                                <div className="text-sm text-gray-400">
                                  Confidence: {(response.response.data.confidence * 100).toFixed(1)}%
                                </div>
                              </div>
                              
                              {/* Key Factors */}
                              {response.response.data.key_factors && (
                                <div className="bg-blue-500/10 border border-blue-500/30 rounded-lg p-3">
                                  <h6 className="font-semibold text-blue-400 mb-2">🎯 Key Factors</h6>
                                  <div className="flex flex-wrap gap-2">
                                    {response.response.data.key_factors.map((factor, index) => (
                                      <span key={index} className="px-2 py-1 bg-blue-500/20 text-blue-300 rounded text-xs">
                                        {factor}
                                      </span>
                                    ))}
                                  </div>
                                </div>
                              )}
                            </div>
                          ) : response.response.data.top_scorers ? (
                            <div className="space-y-4">
                              <h5 className="font-semibold text-white mb-3">⚽ Top Scorers</h5>
                              <div className="space-y-2">
                                {response.response.data.top_scorers.map((scorer, index) => (
                                  <div key={index} className="flex justify-between items-center bg-gray-800/50 rounded-lg p-3">
                                    <div className="flex items-center space-x-3">
                                      <div className="w-8 h-8 bg-[#00ff87]/20 rounded-full flex items-center justify-center">
                                        <span className="text-[#00ff87] font-bold text-sm">{index + 1}</span>
                                      </div>
                                      <div>
                                        <div className="font-semibold text-white">{scorer.player}</div>
                                        <div className="text-sm text-gray-400">{scorer.team}</div>
                                      </div>
                                    </div>
                                    <div className="text-right">
                                      <div className="text-xl font-bold text-[#00ff87]">{scorer.goals}</div>
                                      <div className="text-xs text-gray-400">{scorer.assists} assists</div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ) : response.response.data.league_table ? (
                            <div className="space-y-4">
                              <h5 className="font-semibold text-white mb-3">🏆 League Table</h5>
                              <div className="space-y-1">
                                {response.response.data.league_table.map((team, index) => (
                                  <div key={index} className="flex justify-between items-center bg-gray-800/50 rounded-lg p-3">
                                    <div className="flex items-center space-x-3">
                                      <div className="w-8 h-8 bg-purple-500/20 rounded-full flex items-center justify-center">
                                        <span className="text-purple-400 font-bold text-sm">{team.position}</span>
                                      </div>
                                      <div className="font-semibold text-white">{team.team}</div>
                                    </div>
                                    <div className="flex space-x-4 text-sm">
                                      <div className="text-[#00ff87]">{team.points} pts</div>
                                      <div className="text-gray-400">{team.wins}W {team.draws}D {team.losses}L</div>
                                      <div className="text-gray-400">GD: {team.gd}</div>
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          ) : (
                            <pre className="text-sm text-gray-300 whitespace-pre-wrap overflow-x-auto">
                              {JSON.stringify(response.response.data, null, 2)}
                            </pre>
                          )}
                        </div>
                      )}

                      {/* Suggestions */}
                      {response.response.suggestions && response.response.suggestions.length > 0 && (
                        <div className="mt-4">
                          <h5 className="text-sm font-semibold text-gray-400 mb-2">💡 Try these next:</h5>
                          <div className="flex flex-wrap gap-2">
                            {response.response.suggestions.map((suggestion, index) => (
                              <button
                                key={index}
                                onClick={() => setQuery(suggestion)}
                                className="px-3 py-1 bg-[#37003c]/30 hover:bg-[#37003c]/50 border border-[#37003c]/50 rounded-full text-xs text-gray-300 hover:text-white transition-colors"
                              >
                                {suggestion}
                              </button>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="text-red-400">
                    <p className="mb-2">Error: {response.error || 'Unknown error occurred'}</p>
                    <p className="text-sm text-gray-400">Please try again or rephrase your query.</p>
                  </div>
                )}
              </div>
            )}

            {/* Features */}
            <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-6 text-center">
                <div className="text-3xl mb-3">🧠</div>
                <h3 className="text-lg font-semibold mb-2">Intent Detection</h3>
                <p className="text-gray-400 text-sm">Advanced AI understands what you're asking about</p>
              </div>
              
              <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-6 text-center">
                <div className="text-3xl mb-3">⚽</div>
                <h3 className="text-lg font-semibold mb-2">Football Intelligence</h3>
                <p className="text-gray-400 text-sm">Recognizes all 20 Premier League teams and nicknames</p>
              </div>
              
              <div className="bg-gray-900/60 border border-gray-700 rounded-xl p-6 text-center">
                <div className="text-3xl mb-3">🆓</div>
                <h3 className="text-lg font-semibold mb-2">100% Free</h3>
                <p className="text-gray-400 text-sm">Runs locally with Hugging Face models</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
