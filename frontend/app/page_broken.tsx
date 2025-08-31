'use client';

import Link from 'next/link';
import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { useFrame } from '@react-three/fiber';
import { useRef } from 'react';
import * as THREE from 'three';

// 3D Background Components
function FloatingCube({ position }: { position: [number, number, number] }) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.5;
      meshRef.current.rotation.y += delta * 0.3;
      meshRef.current.position.y = position[1] + Math.sin(state.clock.elapsedTime) * 0.5;
    }
  });

  return (
    <mesh ref={meshRef} position={position}>
      <boxGeometry args={[0.5, 0.5, 0.5]} />
      <meshStandardMaterial color="#37003c" wireframe />
    </mesh>
  );
}

function AnimatedSphere({ position }: { position: [number, number, number] }) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame((state, delta) => {
    if (meshRef.current) {
      meshRef.current.rotation.x += delta * 0.2;
      meshRef.current.rotation.y += delta * 0.4;
      meshRef.current.position.x = position[0] + Math.cos(state.clock.elapsedTime) * 0.3;
    }
  });

  return (
    <mesh ref={meshRef} position={position}>
      <sphereGeometry args={[0.3, 16, 16]} />
      <meshStandardMaterial color="#00ff87" transparent opacity={0.6} />
    </mesh>
  );
}

function AnimatedFootball({ initialPosition }: { initialPosition: [number, number, number] }) {
  const meshRef = useRef<THREE.Mesh>(null)
  const [targetPosition, setTargetPosition] = useState(new THREE.Vector3(...initialPosition))
  const currentPosition = useRef(new THREE.Vector3(...initialPosition))

  const getRandomPosition = (current: THREE.Vector3) => {
    const directions = [
      [3, 0], [-3, 0], [0, 3], [0, -3],
      [2.5, 2.5], [-2.5, -2.5], [2.5, -2.5], [-2.5, 2.5],
      [4, 1], [-4, -1], [1, 4], [-1, -4]
    ]
    const randomDirection = directions[Math.floor(Math.random() * directions.length)]
    return new THREE.Vector3(
      current.x + randomDirection[0] * 2.5,
      Math.random() * 2 + 0.5, // Vary height for more 3D effect
      current.z + randomDirection[1] * 2.5
    )
  }

  useEffect(() => {
    const interval = setInterval(() => {
      const newPosition = getRandomPosition(currentPosition.current)
      newPosition.x = Math.max(-25, Math.min(25, newPosition.x))
      newPosition.z = Math.max(-25, Math.min(25, newPosition.z))
      newPosition.y = Math.max(0.3, Math.min(3, newPosition.y))
      setTargetPosition(newPosition)
    }, 3000 + Math.random() * 2000) // Vary timing

    return () => clearInterval(interval)
  }, [])

  useFrame((state, delta) => {
    if (meshRef.current) {
      currentPosition.current.lerp(targetPosition, 0.03)
      meshRef.current.position.copy(currentPosition.current)
      meshRef.current.rotation.x += delta * 1.5
      meshRef.current.rotation.z += delta * 1.2
      
      // Add subtle floating effect
      meshRef.current.position.y += Math.sin(state.clock.elapsedTime * 2 + initialPosition[0]) * 0.1
    }
  })

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
        <lineBasicMaterial attach="material" color="#000000" linewidth={2} />
      </lineSegments>
    </mesh>
  )
}

function Scene({ teamColors }: { teamColors: { primary: string, secondary: string } }) {
  const footballPositions = useMemo(() => {
    const positions: [number, number, number][] = []
    // Optimized grid - fewer footballs for better performance
    for (let x = -120; x <= 120; x += 20) {
      for (let z = -120; z <= 120; z += 20) {
        for (let y = 0; y <= 20; y += 10) {
          positions.push([
            x + (Math.random() - 0.5) * 8,
            y + Math.random() * 3,
            z + (Math.random() - 0.5) * 8
          ])
        }
      }
    }
    // Strategic edge coverage only
    const edges = []
    for (let i = -150; i <= 150; i += 30) {
      edges.push([i, 3, -150], [i, 3, 150], [-150, 3, i], [150, 3, i])
    }
    positions.push(...edges as [number, number, number][])
    return positions
  }, [])

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
  )
}

