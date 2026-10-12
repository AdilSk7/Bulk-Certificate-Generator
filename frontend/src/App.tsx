import React, { useState, useEffect, useRef } from 'react';
import { UploadCloud, Download, FileText, AlertCircle, RefreshCw } from 'lucide-react';
import Papa from 'papaparse';
import './App.css';

// In development, use an empty base so Vite's proxy forwards /api/* to FastAPI.
// In production, set VITE_API_URL to your deployed backend base URL.
const API_URL = import.meta.env.VITE_API_URL ?? '';

interface Recipient {
  name: string;
  email: string;
}

interface Certificate {
  id: number;
  certificate_id: string;
  recipient_name: string;
  status: string;
  error_message?: string;
}

interface JobResponse {
  job_id: number;
  status: string;
  progress: number;
  total_count: number;
  success_count: number;
  failed_count: number;
  certificates: Certificate[];
}

function App() {
  const [eventName, setEventName] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [issuerName, setIssuerName] = useState('');
  const [certificateTitle, setCertificateTitle] = useState('CERTIFICATE OF PARTICIPATION');
  const [introductionText, setIntroductionText] = useState('This certificate is proudly presented to');
  const [descriptionText, setDescriptionText] = useState('for successfully participating in');
  const [presentedByLabel, setPresentedByLabel] = useState('Presented by');

  const [file, setFile] = useState<File | null>(null);
  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);

  const [jobId, setJobId] = useState<number | null>(null);
  const [jobData, setJobData] = useState<JobResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Poll Job Status
  useEffect(() => {
    if (!isPolling || !jobId) return;

    const fetchJobStatus = async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/jobs/${jobId}`);
        if (!res.ok) throw new Error('Failed to fetch job status');
        const data: JobResponse = await res.json();
        setJobData(data);
        if (data.status === 'COMPLETED' || data.status === 'FAILED') {
          setIsPolling(false);
        }
      } catch {
        setError('Lost connection to backend. Please check if FastAPI is running on port 8000.');
        setIsPolling(false);
      }
    };

    fetchJobStatus();
    const interval = setInterval(fetchJobStatus, 1500);
    return () => clearInterval(interval);
  }, [isPolling, jobId]);

  const parseCSV = (f: File) => {
    setError(null);
    Papa.parse(f, {
      header: true,
      skipEmptyLines: true,
      complete: (results) => {
        const rows = results.data as Record<string, string>[];
        if (rows.length === 0) {
          setError('CSV file is empty. Please provide at least one recipient.');
          return;
        }

        const firstRow = rows[0];
        const hasName = 'name' in firstRow || 'Name' in firstRow;
        const hasEmail = 'email' in firstRow || 'Email' in firstRow;

        if (!hasName || !hasEmail) {
          setError('Invalid CSV. The file must contain "name" and "email" columns.');
          setRecipients([]);
          return;
        }

        const parsed: Recipient[] = rows
          .map((row) => ({
            name: (row.name || row.Name || '').trim(),
            email: (row.email || row.Email || '').trim(),
          }))
          .filter((r) => r.name && r.email);

        if (parsed.length === 0) {
          setError('No valid recipients found. Ensure all rows have a name and email.');
          return;
        }

        setRecipients(parsed);
      },
      error: () => setError('Failed to parse CSV file. Please check the file format.'),
    });
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(true);
  };

  const handleDragLeave = () => setIsDragActive(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragActive(false);
    const dropped = e.dataTransfer.files[0];
    if (dropped) { setFile(dropped); parseCSV(dropped); }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) { setFile(selected); parseCSV(selected); }
  };

  const handleGenerate = async () => {
    if (!eventName.trim() || !eventDate.trim() || !issuerName.trim()) {
      setError('Please fill in Event Name, Event Date, and Issuer Name.');
      return;
    }
    if (recipients.length === 0) {
      setError('Please upload a valid CSV file with recipients first.');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      const res = await fetch(`${API_URL}/api/v1/jobs`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          event_name: eventName,
          event_date: eventDate,
          issuer_name: issuerName,
          certificate_title: certificateTitle,
          introduction_text: introductionText,
          description_text: descriptionText,
          presented_by_label: presentedByLabel,
          recipients,
        }),
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        let errorMsg = 'Backend returned an error. Please try again.';
        if (typeof errorData?.detail === 'string') {
          errorMsg = errorData.detail;
        } else if (Array.isArray(errorData?.detail)) {
          errorMsg = errorData.detail.map((d: any) => `${d.loc?.slice(1).join('.') || 'Field'}: ${d.msg}`).join(', ');
        }
        throw new Error(errorMsg);
      }

      const data = await res.json();
      setJobId(data.job_id);
      setJobData(data);
      setIsPolling(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Could not connect to backend.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDownloadSingle = (certId: string) => {
    const a = document.createElement('a');
    a.href = `${API_URL}/api/v1/certificates/download/${certId}`;
    a.download = `${certId}.pdf`;
    a.click();
  };

  const handleDownloadAll = () => {
    if (!jobId) return;
    const a = document.createElement('a');
    a.href = `${API_URL}/api/v1/jobs/${jobId}/download`;
    a.click();
  };

  const handleReset = () => {
    setEventName('');
    setEventDate('');
    setIssuerName('');
    setCertificateTitle('CERTIFICATE OF PARTICIPATION');
    setIntroductionText('This certificate is proudly presented to');
    setDescriptionText('for successfully participating in');
    setPresentedByLabel('Presented by');
    setFile(null);
    setRecipients([]);
    setError(null);
    setJobId(null);
    setJobData(null);
    setIsPolling(false);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  const isCompleted = jobData?.status === 'COMPLETED' || jobData?.status === 'FAILED';

  return (
    <div className="page">
      {/* Header */}
      <header className="header">
        <div className="header-icon">
          <FileText size={36} color="#fff" />
        </div>
        <h1>Bulk Certificate Generator</h1>
        <p>Generate professional certificates in seconds</p>
      </header>

      <main className="main">
        {/* Error Alert */}
        {error && (
          <div className="alert">
            <AlertCircle size={18} />
            <span>{error}</span>
          </div>
        )}

        {/* Upload Card — hidden once job starts */}
        {!jobId && (
          <div className="card">
            <h2 className="card-title">Event Details</h2>
            <div className="form-grid">
              <div className="form-group">
                <label htmlFor="eventName">Event Name</label>
                <input
                  id="eventName"
                  type="text"
                  placeholder="e.g. Python Workshop"
                  value={eventName}
                  onChange={(e) => setEventName(e.target.value)}
                />
              </div>
              <div className="form-group">
                <label htmlFor="eventDate">Event Date</label>
                <input
                  id="eventDate"
                  type="date"
                  value={eventDate}
                  onChange={(e) => setEventDate(e.target.value)}
                />
              </div>
              <div className="form-group full-width">
                <label htmlFor="issuerName">Issuer / Organisation</label>
                <input
                  id="issuerName"
                  type="text"
                  placeholder="e.g. ABC Organisation"
                  value={issuerName}
                  onChange={(e) => setIssuerName(e.target.value)}
                />
              </div>
            </div>

            {/* Certificate Content */}
            <h2 className="card-title" style={{ marginTop: '1.5rem' }}>Certificate Content</h2>
            <div className="form-grid">
              <div className="form-group full-width">
                <label htmlFor="certificateTitle">Certificate Title</label>
                <input
                  id="certificateTitle"
                  type="text"
                  placeholder="e.g. CERTIFICATE OF PARTICIPATION"
                  value={certificateTitle}
                  onChange={(e) => setCertificateTitle(e.target.value)}
                />
              </div>
              <div className="form-group full-width">
                <label htmlFor="introductionText">Introduction Text</label>
                <input
                  id="introductionText"
                  type="text"
                  placeholder="e.g. This certificate is proudly presented to"
                  value={introductionText}
                  onChange={(e) => setIntroductionText(e.target.value)}
                />
              </div>
              <div className="form-group full-width">
                <label htmlFor="descriptionText">Description Text</label>
                <input
                  id="descriptionText"
                  type="text"
                  placeholder="e.g. for successfully participating in"
                  value={descriptionText}
                  onChange={(e) => setDescriptionText(e.target.value)}
                />
              </div>
              <div className="form-group full-width">
                <label htmlFor="presentedByLabel">Presented By Label</label>
                <input
                  id="presentedByLabel"
                  type="text"
                  placeholder="e.g. Presented by"
                  value={presentedByLabel}
                  onChange={(e) => setPresentedByLabel(e.target.value)}
                />
              </div>
            </div>

            <h2 className="card-title" style={{ marginTop: '1.5rem' }}>Recipients CSV</h2>
            <div
              className={`dropzone${isDragActive ? ' drag-active' : ''}`}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              role="button"
              tabIndex={0}
            >
              <UploadCloud size={44} className="dropzone-icon" />
              {file ? (
                <>
                  <p className="dropzone-filename">{file.name}</p>
                  <p className="dropzone-hint">{recipients.length} recipient{recipients.length !== 1 ? 's' : ''} loaded</p>
                </>
              ) : (
                <>
                  <p className="dropzone-label">Drag &amp; drop a CSV file here</p>
                  <p className="dropzone-hint">or click to browse &nbsp;•&nbsp; Requires <code>name</code> and <code>email</code> columns</p>
                </>
              )}
              <input
                type="file"
                accept=".csv"
                style={{ display: 'none' }}
                ref={fileInputRef}
                onChange={handleFileSelect}
              />
            </div>

            <button
              className="btn btn-primary"
              onClick={handleGenerate}
              disabled={isSubmitting || !file || recipients.length === 0}
            >
              {isSubmitting ? 'Submitting…' : 'Generate Certificates'}
            </button>
          </div>
        )}

        {/* Progress Card */}
        {jobData && (
          <div className="card">
            <div className="progress-header">
              <span className="job-label">Job #{jobData.job_id}</span>
              <span className={`status-badge ${jobData.status.toLowerCase()}`}>{jobData.status}</span>
            </div>

            <div className="progress-track">
              <div className="progress-fill" style={{ width: `${jobData.progress}%` }} />
            </div>

            <div className="progress-meta">
              <span>{jobData.progress}% complete</span>
              <span>
                <span className="success-num">{jobData.success_count}</span> generated &nbsp;
                {jobData.failed_count > 0 && (
                  <span className="failed-num">{jobData.failed_count} failed</span>
                )}
                &nbsp;/ {jobData.total_count} total
              </span>
            </div>

            {isCompleted && jobData.success_count > 0 && (
              <button className="btn btn-primary" style={{ marginTop: '1.25rem' }} onClick={handleDownloadAll}>
                <Download size={17} /> Download All as ZIP
              </button>
            )}

            {isCompleted && (
              <button className="btn btn-ghost" style={{ marginTop: '0.75rem' }} onClick={handleReset}>
                <RefreshCw size={15} /> Generate Another Batch
              </button>
            )}
          </div>
        )}

        {/* Certificate List */}
        {jobData && jobData.certificates.length > 0 && (
          <div className="card card-list">
            <h2 className="card-title">Certificates</h2>
            <ul className="cert-list">
              {jobData.certificates.map((cert) => (
                <li key={cert.id} className="cert-item">
                  <div className="cert-info">
                    <span className="cert-name">{cert.recipient_name}</span>
                    <span className="cert-id">{cert.certificate_id}</span>
                  </div>
                  <div className="cert-right">
                    <span className={`cert-status ${cert.status === 'GENERATED' ? 'generated' : cert.status === 'FAILED' ? 'failed' : 'pending'}`}>
                      {cert.status}
                    </span>
                    {cert.status === 'GENERATED' && cert.certificate_id && (
                      <button
                        className="btn btn-outline"
                        onClick={() => handleDownloadSingle(cert.certificate_id)}
                      >
                        <Download size={14} /> PDF
                      </button>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
