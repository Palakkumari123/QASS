import { Box, Button, Typography, IconButton } from '@mui/material';
import { useState } from 'react';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';

interface ImageCarouselProps {
  images: string[];
  title: string;
  onBack: () => void;
}

export function ImageCarousel({ images, title, onBack }: ImageCarouselProps) {
  const [currentIndex, setCurrentIndex] = useState(0);

  const goToPrevious = () => {
    setCurrentIndex((prev) => (prev === 0 ? images.length - 1 : prev - 1));
  };

  const goToNext = () => {
    setCurrentIndex((prev) => (prev === images.length - 1 ? 0 : prev + 1));
  };

  return (
    <Box
      sx={{
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        gap: 3,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button
          variant="outlined"
          onClick={onBack}
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
        <Typography variant="h5" sx={{ color: '#e7f2ff', fontWeight: 600 }}>
          {title} Analysis
        </Typography>
      </Box>

      <Box
        sx={{
          position: 'relative',
          width: '100%',
          aspectRatio: '16/9',
          borderRadius: '24px',
          overflow: 'hidden',
          border: '1px solid rgba(82, 179, 255, 0.3)',
          backgroundColor: 'rgba(10, 25, 53, 0.6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <img
          src={images[currentIndex]}
          alt={`${title} chart ${currentIndex + 1}`}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            padding: '20px',
          }}
        />

        {/* Previous Button */}
        <IconButton
          onClick={goToPrevious}
          sx={{
            position: 'absolute',
            left: 16,
            top: '50%',
            transform: 'translateY(-50%)',
            backgroundColor: 'rgba(10, 25, 53, 0.7)',
            color: '#b8d4ff',
            border: '1px solid rgba(82, 179, 255, 0.4)',
            backdropFilter: 'blur(10px)',
            '&:hover': {
              backgroundColor: 'rgba(82, 179, 255, 0.2)',
              borderColor: 'rgba(111, 195, 255, 0.8)',
            },
          }}
        >
          <ChevronLeftIcon />
        </IconButton>

        {/* Next Button */}
        <IconButton
          onClick={goToNext}
          sx={{
            position: 'absolute',
            right: 16,
            top: '50%',
            transform: 'translateY(-50%)',
            backgroundColor: 'rgba(10, 25, 53, 0.7)',
            color: '#b8d4ff',
            border: '1px solid rgba(82, 179, 255, 0.4)',
            backdropFilter: 'blur(10px)',
            '&:hover': {
              backgroundColor: 'rgba(82, 179, 255, 0.2)',
              borderColor: 'rgba(111, 195, 255, 0.8)',
            },
          }}
        >
          <ChevronRightIcon />
        </IconButton>

        {/* Pagination Indicator */}
        <Box
          sx={{
            position: 'absolute',
            bottom: 16,
            left: '50%',
            transform: 'translateX(-50%)',
            backgroundColor: 'rgba(10, 25, 53, 0.8)',
            backdropFilter: 'blur(10px)',
            px: 3,
            py: 1,
            borderRadius: '20px',
            border: '1px solid rgba(82, 179, 255, 0.3)',
          }}
        >
          <Typography
            variant="body2"
            sx={{ color: '#b8d4ff', fontWeight: 600 }}
          >
            {currentIndex + 1} / {images.length}
          </Typography>
        </Box>
      </Box>

      {/* Thumbnail Navigation */}
      <Box
        sx={{
          display: 'flex',
          gap: 2,
          overflowX: 'auto',
          pb: 2,
          '&::-webkit-scrollbar': {
            height: '6px',
          },
          '&::-webkit-scrollbar-track': {
            backgroundColor: 'rgba(82, 179, 255, 0.1)',
            borderRadius: '3px',
          },
          '&::-webkit-scrollbar-thumb': {
            backgroundColor: 'rgba(82, 179, 255, 0.4)',
            borderRadius: '3px',
            '&:hover': {
              backgroundColor: 'rgba(111, 195, 255, 0.6)',
            },
          },
        }}
      >
        {images.map((img, idx) => (
          <Box
            key={idx}
            onClick={() => setCurrentIndex(idx)}
            sx={{
              flexShrink: 0,
              width: 100,
              height: 80,
              borderRadius: '12px',
              overflow: 'hidden',
              cursor: 'pointer',
              border:
                idx === currentIndex
                  ? '2px solid rgba(82, 179, 255, 0.8)'
                  : '1px solid rgba(82, 179, 255, 0.2)',
              opacity: idx === currentIndex ? 1 : 0.6,
              transition: 'all 0.3s ease',
              '&:hover': {
                opacity: 0.9,
                borderColor: 'rgba(111, 195, 255, 0.6)',
              },
            }}
          >
            <img
              src={img}
              alt={`Thumbnail ${idx + 1}`}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'cover',
              }}
            />
          </Box>
        ))}
      </Box>
    </Box>
  );
}
