-- Initialize database schema for Premier League Predictor

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Teams table
CREATE TABLE IF NOT EXISTS teams (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL UNIQUE,
    logo_url VARCHAR(500),
    primary_color VARCHAR(7),
    secondary_color VARCHAR(7),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Matches table
CREATE TABLE IF NOT EXISTS matches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    home_team_id UUID REFERENCES teams(id),
    away_team_id UUID REFERENCES teams(id),
    home_score INTEGER,
    away_score INTEGER,
    match_date DATE NOT NULL,
    season VARCHAR(10) NOT NULL,
    gameweek INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Predictions table
CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    home_team_id UUID REFERENCES teams(id),
    away_team_id UUID REFERENCES teams(id),
    predicted_home_score FLOAT,
    predicted_away_score FLOAT,
    confidence_score FLOAT,
    model_version VARCHAR(50),
    prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actual_home_score INTEGER,
    actual_away_score INTEGER,
    is_correct BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Model performance tracking
CREATE TABLE IF NOT EXISTS model_performance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_name VARCHAR(100) NOT NULL,
    model_version VARCHAR(50) NOT NULL,
    accuracy FLOAT,
    precision_score FLOAT,
    recall_score FLOAT,
    f1_score FLOAT,
    training_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Feature importance tracking
CREATE TABLE IF NOT EXISTS feature_importance (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_version VARCHAR(50) NOT NULL,
    feature_name VARCHAR(100) NOT NULL,
    importance_score FLOAT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User sessions for analytics
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) UNIQUE NOT NULL,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Prediction requests tracking
CREATE TABLE IF NOT EXISTS prediction_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id VARCHAR(100) REFERENCES user_sessions(session_id),
    home_team_id UUID REFERENCES teams(id),
    away_team_id UUID REFERENCES teams(id),
    response_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_teams ON matches(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_predictions_date ON predictions(prediction_date);
CREATE INDEX IF NOT EXISTS idx_predictions_teams ON predictions(home_team_id, away_team_id);
CREATE INDEX IF NOT EXISTS idx_model_performance_active ON model_performance(is_active);
CREATE INDEX IF NOT EXISTS idx_user_sessions_activity ON user_sessions(last_activity);

-- Insert initial teams data
INSERT INTO teams (name, logo_url, primary_color, secondary_color) VALUES
('Arsenal', 'https://logos.footystats.org/england/arsenal-fc.png', '#EF0107', '#FFFFFF'),
('Chelsea', 'https://logos.footystats.org/england/chelsea-fc.png', '#034694', '#FFFFFF'),
('Liverpool', 'https://logos.footystats.org/england/liverpool-fc.png', '#C8102E', '#FFFFFF'),
('Manchester City', 'https://logos.footystats.org/england/manchester-city-fc.png', '#6CABDD', '#FFFFFF'),
('Manchester United', 'https://logos.footystats.org/england/manchester-united-fc.png', '#DA020E', '#FFFFFF'),
('Tottenham', 'https://logos.footystats.org/england/tottenham-hotspur-fc.png', '#132257', '#FFFFFF'),
('Newcastle United', 'https://logos.footystats.org/england/newcastle-united-fc.png', '#241F20', '#FFFFFF'),
('Brighton', 'https://logos.footystats.org/england/brighton-hove-albion-fc.png', '#0057B8', '#FFCD00'),
('Aston Villa', 'https://logos.footystats.org/england/aston-villa-fc.png', '#95BFE5', '#670E36'),
('West Ham', 'https://logos.footystats.org/england/west-ham-united-fc.png', '#7A263A', '#F3D459')
ON CONFLICT (name) DO NOTHING;
