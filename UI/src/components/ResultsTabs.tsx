import React from 'react';
import { Tabs, Tab, Box } from '@mui/material';

export interface ResultsTabsProps {
  tabLabels: string[];
  currentTab: number;
  onTabChange: (event: React.SyntheticEvent, newValue: number) => void;
  children: React.ReactNode[];
}

export default function ResultsTabs({ tabLabels, currentTab, onTabChange, children }: ResultsTabsProps) {
  return (
    <Box
      sx={{
        width: '100%',
        background: 'var(--code-bg, #f4f3ec)',
        borderRadius: 4,
        boxShadow: '0 2px 12px rgba(0,0,0,0.07)',
        p: { xs: 1, sm: 2, md: 3 },
        mb: 4,
      }}
    >
      <Tabs
        value={currentTab}
        onChange={onTabChange}
        centered
        sx={{
          borderBottom: '1px solid var(--border, #e5e4e7)',
          minHeight: 48,
          '.MuiTab-root': {
            fontWeight: 600,
            fontSize: 18,
            color: 'var(--text, #6b6375)',
            textTransform: 'none',
            minHeight: 48,
          },
          '.Mui-selected': {
            color: 'var(--accent, #aa3bff)',
          },
          '.MuiTabs-indicator': {
            backgroundColor: 'var(--accent, #aa3bff)',
            height: 3,
            borderRadius: 2,
          },
        }}
      >
        {tabLabels.map((label) => (
          <Tab key={label} label={label} />
        ))}
      </Tabs>
      <Box sx={{ mt: 3 }}>{children[currentTab]}</Box>
    </Box>
  );
}
