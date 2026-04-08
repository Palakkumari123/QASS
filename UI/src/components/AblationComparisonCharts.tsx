
import React, { useState } from 'react';
import { Bar } from 'react-chartjs-2';
import { Box, Paper, Typography, Tabs, Tab } from '@mui/material';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,  
  Legend,
} from 'chart.js';

import ChartDataLabels from 'chartjs-plugin-datalabels';
ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, ChartDataLabels);

import type { AblationDatum } from '../types/ablation';

// Default data (used if no CSV is loaded)
const defaultAblationData: AblationDatum[] = [
  {
    mode: 'baseline_full',
    unique_combo_count: 6,
    combo_entropy: 2.5,
    predictability_rate: 0.25,
    mean_abs_key_corr: 0.063,
    mean_hamming_rate: 0.525,
    mean_total_ms: 2384.2,
  },
  {
    mode: 'no_layer2_fixed_combo',
    unique_combo_count: 1,
    combo_entropy: 0.0,
    predictability_rate: 1.0,
    mean_abs_key_corr: 0.025,
    mean_hamming_rate: 0.508,
    mean_total_ms: 2272.7,
  },
  {
    mode: 'no_layer4_no_ratchet',
    unique_combo_count: 5,
    combo_entropy: 2.25,
    predictability_rate: 0.25,
    mean_abs_key_corr: 0.051,
    mean_hamming_rate: 0.520,
    mean_total_ms: 1395.5,
  },
  {
    mode: 'single_source_kyber',
    unique_combo_count: 1,
    combo_entropy: 0.0,
    predictability_rate: 1.0,
    mean_abs_key_corr: 0.0,
    mean_hamming_rate: 0.0,
    mean_total_ms: 1312.0,
  },
];


const metrics = [
  { key: 'unique_combo_count', label: 'Unique Combo Count', color: '#1976d2' },
  { key: 'combo_entropy', label: 'Combo Entropy', color: '#388e3c' },
  { key: 'predictability_rate', label: 'Predictability Rate', color: '#fbc02d' },
  { key: 'mean_abs_key_corr', label: 'Mean Abs Key Corr.', color: '#d84315' },
  { key: 'mean_hamming_rate', label: 'Mean Hamming Rate', color: '#6a1b9a' },
  { key: 'mean_total_ms', label: 'Mean Total Time (ms)', color: '#00838f' },
];





type Props = {
  ablationData?: AblationDatum[];
};


export const AblationComparisonCharts: React.FC<Props> = ({ ablationData = defaultAblationData }) => {
  const [selectedMetric, setSelectedMetric] = useState(0);
  const metric = metrics[selectedMetric];
  return (
    <Box>
      <Typography variant="h6" gutterBottom>Ablation Architecture Comparison</Typography>
      <Tabs
        value={selectedMetric}
        onChange={(_e, idx) => setSelectedMetric(idx as number)}
        variant="scrollable"
        scrollButtons="auto"
        sx={{ mb: 2, minHeight: 40, '.MuiTab-root': { minHeight: 40 } }}
      >
        {metrics.map((m) => (
          <Tab key={m.key} label={m.label} />
        ))}
      </Tabs>
      <Paper elevation={2} sx={{ p: 2, mb: 3 }}>
        <Typography variant="subtitle1" gutterBottom>{metric.label}</Typography>
        <Bar
          data={{
            labels: ablationData.map((d) =>
              d.mode
                .replace('baseline_full', 'Full (DSR)')
                .replace('no_layer2_fixed_combo', 'No DSR')
                .replace('no_layer4_no_ratchet', 'No Ratchet')
                .replace('single_source_kyber', 'Single Source')
            ),
            datasets: [
              {
                label: metric.label,
                data: ablationData.map((d) => d[metric.key as keyof AblationDatum] as number),
                backgroundColor: metric.color,
                borderRadius: 8,
              },
            ],
          }}
          options={{
            responsive: true,
            plugins: {
              legend: { display: false },
              title: { display: false },
              tooltip: {
                callbacks: {
                  label: (ctx: import('chart.js').TooltipItem<'bar'>) => {
                    const label = ctx.dataset.label ?? '';
                    const value = ctx.parsed.y ?? '';
                    return `${label}: ${value}`;
                  },
                },
              },
              datalabels: {
                display: true,
                anchor: 'end',
                align: 'top',
                color: '#222',
                font: { weight: 'bold', size: 14 },
                formatter: (value: number) => value.toFixed(2),
              },
            },
            scales: {
              y: {
                beginAtZero: true,
                ticks: {
                  font: { size: 14 },
                  color: '#444',
                },
                grid: { color: '#e0e0e0' },
              },
              x: {
                ticks: {
                  font: { size: 14 },
                  color: '#444',
                },
                grid: { display: false },
              },
            },
          }}
          plugins={[ChartDataLabels]}
        />
      </Paper>
    </Box>
  );
};
