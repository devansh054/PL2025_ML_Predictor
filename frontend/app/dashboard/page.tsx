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
    { name: 'NLP Analysis', href: '/nlp' },
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

// Dynamic imports for charts to avoid SSR issues
import dynamic from 'next/dynamic';
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface DashboardMetric {
  name: string;
  value: number;
  change: number;
  trend: string;
  format_type: string;
  description: string;
}

interface ChartData {
  chart_id: string;
  title: string;
  chart_type: string;
  data: any;
  config: any;
  insights: string[];
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

export default function Dashboard() {
  const [metrics, setMetrics] = useState<DashboardMetric[]>([]);
  const [charts, setCharts] = useState<ChartData[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      // Mock data for now - in production would fetch from backend
      const mockMetrics: DashboardMetric[] = [
        {
          name: "Model Accuracy",
          value: 81.4,
          change: 2.3,
          trend: "up",
          format_type: "percentage",
          description: "Overall prediction accuracy across all models"
        },
        {
          name: "Predictions Today",
          value: 1247,
          change: 15.8,
          trend: "up",
          format_type: "number",
          description: "Total predictions made in the last 24 hours"
        },
        {
          name: "Active Users",
          value: 89,
          change: -5.2,
          trend: "down",
          format_type: "number",
          description: "Currently active users on the platform"
        },
        {
          name: "Avg Response Time",
          value: 0.234,
          change: -12.1,
          trend: "up",
          format_type: "time",
          description: "Average API response time in seconds"
        }
      ];

      const mockCharts: ChartData[] = [
        {
          chart_id: "accuracy_trends",
          title: "Model Accuracy Trends",
          chart_type: "line",
          data: {
            data: [
              {
                x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                y: [78.2, 79.1, 80.3, 81.0, 81.4, 81.7],
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Random Forest',
                line: { color: '#37003c' }
              },
              {
                x: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
                y: [76.5, 77.2, 78.8, 79.5, 79.8, 80.1],
                type: 'scatter',
                mode: 'lines+markers',
                name: 'Gradient Boosting',
                line: { color: '#00ff87' }
              }
            ],
            layout: {
              title: 'Model Accuracy Over Time',
              xaxis: { title: 'Month' },
              yaxis: { title: 'Accuracy (%)' },
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              font: { color: 'white' }
            }
          },
          config: { displayModeBar: false },
          insights: [
            "Random Forest shows consistent improvement",
            "6-month accuracy trend is positive",
            "Current model performance exceeds target"
          ]
        },
        {
          chart_id: "team_performance",
          title: "Team Performance Heatmap",
          chart_type: "heatmap",
          data: {
            data: [{
              z: [
                [85, 78, 92, 88, 76],
                [82, 85, 89, 91, 79],
                [79, 82, 87, 85, 82],
                [88, 91, 94, 89, 85],
                [75, 78, 81, 83, 77]
              ],
              x: ['Goals For', 'Goals Against', 'Possession', 'Pass Accuracy', 'Shots on Target'],
              y: ['Arsenal', 'Chelsea', 'Liverpool', 'Man City', 'Man United'],
              type: 'heatmap',
              colorscale: 'RdYlGn'
            }],
            layout: {
              title: 'Team Performance Matrix',
              paper_bgcolor: 'rgba(0,0,0,0)',
              plot_bgcolor: 'rgba(0,0,0,0)',
              font: { color: 'white' }
            }
          },
          config: { displayModeBar: false },
          insights: [
            "Man City leads in possession metrics",
            "Arsenal shows balanced performance",
            "Liverpool excels in attacking stats"
          ]
        }
      ];

      setMetrics(mockMetrics);
      setCharts(mockCharts);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      setLoading(false);
    }
  };

