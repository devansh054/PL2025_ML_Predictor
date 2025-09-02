import '@testing-library/jest-dom'

// Mock all React Three Fiber and related libraries
jest.mock('@react-three/fiber', () => ({
  Canvas: ({ children }) => <div data-testid="canvas">{children}</div>,
  useFrame: jest.fn(),
  useThree: jest.fn(() => ({ viewport: { width: 1, height: 1 } })),
  extend: jest.fn(),
}))

jest.mock('@react-three/drei', () => ({
  OrbitControls: () => null,
  Text: ({ children }) => <div>{children}</div>,
  Box: () => <div data-testid="box" />,
  Sphere: () => <div data-testid="sphere" />,
  useTexture: jest.fn(() => ({})),
  Html: ({ children }) => <div>{children}</div>,
}))

jest.mock('three', () => ({
  Vector3: jest.fn(),
  Color: jest.fn(),
  MeshStandardMaterial: jest.fn(),
  BoxGeometry: jest.fn(),
  SphereGeometry: jest.fn(),
  Mesh: jest.fn(),
  Scene: jest.fn(),
  PerspectiveCamera: jest.fn(),
  WebGLRenderer: jest.fn(),
}))

jest.mock('framer-motion', () => ({
  motion: {
    div: ({ children, ...props }) => <div {...props}>{children}</div>,
    button: ({ children, ...props }) => <button {...props}>{children}</button>,
  },
  AnimatePresence: ({ children }) => <>{children}</>,
}))

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
  constructor() {}
  disconnect() {}
  observe() {}
  unobserve() {}
}

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(),
    removeListener: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock WebGL context for Three.js
const mockWebGLContext = {
  getExtension: () => null,
  getParameter: () => null,
  getShaderPrecisionFormat: () => ({ precision: 1, rangeMin: 1, rangeMax: 1 }),
}

HTMLCanvasElement.prototype.getContext = jest.fn((contextType) => {
  if (contextType === 'webgl' || contextType === 'webgl2') {
    return mockWebGLContext
  }
  return null
})
