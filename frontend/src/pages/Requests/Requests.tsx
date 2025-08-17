import React from 'react';
import { Typography, Box } from '@mui/material';

const Requests: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Requests
      </Typography>
      <Typography>LLM request history and monitoring</Typography>
    </Box>
  );
};

export default Requests;
