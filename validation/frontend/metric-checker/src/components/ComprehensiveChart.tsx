import React, { useRef } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';
import html2canvas from 'html2canvas';
import './MetadataBarChart.css';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface MetricResult {
  metric_type: string;
  field_name: string | null;
  accuracy?: number;
  average_percentage?: number;
}

interface TypeSpecificResult {
  type: string;
  total_documents: number;
  detailed_results: MetricResult[];
  summary: any;
}

interface ComprehensiveChartProps {
  generalResults: MetricResult[];
  typeSpecificResults: Record<string, TypeSpecificResult>;
}

const ComprehensiveChart: React.FC<ComprehensiveChartProps> = ({ 
  generalResults, 
  typeSpecificResults 
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

  // Process data for comprehensive chart
  const chartData = React.useMemo(() => {
    const datasets: any[] = [];
    const labels: string[] = [];
    const allFieldsMap = new Map<string, Map<string, number>>();

    // Process general results
    if (generalResults && generalResults.length > 0) {
      generalResults.forEach(result => {
        const percentage = (result.accuracy || result.average_percentage || 0) * 100;
        const fieldName = result.field_name || 'All Fields';
        const metricType = result.metric_type === 'exact_equality' ? 'Exact' : 'List Match';
        const label = `${fieldName} (${metricType})`;
        
        if (!labels.includes(label)) {
          labels.push(label);
          allFieldsMap.set(label, new Map());
        }
        
        allFieldsMap.get(label)?.set('General', percentage);
      });
    }

    // Process type-specific results
    Object.entries(typeSpecificResults).forEach(([typeName, typeData]) => {
      typeData.detailed_results.forEach(result => {
        const percentage = (result.accuracy || result.average_percentage || 0) * 100;
        const fieldName = result.field_name || 'All Fields';
        const metricType = result.metric_type === 'exact_equality' ? 'Exact' : 'List Match';
        const label = `${fieldName} (${metricType})`;
        
        if (!labels.includes(label)) {
          labels.push(label);
          allFieldsMap.set(label, new Map());
        }
        
        allFieldsMap.get(label)?.set(typeName, percentage);
      });
    });

    // Create datasets - avoid duplicate General
    const allTypes = Object.keys(typeSpecificResults).length > 0 
      ? ['General', ...Object.keys(typeSpecificResults)]
      : ['General'];
    
    // Remove duplicates if General appears in typeSpecificResults
    const uniqueTypes = allTypes.filter((type, index, array) => 
      array.indexOf(type) === index
    );
    
    uniqueTypes.forEach((typeName, index) => {
      const data = labels.map(label => {
        return allFieldsMap.get(label)?.get(typeName) || 0;
      });

      datasets.push({
        label: typeName,
        data,
        backgroundColor: getUniqueTypeColor(typeName, index, 0.8),
        borderColor: getUniqueTypeColor(typeName, index, 1),
        borderWidth: 1,
      });
    });

    return { labels, datasets };
  }, [generalResults, typeSpecificResults]);

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: 'Comprehensive Metadata Accuracy Comparison',
        font: {
          size: 18,
          weight: 'bold' as const
        }
      },
      tooltip: {
        callbacks: {
          label: function(context: any) {
            return `${context.dataset.label}: ${context.parsed.y.toFixed(1)}%`;
          }
        }
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: function(value: any) {
            return value + '%';
          }
        },
        title: {
          display: true,
          text: 'Accuracy Percentage'
        }
      },
      x: {
        ticks: {
          maxRotation: 45,
          minRotation: 0
        }
      }
    },
  };

  function getUniqueTypeColor(typeName: string, index: number, opacity: number): string {
    const colors = [
      `rgba(52, 152, 219, ${opacity})`,   // Blue (General)
      `rgba(231, 76, 60, ${opacity})`,    // Red  
      `rgba(46, 204, 113, ${opacity})`,   // Green
      `rgba(155, 89, 182, ${opacity})`,   // Purple
      `rgba(241, 196, 15, ${opacity})`,   // Yellow
      `rgba(230, 126, 34, ${opacity})`,   // Orange
      `rgba(26, 188, 156, ${opacity})`,   // Turquoise
      `rgba(243, 156, 18, ${opacity})`,   // Dark Orange
      `rgba(142, 68, 173, ${opacity})`,   // Dark Purple
      `rgba(39, 174, 96, ${opacity})`,    // Dark Green
      `rgba(192, 57, 43, ${opacity})`,    // Dark Red
      `rgba(41, 128, 185, ${opacity})`,   // Dark Blue
    ];
    
    // Use index to ensure unique colors, wrap around if we have more types than colors
    return colors[index % colors.length];
  }

  const downloadChart = async () => {
    if (chartRef.current) {
      try {
        const canvas = await html2canvas(chartRef.current, {
          backgroundColor: '#ffffff',
          scale: 2,
          useCORS: true,
        });
        
        const link = document.createElement('a');
        link.download = 'comprehensive-metadata-chart.png';
        link.href = canvas.toDataURL();
        link.click();
      } catch (error) {
        console.error('Error downloading chart:', error);
        alert('Failed to download chart. Please try again.');
      }
    }
  };

  if ((!generalResults || generalResults.length === 0) && 
      (!typeSpecificResults || Object.keys(typeSpecificResults).length === 0)) {
    return (
      <div className="chart-container">
        <div className="no-data">
          <h3>No Data Available</h3>
          <p>No comprehensive data to display in chart.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <div className="chart-header">
        <h3>📊 All Types Overview - Metadata Comparison</h3>
        <div className="chart-actions">
          <button onClick={downloadChart} className="download-btn">
            💾 Download Chart
          </button>
        </div>
      </div>
      <div className="chart-description">
        <p>This chart shows accuracy percentages for each metadata field across all document types and general data. Each bar represents a metadata field, with different colors showing performance across different types.</p>
      </div>
      <div ref={chartRef} className="chart-wrapper" style={{ height: '500px' }}>
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
};

export default ComprehensiveChart;