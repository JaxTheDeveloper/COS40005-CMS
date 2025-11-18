import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  Toolbar,
  IconButton,
  Typography,
  Menu,
  Container,
  Avatar,
  Button,
  Tooltip,
  MenuItem,
  Tab,
  Tabs
} from '@mui/material';
import { Menu as MenuIcon } from '@mui/icons-material';
import { authService } from '../services/auth';

// Define available tabs based on user role
const STUDENT_TABS = [
  { value: '/dashboard/compsci', label: 'Dashboard' },
  { value: '/queries', label: 'Queries' },
  { value: '/ask-ai', label: 'Ask AI' },
];

const CONVENOR_TABS = [
  { value: '/dashboard/compsci', label: 'Dashboard' },
  { value: '/manage-units', label: 'Manage Units' },
  { value: '/reports', label: 'Reports' },
];

const STAFF_TABS = [
  { value: '/dashboard/compsci', label: 'Dashboard' },
  { value: '/admin', label: 'Admin' },
];

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [anchorElNav, setAnchorElNav] = useState(null);
  const [anchorElUser, setAnchorElUser] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [currentTab, setCurrentTab] = useState('/dashboard/compsci');
  const [availableTabs, setAvailableTabs] = useState([]);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const user = await authService.getCurrentUser();
        setCurrentUser(user);
        // Set available tabs based on user type
        if (user) {
          switch (user.user_type) {
            case 'student':
              setAvailableTabs(STUDENT_TABS);
              break;
            case 'unit_convenor':
              setAvailableTabs(CONVENOR_TABS);
              break;
            case 'staff':
              setAvailableTabs(STAFF_TABS);
              break;
            default:
              setAvailableTabs(STUDENT_TABS);
          }
        }
      } catch (error) {
        console.error('Authentication check failed:', error);
        navigate('/login');
      }
    };
    checkAuth();
  }, [navigate]);

  useEffect(() => {
    setCurrentTab(location.pathname);
  }, [location]);

  const handleOpenNavMenu = (event) => {
    setAnchorElNav(event.currentTarget);
  };
  
  const handleOpenUserMenu = (event) => {
    setAnchorElUser(event.currentTarget);
  };

  const handleCloseNavMenu = () => {
    setAnchorElNav(null);
  };

  const handleCloseUserMenu = () => {
    setAnchorElUser(null);
  };

  const handleLogout = () => {
    authService.logout();
    setCurrentUser(null);
    navigate('/login');
    handleCloseUserMenu();
  };

  const handleTabChange = (event, newValue) => {
    setCurrentTab(newValue);
    navigate(newValue);
  };

  return (
    <AppBar position="static" color="default" elevation={1}>
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          <Typography
            variant="h6"
            noWrap
            sx={{
              mr: 2,
              display: { xs: 'none', md: 'flex' },
              fontWeight: 700,
              color: 'inherit',
              textDecoration: 'none',
              cursor: 'pointer'
            }}
            onClick={() => navigate('/')}
          >
            Swinburne VN
          </Typography>

          {currentUser && (
            <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' } }}>
              <Tabs
                value={currentTab}
                onChange={handleTabChange}
                textColor="primary"
                indicatorColor="primary"
              >
                {availableTabs.map((tab) => (
                  <Tab
                    key={tab.value}
                    label={tab.label}
                    value={tab.value}
                  />
                ))}
              </Tabs>
            </Box>
          )}

          {currentUser && (
            <Box sx={{ flexGrow: 1, display: { xs: 'flex', md: 'none' } }}>
              <IconButton
                size="large"
                aria-controls="menu-appbar"
                aria-haspopup="true"
                onClick={handleOpenNavMenu}
                color="inherit"
              >
                <MenuIcon />
              </IconButton>
              <Menu
                id="menu-appbar"
                anchorEl={anchorElNav}
                anchorOrigin={{
                  vertical: 'bottom',
                  horizontal: 'left',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'left',
                }}
                open={Boolean(anchorElNav)}
                onClose={handleCloseNavMenu}
                sx={{
                  display: { xs: 'block', md: 'none' },
                }}
              >
                <MenuItem onClick={() => { handleCloseNavMenu(); navigate('/dashboard/compsci'); }}>
                  <Typography textAlign="center">Dashboard</Typography>
                </MenuItem>
                <MenuItem onClick={() => { handleCloseNavMenu(); navigate('/queries'); }}>
                  <Typography textAlign="center">Queries</Typography>
                </MenuItem>
                <MenuItem onClick={() => { handleCloseNavMenu(); navigate('/events'); }}>
                  <Typography textAlign="center">Events</Typography>
                </MenuItem>
                <MenuItem onClick={() => { handleCloseNavMenu(); navigate('/ask-ai'); }}>
                  <Typography textAlign="center">Ask AI</Typography>
                </MenuItem>
              </Menu>
            </Box>
          )}

          {!currentUser && (
            <Box sx={{ flexGrow: 1 }} />
          )}

          {currentUser ? (
            <Box sx={{ flexGrow: 0 }}>
              <Tooltip title="Open settings">
                <IconButton onClick={handleOpenUserMenu} sx={{ p: 0 }}>
                  <Avatar alt={currentUser.username} src={currentUser.profile_image} />
                </IconButton>
              </Tooltip>
              <Menu
                sx={{ mt: '45px' }}
                id="menu-appbar"
                anchorEl={anchorElUser}
                anchorOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                keepMounted
                transformOrigin={{
                  vertical: 'top',
                  horizontal: 'right',
                }}
                open={Boolean(anchorElUser)}
                onClose={handleCloseUserMenu}
              >
                <MenuItem onClick={() => { handleCloseUserMenu(); navigate('/profile'); }}>
                  <Typography textAlign="center">Profile</Typography>
                </MenuItem>
                <MenuItem onClick={() => { handleCloseUserMenu(); navigate('/enrollments'); }}>
                  <Typography textAlign="center">My Enrollments</Typography>
                </MenuItem>
                <MenuItem onClick={() => { handleCloseUserMenu(); navigate('/social-gold'); }}>
                  <Typography textAlign="center">Social Gold</Typography>
                </MenuItem>
                <MenuItem onClick={handleLogout}>
                  <Typography textAlign="center">Logout</Typography>
                </MenuItem>
              </Menu>
            </Box>
          ) : (
            <Button
              onClick={() => navigate('/login')}
              sx={{ ml: 2 }}
              variant="contained"
              color="primary"
            >
              Login
            </Button>
          )}
        </Toolbar>
      </Container>
    </AppBar>
  );
}
