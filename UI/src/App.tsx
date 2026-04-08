


import { Container, Typography, Box, Button } from '@mui/material';
import { useState } from 'react';
import { ImageCarousel } from './components/ImageCarousel';
import { FileUploadSection } from './components/FileUploadSection';

type NavigationState = 'main' | 'ablation' | 'grover' | 'shors' | 'architecture' | 'upload' | 'qlayer' | 'phase4' | 'pqc';

function App() {
  const [currentPage, setCurrentPage] = useState<NavigationState>('main');
  const [pngUrl, setPngUrl] = useState<string | undefined>(undefined);
  const [csvName, setCsvName] = useState<string | undefined>(undefined);

  // Grover and Shor's image paths
  const groverImages = [
    '/grover/depth_scaling.png',
    '/grover/gate_scaling.png',
    '/grover/iterations_scaling.png',
    '/grover/runtime_exponential_fit.png',
    '/grover/runtime_log_scaling.png',
    '/grover/success_probability.png',
  ];

  const shorsImages = [
    '/shors/shors_depth_scaling.png',
    '/shors/shors_gate_scaling.png',
    '/shors/shors_period.png',
    '/shors/shors_runtime_scaling.png',
  ];

  const qlayerImages = [
    '/qlayer/bb84_key_rate_vs_distance.png',
    '/qlayer/bb84_qber_vs_distance.png',
    '/qlayer/bb84_photon_loss.png',
    '/qlayer/bb84_sifted_key_length.png',
  ];

  const phase4Images = [
    '/phase4/abstract_ablation_dsr_impact.png',
    '/phase4/abstract_ratchet_independence.png',
    '/phase4/abstract_reliability_monitoring.png',
    '/phase4/abstract_selector_uniformity.png',
    '/phase4/qass_ablation_plot.png',
    '/phase4/qass_cipher_comparison.png',
    '/phase4/qass_combination_distribution.png',
    '/phase4/qass_layer_timing_breakdown.png',
    '/phase4/qass_ratchet_key_divergence.png',
    '/phase4/qass_security_monitor_dashboard.png',
    '/phase4/qass_session_key_entropy.png',
  ];

  const pqcImages = [
    '/pqc/fv_correctness.png',
    '/pqc/fv_timing_distribution.png',
    '/pqc/fv_timing_summary.png',
    '/pqc/pqc_ciphertext_size.png',
    '/pqc/pqc_enc_dec_time.png',
    '/pqc/pqc_pubkey_size.png',
    '/pqc/pqc_summary.png',
  ];

  const handleBackToMain = () => {
    setCurrentPage('main');
  };

  const handleCSVUpload = (file: File) => {
    setCsvName(file.name);
  };

  const handlePNGUpload = (file: File) => {
    setPngUrl(URL.createObjectURL(file));
  };

  const handleSelectOption = (option: 'grover' | 'shors') => {
    setCurrentPage(option);
  };

  const navigateToPage = (page: NavigationState) => {
    setCurrentPage(page);
  };
  return (
    <Box
      sx={{
        minHeight: '100vh',
        width: '100%',
        background: 'radial-gradient(circle at 20% 20%, rgba(79, 165, 255, 0.16), transparent 26%), radial-gradient(circle at 80% 12%, rgba(95, 200, 255, 0.12), transparent 18%), linear-gradient(180deg, #070b17 0%, #10182f 100%)',
        color: '#e7f2ff',
        overflowX: 'hidden',
        overflowY: 'auto',
        py: 4,
      }}
    >
      <Container
        maxWidth="lg"
        sx={{
          position: 'relative',
          zIndex: 1,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 4,
          px: { xs: 2, md: 3 },
        }}
      >
        {/* Main Page */}
        {currentPage === 'main' && (
          <>
            <Box
              sx={{
                width: '100%',
                maxWidth: 1080,
                p: { xs: 4, md: 5 },
                borderRadius: '32px',
                border: '1px solid rgba(70, 157, 255, 0.25)',
                background: 'rgba(10, 25, 53, 0.78)',
                backdropFilter: 'blur(30px)',
                boxShadow: '0 32px 90px rgba(8, 24, 56, 0.35)',
                textAlign: 'center',
              }}
            >
              <Typography variant="h3" sx={{ fontWeight: 800, letterSpacing: 1, mb: 2 }}>
                QASS Portal
              </Typography>
              <Box
                sx={{
                  height: 4,
                  width: 140,
                  mx: 'auto',
                  borderRadius: 2,
                  background: 'linear-gradient(90deg, rgba(82,179,255,1), rgba(111,195,255,0.76))',
                  mb: 3,
                }}
              />
              <Typography variant="body1" sx={{ maxWidth: 780, mx: 'auto', color: 'rgba(233, 244, 255, 0.82)' }}>
                Explore quantum threat analysis and ablation metrics in the QASS Portal.
              </Typography>
            </Box>

            <Box
              sx={{
                width: '100%',
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', md: 'repeat(3, minmax(0, 1fr))' },
                gap: 3,
              }}
            >
              {[
                {
                  key: 'architecture',
                  title: 'System Architecture',
                  description: 'View QASS system design and flow.',
                },
                {
                  key: 'ablation',
                  title: 'Threat Assessment',
                  description: 'Analyze Grover and Shor threat assessments.',
                },
                {
                  key: 'qlayer',
                  title: 'Quantum Layer Verification',
                  description: 'Inspect the quantum layer verification outputs.',
                },
                {
                  key: 'pqc',
                  title: 'PQC Assurance',
                  description: 'View post-quantum cryptography assurance plots.',
                },
                {
                  key: 'phase4',
                  title: 'Phase 4',
                  description: 'Review the Phase 4 QASS module details.',
                },
                {
                  key: 'upload',
                  title: 'Upload & Visualize',
                  description: 'Upload CSV/PNG data and preview results.',
                },
              ].map((section) => (
                <Box
                  key={section.key}
                  onClick={() => navigateToPage(section.key as NavigationState)}
                  sx={{
                    cursor: 'pointer',
                    p: 6,
                    borderRadius: '28px',
                    border: '1px solid rgba(92, 156, 255, 0.18)',
                    background: 'rgba(12, 29, 54, 0.74)',
                    backdropFilter: 'blur(22px)',
                    boxShadow: '0 14px 36px rgba(9, 26, 54, 0.18)',
                    transition: 'transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease',
                    textAlign: 'center',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      borderColor: 'rgba(100, 175, 255, 0.4)',
                      boxShadow: '0 22px 60px rgba(55, 130, 255, 0.24)',
                    },
                  }}
                >
                  <Typography variant="h5" sx={{ fontWeight: 700, mb: 2, color: '#dbe7ff' }}>
                    {section.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'rgba(220, 231, 255, 0.72)' }}>
                    {section.description}
                  </Typography>
                </Box>
              ))}
            </Box>
          </>
        )}

        {/* Ablation Submenu Page */}
        {currentPage === 'ablation' && (
          <Box
            sx={{
              width: '100%',
              maxWidth: 1080,
              p: { xs: 3, md: 4 },
              borderRadius: '34px',
              border: '1px solid rgba(97, 145, 255, 0.24)',
              background: 'rgba(8, 18, 42, 0.86)',
              backdropFilter: 'blur(28px)',
              boxShadow: '0 34px 88px rgba(8, 19, 44, 0.4)',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
              <Button
                variant="outlined"
                onClick={handleBackToMain}
                sx={{
                  borderColor: 'rgba(82, 179, 255, 0.5)',
                  color: '#b8d4ff',
                  '&:hover': {
                    borderColor: 'rgba(111, 195, 255, 0.8)',
                    backgroundColor: 'rgba(82, 179, 255, 0.08)',
                  },
                }}
              >
                ← Back
              </Button>
              <Typography variant="h4" sx={{ color: '#eef4ff', fontWeight: 700 }}>
                Threat Assessment
              </Typography>
            </Box>

            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: { xs: '1fr', md: '1fr 1fr' },
                gap: 4,
              }}
            >
              {/* Grover's Algorithm Card */}
              <Box
                onClick={() => handleSelectOption('grover')}
                sx={{
                  cursor: 'pointer',
                  p: 6,
                  borderRadius: '24px',
                  border: '1px solid rgba(92, 156, 255, 0.18)',
                  background: 'rgba(12, 29, 54, 0.74)',
                  backdropFilter: 'blur(22px)',
                  boxShadow: '0 14px 36px rgba(9, 26, 54, 0.18)',
                  transition: 'transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease',
                  textAlign: 'center',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    borderColor: 'rgba(100, 175, 255, 0.4)',
                    boxShadow: '0 22px 60px rgba(55, 130, 255, 0.24)',
                  },
                }}
              >
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, color: '#dbe7ff' }}>
                  Grover's Algorithm
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(220, 231, 255, 0.72)' }}>
                  Quantum search algorithm threat assessment
                </Typography>
              </Box>

              {/* Shor's Algorithm Card */}
              <Box
                onClick={() => handleSelectOption('shors')}
                sx={{
                  cursor: 'pointer',
                  p: 6,
                  borderRadius: '24px',
                  border: '1px solid rgba(92, 156, 255, 0.18)',
                  background: 'rgba(12, 29, 54, 0.74)',
                  backdropFilter: 'blur(22px)',
                  boxShadow: '0 14px 36px rgba(9, 26, 54, 0.18)',
                  transition: 'transform 0.3s ease, border-color 0.3s ease, box-shadow 0.3s ease',
                  textAlign: 'center',
                  '&:hover': {
                    transform: 'translateY(-4px)',
                    borderColor: 'rgba(100, 175, 255, 0.4)',
                    boxShadow: '0 22px 60px rgba(55, 130, 255, 0.24)',
                  },
                }}
              >
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, color: '#dbe7ff' }}>
                  Shor's Algorithm
                </Typography>
                <Typography variant="body2" sx={{ color: 'rgba(220, 231, 255, 0.72)' }}>
                  Quantum factoring algorithm threat assessment
                </Typography>
              </Box>
            </Box>
          </Box>
        )}

        {/* System Architecture Page */}
        {currentPage === 'architecture' && (
          <Box
            sx={{
              width: '100%',
              maxWidth: 1080,
              p: { xs: 3, md: 4 },
              borderRadius: '34px',
              border: '1px solid rgba(97, 145, 255, 0.24)',
              background: 'rgba(8, 18, 42, 0.86)',
              backdropFilter: 'blur(28px)',
              boxShadow: '0 34px 88px rgba(8, 19, 44, 0.4)',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
              <Button
                variant="outlined"
                onClick={handleBackToMain}
                sx={{
                  borderColor: 'rgba(82, 179, 255, 0.5)',
                  color: '#b8d4ff',
                  '&:hover': {
                    borderColor: 'rgba(111, 195, 255, 0.8)',
                    backgroundColor: 'rgba(82, 179, 255, 0.08)',
                  },
                }}
              >
                ← Back
              </Button>
              <Typography variant="h4" sx={{ color: '#eef4ff', fontWeight: 700 }}>
                System Architecture
              </Typography>
            </Box>
            <Box
              sx={{
                width: '100%',
                borderRadius: '24px',
                overflow: 'hidden',
                border: '1px solid rgba(82, 179, 255, 0.2)',
                background: 'rgba(6, 16, 34, 0.75)',
              }}
            >
              <object
                type="image/svg+xml"
                data="/Quantum%20Key%20Generation%20Flow-2026-03-25-115040.svg"
                aria-label="QASS System Architecture SVG Diagram"
                style={{ width: '100%', minHeight: 520, display: 'block' }}
              />
            </Box>
          </Box>
        )}

        {/* Upload & Visualize Page */}
        {currentPage === 'upload' && (
          <Box
            sx={{
              width: '100%',
              maxWidth: 1080,
              p: { xs: 3, md: 4 },
              borderRadius: '34px',
              border: '1px solid rgba(97, 145, 255, 0.24)',
              background: 'rgba(8, 18, 42, 0.86)',
              backdropFilter: 'blur(28px)',
              boxShadow: '0 34px 88px rgba(8, 19, 44, 0.4)',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
              <Button
                variant="outlined"
                onClick={handleBackToMain}
                sx={{
                  borderColor: 'rgba(82, 179, 255, 0.5)',
                  color: '#b8d4ff',
                  '&:hover': {
                    borderColor: 'rgba(111, 195, 255, 0.8)',
                    backgroundColor: 'rgba(82, 179, 255, 0.08)',
                  },
                }}
              >
                ← Back
              </Button>
              <Typography variant="h4" sx={{ color: '#eef4ff', fontWeight: 700 }}>
                Upload & Visualize
              </Typography>
            </Box>
            <FileUploadSection onCSVUpload={handleCSVUpload} onPNGUpload={handlePNGUpload} />
            {csvName && (
              <Typography variant="body1" sx={{ color: '#dbe7ff', mb: 2 }}>
                Uploaded CSV: {csvName}
              </Typography>
            )}
            {pngUrl && (
              <Box sx={{ mt: 3, textAlign: 'center' }}>
                <Typography variant="subtitle1" gutterBottom sx={{ color: '#d7e4ff' }}>
                  Uploaded Image Preview
                </Typography>
                <Box
                  component="img"
                  src={pngUrl}
                  alt="Uploaded diagram"
                  sx={{ width: '100%', maxHeight: 360, borderRadius: 3, border: '1px solid rgba(255,255,255,0.12)' }}
                />
              </Box>
            )}
          </Box>
        )}

        {/* Quantum Layer Verification Page */}
        {currentPage === 'qlayer' && (
          <Box
            sx={{
              width: '100%',
              maxWidth: 1080,
              p: { xs: 3, md: 4 },
              borderRadius: '34px',
              border: '1px solid rgba(97, 145, 255, 0.24)',
              background: 'rgba(8, 18, 42, 0.86)',
              backdropFilter: 'blur(28px)',
              boxShadow: '0 34px 88px rgba(8, 19, 44, 0.4)',
            }}
          >
            <ImageCarousel
              images={qlayerImages}
              title="Quantum Layer Verification"
              onBack={handleBackToMain}
            />
          </Box>
        )}

        {/* Phase 4 Page */}
        {currentPage === 'phase4' && (
          <Box
            sx={{
              width: '100%',
              maxWidth: 1080,
              p: { xs: 3, md: 4 },
              borderRadius: '34px',
              border: '1px solid rgba(97, 145, 255, 0.24)',
              background: 'rgba(8, 18, 42, 0.86)',
              backdropFilter: 'blur(28px)',
              boxShadow: '0 34px 88px rgba(8, 19, 44, 0.4)',
            }}
          >
            <ImageCarousel
              images={phase4Images}
              title="Phase 4"
              onBack={handleBackToMain}
            />
          </Box>
        )}

        {/* PQC Assurance Page */}
        {currentPage === 'pqc' && (
          <Box
            sx={{
              width: '100%',
              maxWidth: 1080,
              p: { xs: 3, md: 4 },
              borderRadius: '34px',
              border: '1px solid rgba(97, 145, 255, 0.24)',
              background: 'rgba(8, 18, 42, 0.86)',
              backdropFilter: 'blur(28px)',
              boxShadow: '0 34px 88px rgba(8, 19, 44, 0.4)',
            }}
          >
            <ImageCarousel
              images={pqcImages}
              title="PQC Assurance"
              onBack={handleBackToMain}
            />
          </Box>
        )}

        {/* Grover's Algorithm Carousel Page */}
        {currentPage === 'grover' && (
          <Box
            sx={{
              width: '100%',
              maxWidth: 1080,
              p: { xs: 3, md: 4 },
              borderRadius: '34px',
              border: '1px solid rgba(97, 145, 255, 0.24)',
              background: 'rgba(8, 18, 42, 0.86)',
              backdropFilter: 'blur(28px)',
              boxShadow: '0 34px 88px rgba(8, 19, 44, 0.4)',
            }}
          >
            <ImageCarousel
              images={groverImages}
              title="Grover's Algorithm"
              onBack={() => setCurrentPage('ablation')}
            />
          </Box>
        )}

        {/* Shor's Algorithm Carousel Page */}
        {currentPage === 'shors' && (
          <Box
            sx={{
              width: '100%',
              maxWidth: 1080,
              p: { xs: 3, md: 4 },
              borderRadius: '34px',
              border: '1px solid rgba(97, 145, 255, 0.24)',
              background: 'rgba(8, 18, 42, 0.86)',
              backdropFilter: 'blur(28px)',
              boxShadow: '0 34px 88px rgba(8, 19, 44, 0.4)',
            }}
          >
            <ImageCarousel
              images={shorsImages}
              title="Shor's Algorithm"
              onBack={() => setCurrentPage('ablation')}
            />
          </Box>
        )}
      </Container>
    </Box>
  );
}

export default App
