import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper
} from '@mui/material';
import axios from 'axios';

export default function SocialGold() {
  const [socialGold, setSocialGold] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSocialGoldData();
  }, []);

  const loadSocialGoldData = async () => {
    try {
      const [goldResponse, transactionsResponse] = await Promise.all([
        axios.get('/api/social/social-gold/'),
        axios.get('/api/social/transactions/')
      ]);
      
      setSocialGold(goldResponse.data[0]); // Assuming user has one social gold record
      setTransactions(transactionsResponse.data);
      setError(null);
    } catch (err) {
      setError('Failed to load social gold data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Box>Loading...</Box>;
  if (error) return <Box color="error.main">{error}</Box>;

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Social Gold</Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Current Balance</Typography>
              <Typography variant="h3" color="primary">
                {socialGold?.current_balance || 0}
              </Typography>
              <Typography color="textSecondary">
                Lifetime earned: {socialGold?.lifetime_earned || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Box mt={4}>
        <Typography variant="h5" gutterBottom>Transaction History</Typography>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Date</TableCell>
                <TableCell>Type</TableCell>
                <TableCell>Amount</TableCell>
                <TableCell>Reason</TableCell>
                <TableCell>Awarded By</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {transactions.map((transaction) => (
                <TableRow key={transaction.id}>
                  <TableCell>
                    {new Date(transaction.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>{transaction.transaction_type}</TableCell>
                  <TableCell
                    sx={{
                      color: transaction.amount >= 0 ? 'success.main' : 'error.main'
                    }}
                  >
                    {transaction.amount >= 0 ? '+' : ''}{transaction.amount}
                  </TableCell>
                  <TableCell>{transaction.reason}</TableCell>
                  <TableCell>
                    {transaction.awarded_by?.email || 'System'}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Box>
    </Box>
  );
}