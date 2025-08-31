export const teamLogos: Record<string, string> = {
  'Arsenal': '/logos/arsenal.svg',
  'Aston Villa': '/logos/aston-villa.svg',
  'Brighton & Hove Albion': '/logos/brighton.svg',
  'Brighton': '/logos/brighton.svg',
  'Burnley': '/logos/burnley.svg',
  'Chelsea': '/logos/chelsea.svg',
  'Crystal Palace': '/logos/crystal-palace.svg',
  'Everton': '/logos/everton.svg',
  'Fulham': '/logos/fulham.svg',
  'Liverpool': '/logos/liverpool.svg',
  'Luton Town': '/logos/luton.svg',
  'Manchester City': '/logos/manchester-city.svg',
  'Manchester United': '/logos/manchester-united.svg',
  'Newcastle United': '/logos/newcastle.svg',
  'Nottingham Forest': '/logos/nottingham-forest.svg',
  'Sheffield United': '/logos/sheffield-united.svg',
  'Tottenham Hotspur': '/logos/tottenham.svg',
  'West Ham United': '/logos/west-ham.svg',
  'Wolverhampton Wanderers': '/logos/wolves.svg',
  'Brentford': '/logos/brentford.svg'
};

export const getTeamLogo = (teamName: string): string => {
  return teamLogos[teamName] || '/logos/default.svg';
};
