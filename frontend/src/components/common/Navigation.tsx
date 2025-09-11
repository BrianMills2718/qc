// Navigation component for the application

import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Analytics as AnalyticsIcon,
  Code as CodeIcon,
  FormatQuote as QuoteIcon,
  Assessment as ReportIcon,
  MoreVert as MoreIcon,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useHealth, useQueryHealth } from '../../hooks/useQueries';

const Navigation: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMoreAnchorEl, setMobileMoreAnchorEl] = useState<null | HTMLElement>(null);
  
  // Health checks for status indicator
  const { data: health } = useHealth();
  const { data: queryHealth } = useQueryHealth();
  
  const isHealthy = health && queryHealth?.status === 'healthy';

  const navigationItems = [
    { label: 'Dashboard', path: '/dashboard', icon: <DashboardIcon /> },
    { label: 'Workspace', path: '/workspace', icon: <AnalyticsIcon /> },
    { label: 'Codes', path: '/codes', icon: <CodeIcon /> },
    { label: 'Quotes', path: '/quotes', icon: <QuoteIcon /> },
    { label: 'Reports', path: '/reports', icon: <ReportIcon /> },
  ];

  const isActiveRoute = (path: string) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  const handleMobileMenuClose = () => {
    setMobileMoreAnchorEl(null);
  };

  const handleMobileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMobileMoreAnchorEl(event.currentTarget);
  };

  const handleNavigate = (path: string) => {
    navigate(path);
    handleMobileMenuClose();
  };

  const renderMobileMenu = (
    <Menu
      anchorEl={mobileMoreAnchorEl}
      anchorOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      keepMounted
      transformOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      open={Boolean(mobileMoreAnchorEl)}
      onClose={handleMobileMenuClose}
    >
      {navigationItems.map((item) => (
        <MenuItem 
          key={item.path}
          onClick={() => handleNavigate(item.path)}
          selected={isActiveRoute(item.path)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {item.icon}
            {item.label}
          </Box>
        </MenuItem>
      ))}
    </Menu>
  );

  return (
    <>
      <AppBar position="static" elevation={1}>
        <Toolbar>
          {/* Logo/Title */}
          <Typography
            variant="h6"
            component="div"
            sx={{ cursor: 'pointer' }}
            onClick={() => navigate('/dashboard')}
          >
            Qualitative Coding Analysis
          </Typography>

          {/* Desktop Navigation */}
          <Box sx={{ 
            flexGrow: 1, 
            display: { xs: 'none', md: 'flex' }, 
            justifyContent: 'center',
            gap: 1 
          }}>
            {navigationItems.map((item) => (
              <Button
                key={item.path}
                color="inherit"
                startIcon={item.icon}
                onClick={() => navigate(item.path)}
                sx={{
                  borderRadius: 2,
                  backgroundColor: isActiveRoute(item.path) ? 'rgba(255, 255, 255, 0.1)' : 'transparent',
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.2)',
                  },
                }}
              >
                {item.label}
              </Button>
            ))}
          </Box>

          {/* Health Status Indicator */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: isHealthy ? '#4caf50' : '#f44336',
              }}
            />
            <Typography variant="caption" sx={{ display: { xs: 'none', sm: 'block' } }}>
              {isHealthy ? 'Connected' : 'Offline'}
            </Typography>
          </Box>

          {/* Mobile menu button */}
          <Box sx={{ display: { xs: 'flex', md: 'none' } }}>
            <IconButton
              size="large"
              color="inherit"
              onClick={handleMobileMenuOpen}
            >
              <MoreIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>
      
      {renderMobileMenu}
    </>
  );
};

export default Navigation;