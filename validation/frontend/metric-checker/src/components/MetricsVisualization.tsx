import React, { useState } from 'react';
import './MetricsVisualization.css';
import MetadataBarChart from './MetadataBarChart';
import ComprehensiveChart from './ComprehensiveChart';

interface MetricResult {
  metric_type: string;
  field_name: string | null;
  total_items: number;
  exact_matches?: number;
  accuracy?: number;
  mismatches?: Array<{
    id: string;
    field?: string;
    predicted?: any;
    real?: any;
    mismatched_fields?: Array<{
      field: string;
      predicted: any;
      real: any;
    }>;
  }>;
  perfect_matches?: number;
  average_percentage?: number;
  details?: Array<{
    id: string;
    predicted_list: string[];
    real_list: string[];
    match_percentage: number;
    matching_elements: string[];
    missing_elements: string[];
    extra_elements: string[];
  }>;
}

interface TypeSpecificResult {
  type: string;
  total_documents: number;
  detailed_results: MetricResult[];
  summary: any;
}

interface MetricsVisualizationProps {
  results: MetricResult[];
  typeSpecificResults?: Record<string, TypeSpecificResult>;
  onReset: () => void;
}

const MetricsVisualization: React.FC<MetricsVisualizationProps> = ({ results, typeSpecificResults, onReset }) => {
  const [selectedType, setSelectedType] = useState<string>('General');
  
  // Get available types
  const availableTypes = typeSpecificResults ? Object.keys(typeSpecificResults) : ['General'];
  
  // Get current results based on selected type
  const getCurrentResults = (): MetricResult[] => {
    if (selectedType === 'Comprehensive') {
      return results; // Return general results for comprehensive view
    }
    if (selectedType === 'General' || !typeSpecificResults) {
      return results;
    }
    return typeSpecificResults[selectedType]?.detailed_results || [];
  };
  
  const currentResults = getCurrentResults();
  const currentTypeInfo = typeSpecificResults?.[selectedType];
  const formatPercentage = (value: number): string => {
    return (value * 100).toFixed(1) + '%';
  };

  const getScoreColor = (score: number): string => {
    if (score >= 0.8) return '#27ae60';
    if (score >= 0.6) return '#f39c12';
    if (score >= 0.4) return '#e67e22';
    return '#e74c3c';
  };

  const renderExactEqualityMetric = (result: MetricResult) => {
    const accuracy = result.accuracy || 0;
    const scoreColor = getScoreColor(accuracy);

    return (
      <div key={`${result.metric_type}-${result.field_name}`} className="metric-card exact-equality">
        <div className="metric-header">
          <h3>Exact Equality Comparison</h3>
          <span className="field-name">{result.field_name || 'All Fields'}</span>
        </div>
        
        <div className="metric-score">
          <div className="score-circle" style={{ borderColor: scoreColor }}>
            <span className="score-text" style={{ color: scoreColor }}>
              {formatPercentage(accuracy)}
            </span>
          </div>
        </div>

        <div className="metric-stats">
          <div className="stat-item">
            <span className="stat-label">Total Items:</span>
            <span className="stat-value">{result.total_items}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Exact Matches:</span>
            <span className="stat-value">{result.exact_matches}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Mismatches:</span>
            <span className="stat-value">{result.mismatches?.length || 0}</span>
          </div>
        </div>

        {result.mismatches && result.mismatches.length > 0 && (
          <details className="mismatches-details">
            <summary>View Mismatches ({result.mismatches.length})</summary>
            <div className="mismatches-list">
              {result.mismatches.slice(0, 5).map((mismatch, index) => (
                <div key={index} className="mismatch-item">
                  <strong>ID: {mismatch.id}</strong>
                  {mismatch.field && (
                    <div className="field-comparison">
                      <p><strong>Field:</strong> {mismatch.field}</p>
                      <div className="value-comparison">
                        <div className="predicted-value">
                          <span className="label">Predicted:</span>
                          <span className="value">{JSON.stringify(mismatch.predicted)}</span>
                        </div>
                        <div className="real-value">
                          <span className="label">Real:</span>
                          <span className="value">{JSON.stringify(mismatch.real)}</span>
                        </div>
                      </div>
                    </div>
                  )}
                  {mismatch.mismatched_fields && (
                    <div className="mismatched-fields">
                      <p><strong>Mismatched Fields:</strong></p>
                      {mismatch.mismatched_fields.slice(0, 3).map((field, fidx) => (
                        <div key={fidx} className="field-detail">
                          <span className="field-name">{field.field}:</span>
                          <span className="predicted">Predicted: {JSON.stringify(field.predicted)}</span>
                          <span className="real">Real: {JSON.stringify(field.real)}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {result.mismatches.length > 5 && (
                <p className="more-items">... and {result.mismatches.length - 5} more</p>
              )}
            </div>
          </details>
        )}
      </div>
    );
  };

  const renderListPercentageMetric = (result: MetricResult) => {
    const avgPercentage = result.average_percentage || 0;
    const scoreColor = getScoreColor(avgPercentage);

    return (
      <div key={`${result.metric_type}-${result.field_name}`} className="metric-card list-percentage">
        <div className="metric-header">
          <h3>List Percentage Match</h3>
          <span className="field-name">{result.field_name}</span>
        </div>

        <div className="metric-score">
          <div className="score-circle" style={{ borderColor: scoreColor }}>
            <span className="score-text" style={{ color: scoreColor }}>
              {formatPercentage(avgPercentage)}
            </span>
          </div>
        </div>

        <div className="metric-stats">
          <div className="stat-item">
            <span className="stat-label">Total Items:</span>
            <span className="stat-value">{result.total_items}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Perfect Matches:</span>
            <span className="stat-value">{result.perfect_matches}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Average Match:</span>
            <span className="stat-value">{formatPercentage(avgPercentage)}</span>
          </div>
        </div>

        {result.details && result.details.length > 0 && (
          <details className="details-section">
            <summary>View Detailed Comparisons ({result.details.length})</summary>
            <div className="details-list">
              {result.details.slice(0, 5).map((detail, index) => (
                <div key={index} className="detail-item">
                  <div className="detail-header">
                    <strong>ID: {detail.id}</strong>
                    <span className="match-score" style={{ color: getScoreColor(detail.match_percentage) }}>
                      {formatPercentage(detail.match_percentage)}
                    </span>
                  </div>
                  
                  <div className="list-comparison">
                    <div className="list-section">
                      <span className="list-label">Predicted:</span>
                      <div className="list-items">
                        {detail.predicted_list.map((item, idx) => (
                          <span key={idx} className="list-item predicted">{item}</span>
                        ))}
                      </div>
                    </div>
                    
                    <div className="list-section">
                      <span className="list-label">Real:</span>
                      <div className="list-items">
                        {detail.real_list.map((item, idx) => (
                          <span key={idx} className="list-item real">{item}</span>
                        ))}
                      </div>
                    </div>
                  </div>

                  {detail.matching_elements.length > 0 && (
                    <div className="match-breakdown">
                      <span className="breakdown-label">✓ Matching:</span>
                      <div className="breakdown-items">
                        {detail.matching_elements.map((item, idx) => (
                          <span key={idx} className="breakdown-item matching">{item}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {detail.missing_elements.length > 0 && (
                    <div className="match-breakdown">
                      <span className="breakdown-label">✗ Missing:</span>
                      <div className="breakdown-items">
                        {detail.missing_elements.map((item, idx) => (
                          <span key={idx} className="breakdown-item missing">{item}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {detail.extra_elements.length > 0 && (
                    <div className="match-breakdown">
                      <span className="breakdown-label">+ Extra:</span>
                      <div className="breakdown-items">
                        {detail.extra_elements.map((item, idx) => (
                          <span key={idx} className="breakdown-item extra">{item}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
              {result.details.length > 5 && (
                <p className="more-items">... and {result.details.length - 5} more</p>
              )}
            </div>
          </details>
        )}
      </div>
    );
  };

  const renderTypeSelector = () => {
    if (availableTypes.length <= 1) return null;
    
    return (
      <div className="type-selector">
        <h3>Select Document Type:</h3>
        <div className="type-buttons">
          {availableTypes.map(type => (
            <button
              key={type}
              className={`type-btn ${selectedType === type ? 'active' : ''}`}
              onClick={() => setSelectedType(type)}
            >
              {type}
              {typeSpecificResults?.[type] && (
                <span className="type-count">({typeSpecificResults[type].total_documents})</span>
              )}
            </button>
          ))}
          {typeSpecificResults && Object.keys(typeSpecificResults).length > 0 && (
            <button
              key="comprehensive"
              className={`type-btn comprehensive-btn ${selectedType === 'Comprehensive' ? 'active' : ''}`}
              onClick={() => setSelectedType('Comprehensive')}
            >
              📊 All Types Overview
            </button>
          )}
        </div>
      </div>
    );
  };

  const renderSummaryStats = () => {
    const exactEqualityResults = currentResults.filter(r => r.metric_type === 'exact_equality');
    const listPercentageResults = currentResults.filter(r => r.metric_type === 'list_percentage_match');

    const avgExactAccuracy = exactEqualityResults.length > 0 
      ? exactEqualityResults.reduce((sum, r) => sum + (r.accuracy || 0), 0) / exactEqualityResults.length
      : 0;

    const avgListPercentage = listPercentageResults.length > 0
      ? listPercentageResults.reduce((sum, r) => sum + (r.average_percentage || 0), 0) / listPercentageResults.length
      : 0;

    return (
      <div className="summary-stats">
        <h2>Summary Statistics - {selectedType}</h2>
        {currentTypeInfo && (
          <div className="type-info">
            <span className="total-docs">Total Documents: {currentTypeInfo.total_documents}</span>
          </div>
        )}
        <div className="summary-grid">
          <div className="summary-item">
            <span className="summary-label">Total Metrics:</span>
            <span className="summary-value">{currentResults.length}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Avg. Exact Accuracy:</span>
            <span className="summary-value">{formatPercentage(avgExactAccuracy)}</span>
          </div>
          <div className="summary-item">
            <span className="summary-label">Avg. List Match:</span>
            <span className="summary-value">{formatPercentage(avgListPercentage)}</span>
          </div>
        </div>
      </div>
    );
  };

  if (!currentResults || currentResults.length === 0) {
    return (
      <div className="metrics-container">
        <div className="no-results">
          <h2>No Results</h2>
          <p>No metric results to display.</p>
          <button onClick={onReset} className="reset-btn">Upload New Files</button>
        </div>
      </div>
    );
  }

  return (
    <div className="metrics-container">
      <div className="metrics-header">
        <h1>Metric Comparison Results</h1>
        <button onClick={onReset} className="reset-btn">Upload New Files</button>
      </div>

      {renderTypeSelector()}
      
      {selectedType === 'Comprehensive' && typeSpecificResults && Object.keys(typeSpecificResults).length > 0 ? (
        <ComprehensiveChart 
          generalResults={results}
          typeSpecificResults={typeSpecificResults}
        />
      ) : (
        <>
          {renderSummaryStats()}
          <MetadataBarChart 
            results={currentResults}
            title="Metadata Accuracy Overview"
            type={selectedType}
          />
        </>
      )}

      {selectedType !== 'Comprehensive' && (
        <div className="metrics-grid">
        {currentResults.map(result => {
          if (result.metric_type === 'exact_equality') {
            return renderExactEqualityMetric(result);
          } else if (result.metric_type === 'list_percentage_match') {
            return renderListPercentageMetric(result);
          }
          return null;
        })}
        </div>
      )}
    </div>
  );
};

export default MetricsVisualization;