  const formatValue = (value: number, type: string) => {
    switch (type) {
      case 'percentage':
        return `${value}%`;
      case 'time':
        return `${value}s`;
      case 'number':
        return value.toLocaleString();
      default:
        return value.toString();
    }
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return '↗️';
      case 'down':
        return '↘️';
      default:
        return '➡️';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-[#37003c] mx-auto mb-4"></div>
          <p className="text-xl">Loading Advanced Analytics...</p>
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

      {/* Dashboard Content */}
      <div className="relative z-10 p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-4xl font-bold mb-2">Advanced Analytics Dashboard</h1>
          <p className="text-gray-400">Real-time insights and performance metrics</p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex space-x-4 mb-8">
          {['overview', 'models', 'performance', 'insights'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-[#37003c] text-white'
                  : 'bg-gray-800 text-gray-400 hover:text-white'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <>
            {/* KPI Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {metrics.map((metric, index) => (
                <div key={index} className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-sm font-medium text-gray-400">{metric.name}</h3>
                    <span className="text-lg">{getTrendIcon(metric.trend)}</span>
                  </div>
                  <div className="text-2xl font-bold mb-1">
                    {formatValue(metric.value, metric.format_type)}
                  </div>
                  <div className={`text-sm ${
                    metric.change > 0 ? 'text-green-400' : 'text-red-400'
                  }`}>
                    {metric.change > 0 ? '+' : ''}{metric.change}% from last period
                  </div>
                  <p className="text-xs text-gray-500 mt-2">{metric.description}</p>
                </div>
              ))}
            </div>

            {/* Real-time Features Section */}
            <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800">
              <h3 className="text-xl font-bold mb-4">Real-time System Status</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  <div className="text-3xl font-bold text-green-400">99.97%</div>
                  <div className="text-sm text-gray-400">System Uptime</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-blue-400">847</div>
                  <div className="text-sm text-gray-400">Requests/sec</div>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold text-purple-400">94.7%</div>
                  <div className="text-sm text-gray-400">Cache Hit Rate</div>
                </div>
              </div>
            </div>
          </>
        )}

        {activeTab === 'models' && (
          <div className="space-y-8">
            <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800">
              <h3 className="text-xl font-bold mb-4">ML Model Performance</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-3xl font-bold text-green-400">81.4%</div>
                  <div className="text-sm text-gray-400">Random Forest Accuracy</div>
                </div>
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-3xl font-bold text-blue-400">78.9%</div>
                  <div className="text-sm text-gray-400">XGBoost Accuracy</div>
                </div>
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-3xl font-bold text-purple-400">76.2%</div>
                  <div className="text-sm text-gray-400">Neural Network Accuracy</div>
                </div>
              </div>
            </div>
            
            <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800">
              <h3 className="text-xl font-bold mb-4">Model Features</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <h4 className="font-medium text-gray-300">Primary Features</h4>
                  <ul className="text-sm text-gray-400 space-y-1">
                    <li>• Team Form (Last 5 matches)</li>
                    <li>• Head-to-head Record</li>
                    <li>• Home/Away Performance</li>
                    <li>• Goals Scored/Conceded</li>
                  </ul>
                </div>
                <div className="space-y-2">
                  <h4 className="font-medium text-gray-300">Advanced Features</h4>
                  <ul className="text-sm text-gray-400 space-y-1">
                    <li>• ELO Rating System</li>
                    <li>• Player Availability</li>
                    <li>• Weather Conditions</li>
                    <li>• Match Importance</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'performance' && (
          <div className="space-y-8">
            {/* Charts Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {charts.map((chart, index) => (
                <div key={index} className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800">
                  <h3 className="text-xl font-bold mb-4">{chart.title}</h3>
                  <div className="h-80">
                    <Plot
                      data={chart.data.data}
                      layout={{
                        ...chart.data.layout,
                        autosize: true,
                        margin: { l: 50, r: 50, t: 50, b: 50 }
                      }}
                      config={chart.config}
                      style={{ width: '100%', height: '100%' }}
                      useResizeHandler={true}
                      {...({} as any)}
                    />
                  </div>
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-400 mb-2">Key Insights:</h4>
                    <ul className="text-sm text-gray-300 space-y-1">
                      {chart.insights.map((insight, i) => (
                        <li key={i} className="flex items-center">
                          <span className="w-2 h-2 bg-[#37003c] rounded-full mr-2"></span>
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>

            <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800">
              <h3 className="text-xl font-bold mb-4">Performance Metrics</h3>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-green-400">94.2%</div>
                  <div className="text-sm text-gray-400">Precision</div>
                </div>
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-400">89.7%</div>
                  <div className="text-sm text-gray-400">Recall</div>
                </div>
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-purple-400">91.8%</div>
                  <div className="text-sm text-gray-400">F1-Score</div>
                </div>
                <div className="text-center p-4 bg-gray-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-400">0.23</div>
                  <div className="text-sm text-gray-400">Log Loss</div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'insights' && (
          <div className="space-y-8">
            <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800">
              <h3 className="text-xl font-bold mb-4">Key Insights & Trends</h3>
              <div className="space-y-6">
                <div className="p-4 bg-gradient-to-r from-green-500/10 to-green-600/10 rounded-lg border border-green-500/20">
                  <h4 className="font-bold text-green-400 mb-2">🏆 Top Performing Teams</h4>
                  <p className="text-gray-300">Manchester City maintains the highest win probability at home (78%), followed by Arsenal (72%) and Liverpool (69%).</p>
                </div>
                
                <div className="p-4 bg-gradient-to-r from-blue-500/10 to-blue-600/10 rounded-lg border border-blue-500/20">
                  <h4 className="font-bold text-blue-400 mb-2">📊 Model Accuracy Trends</h4>
                  <p className="text-gray-300">Random Forest model shows 15% improvement in accuracy over the past month, particularly in predicting away team victories.</p>
                </div>
                
                <div className="p-4 bg-gradient-to-r from-purple-500/10 to-purple-600/10 rounded-lg border border-purple-500/20">
                  <h4 className="font-bold text-purple-400 mb-2">⚽ Match Patterns</h4>
                  <p className="text-gray-300">Home advantage has decreased by 8% this season, with away teams winning 32% more matches compared to last season.</p>
                </div>
                
                <div className="p-4 bg-gradient-to-r from-yellow-500/10 to-yellow-600/10 rounded-lg border border-yellow-500/20">
                  <h4 className="font-bold text-yellow-400 mb-2">🔮 Prediction Confidence</h4>
                  <p className="text-gray-300">Model confidence is highest for matches involving top-6 teams (89% avg) and lowest for newly promoted teams (67% avg).</p>
                </div>
              </div>
            </div>

            <div className="bg-gray-900/80 backdrop-blur-sm rounded-lg p-6 border border-gray-800">
              <h3 className="text-xl font-bold mb-4">Recent Discoveries</h3>
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-300 mb-3">Key Performance Metrics</h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-400">Model Accuracy</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-20 bg-gray-700 rounded-full h-2">
                          <div className="bg-green-400 h-2 rounded-full" style={{width: '81%'}}></div>
                        </div>
                        <span className="text-xs text-gray-400">81%</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-400">Prediction Confidence</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-20 bg-gray-700 rounded-full h-2">
                          <div className="bg-blue-400 h-2 rounded-full" style={{width: '72%'}}></div>
                        </div>
                        <span className="text-xs text-gray-400">72%</span>
                      </div>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-400">Home Advantage</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-20 bg-gray-700 rounded-full h-2">
                          <div className="bg-purple-400 h-2 rounded-full" style={{width: '58%'}}></div>
                        </div>
                        <span className="text-xs text-gray-400">58%</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-300 mb-3">Seasonal Trends</h4>
                  <ul className="text-sm text-gray-400 space-y-2">
                    <li>• Goals per match increased by 12% this season</li>
                    <li>• Draw percentage decreased to 22% (lowest in 5 years)</li>
                    <li>• Late goals (80+ min) account for 28% of match outcomes</li>
                    <li>• Weather impact on scoring reduced due to improved pitches</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-gray-500">
          <p>Advanced Analytics • Real-time Monitoring • ML Pipeline Status</p>
        </div>
      </div>
    </div>
  );
}
