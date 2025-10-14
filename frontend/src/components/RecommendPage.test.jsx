import React from 'react';
import { render, screen } from '@testing-library/react';
import RecommendPage from './RecommendPage';

describe('RecommendPage', () => {
  it('smoke renders', () => {
    render(<RecommendPage />);
    expect(screen.getByText(/CineSense Recommendations/i)).toBeInTheDocument();
  });
});
