import { AppBar, Toolbar, Typography, Box, Button } from '@mui/material';

export interface TopNavBarProps {
  tabs: string[];
  currentTab: number;
  onTabChange: (idx: number) => void;
}

export default function TopNavBar({ tabs, currentTab, onTabChange }: TopNavBarProps) {
  return (
    <AppBar position="static" color="primary" elevation={2}>
      <Toolbar sx={{ justifyContent: 'space-between' }}>
        <Typography variant="h5" sx={{ fontWeight: 700, letterSpacing: 1 }}>
          QASS Results Portal
        </Typography>
        <Box>
          {tabs.map((tab, idx) => (
            <Button
              key={tab}
              color={currentTab === idx ? 'secondary' : 'inherit'}
              onClick={() => onTabChange(idx)}
              sx={{
                fontWeight: currentTab === idx ? 700 : 500,
                fontSize: 18,
                mx: 1,
                borderBottom: currentTab === idx ? '2.5px solid #fff' : 'none',
                borderRadius: 0,
                textTransform: 'none',
              }}
            >
              {tab}
            </Button>
          ))}
        </Box>
      </Toolbar>
    </AppBar>
  );
}
