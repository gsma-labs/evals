import React from 'react';

interface BenchmarkCardProps {
  title: string;
  description: string;
  link?: string;
  paperLink?: string;
  datasetLink?: string;
}

export default function BenchmarkCard({
  title,
  description,
  link,
  paperLink,
  datasetLink,
}: BenchmarkCardProps): JSX.Element {
  return (
    <div style={{
      border: '1px solid #e0e0e0',
      borderRadius: '8px',
      padding: '20px 24px',
      backgroundColor: 'white',
      display: 'flex',
      flexDirection: 'column',
      height: '100%',
      transition: 'box-shadow 0.2s ease',
    }}
    onMouseEnter={(e) => {
      e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.08)';
    }}
    onMouseLeave={(e) => {
      e.currentTarget.style.boxShadow = 'none';
    }}
    >
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'flex-start',
        marginBottom: '12px',
      }}>
        <h3 style={{
          fontSize: '17px',
          fontWeight: '600',
          margin: 0,
          color: '#1a1a1a',
        }}>
          {title}
        </h3>
        {(paperLink || datasetLink) && (
          <div style={{ display: 'flex', gap: '8px' }}>
            {paperLink && (
              <a
                href={paperLink}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  color: '#008080',
                  fontSize: '14px',
                }}
                title="Paper"
              >
                ↗
              </a>
            )}
          </div>
        )}
      </div>
      <p style={{
        fontSize: '14px',
        color: '#555',
        lineHeight: '1.5',
        margin: 0,
        flex: 1,
      }}>
        {description}
      </p>
      {(paperLink || datasetLink) && (
        <div style={{
          marginTop: '16px',
          display: 'flex',
          gap: '12px',
          fontSize: '13px',
        }}>
          {paperLink && (
            <a
              href={paperLink}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#008080', textDecoration: 'none' }}
            >
              Paper
            </a>
          )}
          {datasetLink && (
            <a
              href={datasetLink}
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: '#008080', textDecoration: 'none' }}
            >
              Dataset
            </a>
          )}
        </div>
      )}
    </div>
  );
}
