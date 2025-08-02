import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import './FileUpload.css';

interface FileUploadProps {
  onFilesSelected: (predictedFile: File | null, realFile: File | null) => void;
  onCompare: () => void;
}

interface UploadedFiles {
  predicted: File | null;
  real: File | null;
}

const FileUpload: React.FC<FileUploadProps> = ({ onFilesSelected, onCompare }) => {
  const [files, setFiles] = useState<UploadedFiles>({ predicted: null, real: null });
  const [activeDropzone, setActiveDropzone] = useState<'predicted' | 'real' | null>(null);

  const onDropPredicted = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const newFiles = { ...files, predicted: acceptedFiles[0] };
      setFiles(newFiles);
      onFilesSelected(newFiles.predicted, newFiles.real);
    }
  }, [files, onFilesSelected]);

  const onDropReal = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      const newFiles = { ...files, real: acceptedFiles[0] };
      setFiles(newFiles);
      onFilesSelected(newFiles.predicted, newFiles.real);
    }
  }, [files, onFilesSelected]);

  const {
    getRootProps: getPredictedRootProps,
    getInputProps: getPredictedInputProps,
    isDragActive: isPredictedDragActive
  } = useDropzone({
    onDrop: onDropPredicted,
    accept: {
      'application/json': ['.json']
    },
    multiple: false
  });

  const {
    getRootProps: getRealRootProps,
    getInputProps: getRealInputProps,
    isDragActive: isRealDragActive
  } = useDropzone({
    onDrop: onDropReal,
    accept: {
      'application/json': ['.json']
    },
    multiple: false
  });

  const removeFile = (type: 'predicted' | 'real') => {
    const newFiles = { ...files, [type]: null };
    setFiles(newFiles);
    onFilesSelected(newFiles.predicted, newFiles.real);
  };

  const canCompare = files.predicted && files.real;

  return (
    <div className="file-upload-container">
      <h1 className="title">JSON Metric Checker</h1>
      <p className="subtitle">Upload your predicted and real JSON files to compare metadata metrics</p>
      
      <div className="upload-section">
        <div className="dropzone-container">
          <div
            {...getPredictedRootProps()}
            className={`dropzone predicted ${isPredictedDragActive ? 'active' : ''} ${files.predicted ? 'has-file' : ''}`}
          >
            <input {...getPredictedInputProps()} />
            <div className="dropzone-content">
              <div className="icon">📄</div>
              {files.predicted ? (
                <div className="file-info">
                  <p className="file-name">{files.predicted.name}</p>
                  <p className="file-size">{(files.predicted.size / 1024).toFixed(2)} KB</p>
                  <button 
                    onClick={(e) => { e.stopPropagation(); removeFile('predicted'); }}
                    className="remove-file-btn"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div className="placeholder">
                  <p><strong>Predicted Output JSON</strong></p>
                  <p>Drag & drop your predicted JSON file here</p>
                  <p>or click to browse</p>
                </div>
              )}
            </div>
          </div>

          <div className="vs-separator">
            <span>VS</span>
          </div>

          <div
            {...getRealRootProps()}
            className={`dropzone real ${isRealDragActive ? 'active' : ''} ${files.real ? 'has-file' : ''}`}
          >
            <input {...getRealInputProps()} />
            <div className="dropzone-content">
              <div className="icon">📋</div>
              {files.real ? (
                <div className="file-info">
                  <p className="file-name">{files.real.name}</p>
                  <p className="file-size">{(files.real.size / 1024).toFixed(2)} KB</p>
                  <button 
                    onClick={(e) => { e.stopPropagation(); removeFile('real'); }}
                    className="remove-file-btn"
                  >
                    Remove
                  </button>
                </div>
              ) : (
                <div className="placeholder">
                  <p><strong>Ground Truth JSON</strong></p>
                  <p>Drag & drop your ground truth JSON file here</p>
                  <p>or click to browse</p>
                </div>
              )}
            </div>
          </div>
        </div>

        <div className="action-section">
          <button 
            onClick={onCompare}
            disabled={!canCompare}
            className={`compare-btn ${canCompare ? 'enabled' : 'disabled'}`}
          >
            {canCompare ? 'Compare Files' : 'Upload Both Files to Compare'}
          </button>
          
          {canCompare && (
            <div className="file-summary">
              <p>✓ Ready to compare:</p>
              <ul>
                <li>Predicted: {files.predicted?.name}</li>
                <li>Ground Truth: {files.real?.name}</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileUpload;