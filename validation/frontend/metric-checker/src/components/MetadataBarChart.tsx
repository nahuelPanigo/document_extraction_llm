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

interface MetadataBarChartProps {
  results: MetricResult[];
  title?: string;
  type?: string;
}

const MetadataBarChart: React.FC<MetadataBarChartProps> = ({ 
  results, 
  title = "Metadata Accuracy by Field",
  type = "General"
}) => {
  const chartRef = useRef<HTMLDivElement>(null);

  // Process data for chart
  const chartData = React.useMemo(() => {
    const processedData = results.map(result => {
      const percentage = (result.accuracy || result.average_percentage || 0) * 100;
      const fieldName = result.field_name || 'All Fields';
      return {
        label: `${fieldName} (${result.metric_type})`,
        value: percentage,
        color: getBarColor(percentage / 100)
      };
    });

    return {
      labels: processedData.map(item => item.label),
      datasets: [
        {
          label: 'Accuracy %',
          data: processedData.map(item => item.value),
          backgroundColor: processedData.map(item => item.color),
          borderColor: processedData.map(item => item.color.replace('0.8', '1')),
          borderWidth: 1,
        },
      ],
    };
  }, [results]);

  const options = {
    responsive: true,
    plugins: {
      legend: {
        position: 'top' as const,
      },
      title: {
        display: true,
        text: `${title} - ${type}`,
        font: {
          size: 16,
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

  function getBarColor(score: number): string {
    if (score >= 0.8) return 'rgba(39, 174, 96, 0.8)';
    if (score >= 0.6) return 'rgba(243, 156, 18, 0.8)';
    if (score >= 0.4) return 'rgba(230, 126, 34, 0.8)';
    return 'rgba(231, 76, 60, 0.8)';
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
        link.download = `metadata-chart-${type.toLowerCase().replace(/\s+/g, '-')}.png`;
        link.href = canvas.toDataURL();
        link.click();
      } catch (error) {
        console.error('Error downloading chart:', error);
        alert('Failed to download chart. Please try again.');
      }
    }
  };

  if (!results || results.length === 0) {
    return (
      <div className="chart-container">
        <div className="no-data">
          <h3>No Data Available</h3>
          <p>No metrics data to display in chart.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="chart-container">
      <div className="chart-header">
        <h3>{title} - {type}</h3>
        <button onClick={downloadChart} className="download-btn">
          📊 Download Chart
        </button>
      </div>
      <div ref={chartRef} className="chart-wrapper">
        <Bar data={chartData} options={options} />
      </div>
    </div>
  );
};

export default MetadataBarChart;