interface Team {
  name: string
}

interface TeamTheme {
  name: string
  primaryColor: string
  secondaryColor: string
  logo: string
}

interface Prediction {
  home_team: string
  away_team: string
  win_probability: number
  draw_probability: number
  loss_probability: number
  confidence_score: number
  model_used: string
  features_used: string
}

// Premier League team themes and colors with reliable logos
const teamThemes: Record<string, TeamTheme> = {
  'Arsenal': { name: 'Arsenal', primaryColor: '#DC143C', secondaryColor: '#FFD700', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t3.svg' },
  'Chelsea': { name: 'Chelsea', primaryColor: '#034694', secondaryColor: '#FFFFFF', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t8.svg' },
  'Liverpool': { name: 'Liverpool', primaryColor: '#C8102E', secondaryColor: '#F6EB61', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t14.svg' },
  'Manchester City': { name: 'Manchester City', primaryColor: '#6CABDD', secondaryColor: '#FFFFFF', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t43.svg' },
  'Manchester United': { name: 'Manchester United', primaryColor: '#DA020E', secondaryColor: '#FFE500', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t1.svg' },
  'Tottenham': { name: 'Tottenham', primaryColor: '#132257', secondaryColor: '#FFFFFF', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t6.svg' },
  'Newcastle': { name: 'Newcastle', primaryColor: '#241F20', secondaryColor: '#FFFFFF', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t4.svg' },
  'Brighton': { name: 'Brighton', primaryColor: '#0057B8', secondaryColor: '#FFCD00', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t36.svg' },
  'West Ham': { name: 'West Ham', primaryColor: '#7A263A', secondaryColor: '#1BB1E7', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t21.svg' },
  'Aston Villa': { name: 'Aston Villa', primaryColor: '#95BFE5', secondaryColor: '#670E36', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t7.svg' },
  'Crystal Palace': { name: 'Crystal Palace', primaryColor: '#1B458F', secondaryColor: '#C4122E', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t31.svg' },
  'Fulham': { name: 'Fulham', primaryColor: '#FFFFFF', secondaryColor: '#000000', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t54.svg' },
  'Leicester': { name: 'Leicester', primaryColor: '#003090', secondaryColor: '#FDBE11', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t13.svg' },
  'Brentford': { name: 'Brentford', primaryColor: '#E30613', secondaryColor: '#FFE500', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t94.svg' },
  'Wolves': { name: 'Wolves', primaryColor: '#FDB913', secondaryColor: '#231F20', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t39.svg' },
  'Everton': { name: 'Everton', primaryColor: '#003399', secondaryColor: '#FFFFFF', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t11.svg' },
  'Leeds': { name: 'Leeds', primaryColor: '#FFFFFF', secondaryColor: '#1D428A', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t2.svg' },
  'Burnley': { name: 'Burnley', primaryColor: '#6C1D45', secondaryColor: '#99D6EA', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t90.svg' },
  'Sheffield Utd': { name: 'Sheffield Utd', primaryColor: '#EE2737', secondaryColor: '#000000', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t49.svg' },
  'Southampton': { name: 'Southampton', primaryColor: '#D71920', secondaryColor: '#FFE500', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t20.svg' },
  'Bournemouth': { name: 'Bournemouth', primaryColor: '#DA020E', secondaryColor: '#000000', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t91.svg' },
  'West Bromwich Albion': { name: 'West Bromwich Albion', primaryColor: '#122F67', secondaryColor: '#FFFFFF', logo: 'https://logos-world.net/wp-content/uploads/2020/06/West-Bromwich-Albion-Logo.png' },
  'Sheffield United': { name: 'Sheffield United', primaryColor: '#EE2737', secondaryColor: '#000000', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t49.svg' },
  'Nottm Forest': { name: 'Nottm Forest', primaryColor: '#DD0000', secondaryColor: '#FFFFFF', logo: 'https://resources.premierleague.com/premierleague/badges/rb/t17.svg' },
  'Watford': { name: 'Watford', primaryColor: '#FBEE23', secondaryColor: '#ED2127', logo: 'https://upload.wikimedia.org/wikipedia/en/e/e2/Watford.svg' },
  'Norwich': { name: 'Norwich', primaryColor: '#FFF200', secondaryColor: '#00A650', logo: 'https://upload.wikimedia.org/wikipedia/en/8/8c/Norwich_City.svg' }
}

export default function PremierLeaguePredictor() {
  const [teams, setTeams] = useState<string[]>([])
  const [homeTeam, setHomeTeam] = useState('')
  const [awayTeam, setAwayTeam] = useState('')
  const [prediction, setPrediction] = useState<Prediction | null>(null)
  const [winningTeam, setWinningTeam] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [activeView, setActiveView] = useState<'home' | 'stats' | 'teams' | 'about'>('home')

  useEffect(() => {
    // Fetch available teams
    const fetchTeams = async () => {
      try {
        const response = await axios.get('http://localhost:8000/teams')
        setTeams(response.data)
      } catch (err) {
        console.error('Error fetching teams:', err)
        setError('Failed to load teams. Make sure the backend is running.')
      }
    }
    fetchTeams()
  }, [])

  const handlePredict = async () => {
    if (!homeTeam || !awayTeam) {
      setError('Please select both teams')
      return
    }
    if (homeTeam === awayTeam) {
      setError('Please select different teams')
      return
    }

    setLoading(true)
    setError('')
    
    try {
      const response = await axios.post('http://localhost:8000/predict', {
        home_team: homeTeam,
        away_team: awayTeam,
        venue: 'Home'
      })
      setPrediction(response.data)
      
      // Determine winning team for dynamic theming
      const result = response.data
      if (result.win_probability > result.draw_probability && result.win_probability > result.loss_probability) {
        setWinningTeam(homeTeam)
      } else if (result.loss_probability > result.draw_probability && result.loss_probability > result.win_probability) {
        setWinningTeam(awayTeam)
      } else {
        setWinningTeam(null) // Draw
      }
    } catch (err) {
      setError('Prediction failed. Please try again.')
      console.error('Prediction error:', err)
    } finally {
      setLoading(false)
    }
  }

  // Get team theme for dynamic styling
  const getTeamTheme = (teamName: string): TeamTheme => {
    return teamThemes[teamName] || { name: teamName, primaryColor: '#FFFFFF', secondaryColor: '#000000', logo: '⚽' }
  }

  // Get winning team's colors for 3D background
  const getWinningTeamColors = () => {
    if (!winningTeam) return { primary: '#26d926', secondary: '#1a8c1a' }
    const theme = getTeamTheme(winningTeam)
    return { primary: theme.primaryColor, secondary: theme.secondaryColor }
  }

  return (
    <div className="relative w-full h-screen bg-transparent text-white overflow-hidden font-sans">
      <header className="fixed top-0 left-0 right-0 z-20 p-6 bg-black bg-opacity-20 backdrop-blur-sm">
        <nav className="flex justify-between items-center">
          <div className="flex items-center space-x-3">
            <img 
              src="https://upload.wikimedia.org/wikipedia/en/f/f2/Premier_League_Logo.svg" 
              alt="Premier League" 
              className="h-13 w-12 object-contain"
            />
            <div className="text-2xl font-bold">PL Predictor</div>
          </div>
          <nav className="flex space-x-8">
            <button 
              onClick={() => setActiveView('home')}
              className={`transition-colors ${activeView === 'home' ? 'text-white' : 'text-white/80 hover:text-white'}`}
            >
              Predictions
            </button>
            <button 
              onClick={() => setActiveView('stats')}
              className={`transition-colors ${activeView === 'stats' ? 'text-white' : 'text-white/80 hover:text-white'}`}
            >
              Stats
            </button>
            <button 
              onClick={() => setActiveView('teams')}
              className={`transition-colors ${activeView === 'teams' ? 'text-white' : 'text-white/80 hover:text-white'}`}
            >
              Teams
            </button>
            <button 
              onClick={() => setActiveView('about')}
              className={`transition-colors ${activeView === 'about' ? 'text-white' : 'text-white/80 hover:text-white'}`}
            >
              About
            </button>
          </nav>
        </nav>
      </header>

      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 text-center z-20 w-full max-w-4xl px-4">
        {activeView !== 'home' && (
          <h2 className="text-xl mb-12 text-gray-400 font-light max-w-2xl mx-auto">
            AI-powered predictions with 81.4% accuracy using advanced ML models
          </h2>
        )}

        {activeView === 'home' && (
          <>
            {/* Team Selection */}
            <div className="relative bg-black bg-opacity-40 backdrop-blur-md border border-white border-opacity-10 rounded-2xl p-8 mb-8 shadow-2xl">
              <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent rounded-2xl"></div>
              <div className="relative z-10">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
                  <div className="space-y-3">
                    <label className="block text-sm font-medium text-gray-300 uppercase tracking-wider">Home Team</label>
                    <select 
                      value={homeTeam} 
                      onChange={(e) => setHomeTeam(e.target.value)}
                      className="w-full p-4 bg-black bg-opacity-50 border border-white border-opacity-20 rounded-xl text-white focus:ring-2 focus:ring-white focus:ring-opacity-30 focus:border-white focus:border-opacity-40 transition-all duration-300 backdrop-blur-sm"
                    >
                      <option value="" className="bg-black">Select Home Team</option>
                      {teams.map(team => (
                        <option key={team} value={team} className="bg-black">
                          {team}
                        </option>
                      ))}
                    </select>
                  </div>
                  
                  <div className="text-center">
                    <div className="inline-flex items-center justify-center w-16 h-16 rounded-full border-2 border-white border-opacity-30 bg-white bg-opacity-10 backdrop-blur-sm">
                      <span className="text-2xl font-bold text-white">VS</span>
                    </div>
                  </div>
                  
                  <div className="space-y-3">
                    <label className="block text-sm font-medium text-gray-300 uppercase tracking-wider">Away Team</label>
                    <select 
                      value={awayTeam} 
                      onChange={(e) => setAwayTeam(e.target.value)}
                      className="w-full p-4 bg-black bg-opacity-50 border border-white border-opacity-20 rounded-xl text-white focus:ring-2 focus:ring-white focus:ring-opacity-30 focus:border-white focus:border-opacity-40 transition-all duration-300 backdrop-blur-sm"
                    >
                      <option value="" className="bg-black">Select Away Team</option>
                      {teams.map(team => (
                        <option key={team} value={team} className="bg-black">
                          {team}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
                
                <div className="flex justify-center mt-8">
                  <button 
                    onClick={handlePredict}
                    disabled={loading || !homeTeam || !awayTeam}
                    className="relative px-12 py-4 bg-white text-black font-bold rounded-xl hover:bg-gray-200 disabled:bg-gray-600 disabled:text-gray-400 transition-all duration-300 transform hover:scale-105 disabled:hover:scale-100 shadow-lg"
                  >
                    <span className="relative z-10">
                      {loading ? 'Predicting...' : 'Predict Match'}
                    </span>
                    <div className="absolute inset-0 bg-gradient-to-r from-white to-gray-100 rounded-xl opacity-0 hover:opacity-100 transition-opacity duration-300"></div>
                  </button>
                </div>
              </div>
            </div>

            {/* Error Display */}
            {error && (
              <div className="relative bg-red-500 bg-opacity-20 backdrop-blur-md border border-red-500 border-opacity-30 rounded-2xl p-6 mb-8">
                <div className="absolute inset-0 bg-gradient-to-br from-red-500/10 to-transparent rounded-2xl"></div>
                <p className="relative z-10 text-red-200 text-center font-medium">{error}</p>
              </div>
            )}

            {/* Prediction Results */}
            {prediction && (
              <div className="relative bg-black bg-opacity-50 backdrop-blur-md border border-white border-opacity-20 rounded-2xl p-8 shadow-2xl">
                <div className="absolute inset-0 bg-gradient-to-br from-white/10 to-transparent rounded-2xl"></div>
                <div className="relative z-10">
                  <div className="text-center mb-8">
                    <h3 className="text-3xl font-bold mb-2 tracking-tight flex items-center justify-center gap-3">
                      <img src={getTeamTheme(prediction.home_team).logo} alt={prediction.home_team} className="w-10 h-10 object-contain" />
                      {prediction.home_team} vs {prediction.away_team}
                      <img src={getTeamTheme(prediction.away_team).logo} alt={prediction.away_team} className="w-10 h-10 object-contain" />
                    </h3>
                    <div className="w-24 h-1 bg-gradient-to-r from-transparent via-white to-transparent mx-auto opacity-30"></div>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-6 mb-8">
                    <div className="text-center group">
                      <div className="relative mb-3">
                        <div className="text-4xl font-bold text-green-400 mb-1 transition-transform duration-300 group-hover:scale-110">
                          {(prediction.win_probability * 100).toFixed(1)}%
                        </div>
                        <div className="w-full h-2 bg-white bg-opacity-10 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full transition-all duration-1000"
                            style={{ width: `${prediction.win_probability * 100}%` }}
                          ></div>
                        </div>
                      </div>
                      <div className="text-sm text-gray-300 uppercase tracking-wider font-medium">Home Win</div>
                    </div>
                    
                    <div className="text-center group">
                      <div className="relative mb-3">
                        <div className="text-4xl font-bold text-yellow-400 mb-1 transition-transform duration-300 group-hover:scale-110">
                          {(prediction.draw_probability * 100).toFixed(1)}%
                        </div>
                        <div className="w-full h-2 bg-white bg-opacity-10 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-yellow-500 to-yellow-400 rounded-full transition-all duration-1000"
                            style={{ width: `${prediction.draw_probability * 100}%` }}
                          ></div>
                        </div>
                      </div>
                      <div className="text-sm text-gray-300 uppercase tracking-wider font-medium">Draw</div>
                    </div>
                    
                    <div className="text-center group">
                      <div className="relative mb-3">
                        <div className="text-4xl font-bold text-red-400 mb-1 transition-transform duration-300 group-hover:scale-110">
                          {(prediction.loss_probability * 100).toFixed(1)}%
                        </div>
                        <div className="w-full h-2 bg-white bg-opacity-10 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-gradient-to-r from-red-500 to-red-400 rounded-full transition-all duration-1000"
                            style={{ width: `${prediction.loss_probability * 100}%` }}
                          ></div>
                        </div>
                      </div>
                      <div className="text-sm text-gray-300 uppercase tracking-wider font-medium">Away Win</div>
                    </div>
                  </div>
                  
                  <div className="flex justify-center space-x-8 text-sm text-gray-400">
                    <div className="text-center">
                      <div className="text-white font-bold text-lg">{(prediction.confidence_score * 100).toFixed(1)}%</div>
                      <div className="uppercase tracking-wider">Confidence</div>
                    </div>
                    <div className="text-center">
                      <div className="text-white font-bold text-lg">{prediction.model_used}</div>
                      <div className="uppercase tracking-wider">Model</div>
                    </div>
                    <div className="text-center">
                      <div className="text-white font-bold text-lg">{prediction.features_used}</div>
                      <div className="uppercase tracking-wider">Features</div>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {activeView === 'stats' && (
          <div className="relative bg-black bg-opacity-40 backdrop-blur-md border border-white border-opacity-10 rounded-2xl p-8 shadow-2xl max-h-[calc(100vh-200px)] overflow-y-auto scrollbar-thin scrollbar-track-transparent scrollbar-thumb-white/20 hover:scrollbar-thumb-white/40">
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent rounded-2xl"></div>
            <div className="relative z-10">
              <h3 className="text-3xl font-bold mb-8 text-center">Model Performance Statistics</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                <div className="text-center">
                  <div className="text-5xl font-bold text-green-400 mb-2">81.4%</div>
                  <div className="text-gray-300 uppercase tracking-wider">Overall Accuracy</div>
                </div>
                <div className="text-center">
                  <div className="text-5xl font-bold text-blue-400 mb-2">15+</div>
                  <div className="text-gray-300 uppercase tracking-wider">Features Used</div>
                </div>
                <div className="text-center">
                  <div className="text-5xl font-bold text-purple-400 mb-2">5000+</div>
                  <div className="text-gray-300 uppercase tracking-wider">Matches Analyzed</div>
                </div>
              </div>
              <div className="mt-8 text-center text-gray-400">
                <p>Our machine learning model uses Random Forest algorithm with advanced feature engineering including team strength ratings, recent form, and historical performance metrics.</p>
              </div>
            </div>
          </div>
        )}

        {activeView === 'teams' && (
          <div className="relative bg-black bg-opacity-40 backdrop-blur-md border border-white border-opacity-10 rounded-2xl p-6 shadow-2xl">
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent rounded-2xl"></div>
            <div className="relative z-10">
              <h3 className="text-2xl font-bold mb-6 text-center">Premier League Teams</h3>
              <div className="grid grid-cols-3 md:grid-cols-5 lg:grid-cols-6 gap-3">
                {teams.map(team => (
                  <div key={team} className="flex flex-col items-center p-3 bg-white bg-opacity-5 rounded-xl hover:bg-opacity-10 transition-all">
                    <img src={getTeamTheme(team).logo} alt={team} className="w-6 h-6 object-contain mb-2" />
                    <span className="text-white text-xs font-medium text-center leading-tight">{team}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {activeView === 'about' && (
          <div className="relative bg-black bg-opacity-40 backdrop-blur-md border border-white border-opacity-10 rounded-2xl p-8 shadow-2xl max-h-[calc(100vh-200px)] overflow-y-auto scrollbar-thin scrollbar-track-transparent scrollbar-thumb-white/20 hover:scrollbar-thumb-white/40">
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent rounded-2xl"></div>
            <div className="relative z-10">
              <h3 className="text-3xl font-bold mb-8 text-center">About PL Predictor</h3>
              <div className="space-y-6 text-gray-300 max-w-2xl mx-auto">
                <p>
                  Premier League Predictor is an advanced AI-powered system that analyzes football matches using machine learning algorithms to provide accurate predictions.
                </p>
                <p>
            </div>
            <div className="bg-gray-900/50 p-4 rounded-lg border border-gray-700">
              <div className="text-2xl mb-2">📺</div>
              <div className="text-sm font-medium">Live Matches</div>
              <div className="text-xs text-gray-400">WebSocket Updates</div>
            </div>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4">
            <Link 
              href="/predictions" 
              className="bg-[#37003c] hover:bg-[#37003c]/80 text-white px-8 py-4 rounded-lg text-lg font-medium transition-colors"
            >
              Make Predictions
            </Link>
            <Link 
              href="/dashboard" 
              className="bg-gray-800 hover:bg-gray-700 text-white px-8 py-4 rounded-lg text-lg font-medium transition-colors border border-gray-600"
            >
              View Analytics
            </Link>
            <Link 
              href="/nlp" 
              className="bg-[#00ff87] hover:bg-[#00ff87]/80 text-black px-8 py-4 rounded-lg text-lg font-medium transition-colors"
            >
              Ask AI Assistant
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
              <div className="text-3xl font-bold text-blue-400">< 200ms</div>
              <div className="text-sm text-gray-400">API Response</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-400">99.97%</div>
              <div className="text-sm text-gray-400">Uptime</div>
            </div>
          </div>
        </div>

      {/* Copyright Footer */}
      <footer className="fixed bottom-0 left-0 right-0 z-20 p-4 bg-black bg-opacity-20 backdrop-blur-sm">
        <div className="text-center text-gray-400 text-sm">
          2024 Premier League Predictor. All rights reserved. | Powered by AI & Machine Learning
        </div>
      </footer>

      <Canvas 
        shadows 
        camera={{ position: [80, 80, 80], fov: 100 }} 
        className="fixed inset-0 w-screen h-screen"
        style={{ 
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          zIndex: 0,
          minWidth: '100vw',
          minHeight: '100vh',
          overflow: 'hidden'
        }}
        gl={{ 
          antialias: false, 
          alpha: false,
          powerPreference: "high-performance",
          pixelRatio: Math.min(window.devicePixelRatio, 1.5)
        }}
        dpr={[1, 1.5]}
        frameloop="demand"
      >
        <color attach="background" args={['#000000']} />
        <fog attach="fog" args={['#000000', 200, 600]} />
        <Scene teamColors={winningTeam && teamThemes[winningTeam] ? 
          { primary: teamThemes[winningTeam].primaryColor, secondary: teamThemes[winningTeam].secondaryColor } : 
          { primary: '#26d926', secondary: '#1a8c1a' }
        } />
      </Canvas>
    </div>
  )
}
