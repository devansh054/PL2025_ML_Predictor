import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import '@testing-library/jest-dom'
import PremierLeaguePredictor from '../app/page'

// Mock the Canvas component from @react-three/fiber
jest.mock('@react-three/fiber', () => ({
  Canvas: ({ children }: { children: React.ReactNode }) => <div data-testid="canvas">{children}</div>,
}))

// Mock axios
jest.mock('axios', () => ({
  get: jest.fn(),
  post: jest.fn(),
}))

const mockAxios = require('axios')

describe('Premier League Predictor', () => {
  beforeEach(() => {
    mockAxios.get.mockClear()
    mockAxios.post.mockClear()
  })

  it('renders the main heading', () => {
    render(<PremierLeaguePredictor />)
    expect(screen.getByText('PL Predictor')).toBeInTheDocument()
  })

  it('renders navigation buttons', () => {
    render(<PremierLeaguePredictor />)
    expect(screen.getByText('Predictions')).toBeInTheDocument()
    expect(screen.getByText('Stats')).toBeInTheDocument()
    expect(screen.getByText('Teams')).toBeInTheDocument()
    expect(screen.getByText('About')).toBeInTheDocument()
  })

  it('shows team selection dropdowns on home view', () => {
    render(<PremierLeaguePredictor />)
    expect(screen.getByText('Home Team')).toBeInTheDocument()
    expect(screen.getByText('Away Team')).toBeInTheDocument()
  })

  it('switches to stats view when stats button is clicked', async () => {
    render(<PremierLeaguePredictor />)
    
    const statsButton = screen.getByText('Stats')
    fireEvent.click(statsButton)
    
    await waitFor(() => {
      expect(screen.getByText('Model Performance')).toBeInTheDocument()
    })
  })

  it('switches to teams view when teams button is clicked', async () => {
    render(<PremierLeaguePredictor />)
    
    const teamsButton = screen.getByText('Teams')
    fireEvent.click(teamsButton)
    
    await waitFor(() => {
      expect(screen.getByText('Premier League Teams')).toBeInTheDocument()
    })
  })

  it('switches to about view when about button is clicked', async () => {
    render(<PremierLeaguePredictor />)
    
    const aboutButton = screen.getByText('About')
    fireEvent.click(aboutButton)
    
    await waitFor(() => {
      expect(screen.getByText('About Premier League Predictor')).toBeInTheDocument()
    })
  })

  it('shows subtitle on non-home views', async () => {
    render(<PremierLeaguePredictor />)
    
    const statsButton = screen.getByText('Stats')
    fireEvent.click(statsButton)
    
    await waitFor(() => {
      expect(screen.getByText('AI-powered predictions with 81.4% accuracy using advanced ML models')).toBeInTheDocument()
    })
  })

  it('does not show subtitle on home view', () => {
    render(<PremierLeaguePredictor />)
    expect(screen.queryByText('AI-powered predictions with 81.4% accuracy using advanced ML models')).not.toBeInTheDocument()
  })

  it('renders canvas for 3D background', () => {
    render(<PremierLeaguePredictor />)
    expect(screen.getByTestId('canvas')).toBeInTheDocument()
  })

  it('makes prediction when predict button is clicked', async () => {
    mockAxios.post.mockResolvedValue({
      data: {
        home_win_prob: 0.45,
        draw_prob: 0.25,
        away_win_prob: 0.30,
        confidence: 0.85
      }
    })

    render(<PremierLeaguePredictor />)
    
    const predictButton = screen.getByText('Predict Match')
    fireEvent.click(predictButton)
    
    await waitFor(() => {
      expect(mockAxios.post).toHaveBeenCalledWith(
        'http://localhost:8000/predict',
        expect.any(Object)
      )
    })
  })
})
