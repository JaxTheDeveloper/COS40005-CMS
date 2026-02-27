import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

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
        api.get('/social/social-gold/'),
        api.get('/social/transactions/')
      ]);
      
      setSocialGold(goldResponse.data[0]);
      setTransactions(transactionsResponse.data);
      setError(null);
    } catch (err) {
      setError('Failed to load social gold data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <section className="stack">
        <p className="lead">Loading...</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="stack">
        <div className="alert alert-error">{error}</div>
      </section>
    );
  }

  return (
    <section className="stack">
      <div className="breadcrumb">Home / <strong>Social Gold</strong></div>
      <h1 className="page-h1">Social Gold</h1>

      <div className="stat-grid">
        <div className="stat-card">
          <div className="stat-label">Current Balance</div>
          <div className="stat-value">{socialGold?.current_balance || 0}</div>
          <div className="stat-sub">Lifetime earned: {socialGold?.lifetime_earned || 0}</div>
        </div>
      </div>

      <h3 className="subheading">Transaction History</h3>
      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Type</th>
              <th>Amount</th>
              <th>Reason</th>
              <th>Awarded By</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 ? (
              <tr>
                <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-muted)' }}>
                  No transactions found
                </td>
              </tr>
            ) : (
              transactions.map((transaction) => (
                <tr key={transaction.id}>
                  <td>{new Date(transaction.created_at).toLocaleDateString()}</td>
                  <td>{transaction.transaction_type}</td>
                  <td className={transaction.amount >= 0 ? 'text-positive' : 'text-negative'}>
                    {transaction.amount >= 0 ? '+' : ''}{transaction.amount}
                  </td>
                  <td>{transaction.reason}</td>
                  <td>{transaction.awarded_by?.email || 'System'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}